<#
.SYNOPSIS
  Chain DICOM de-identification -> AVI staging -> TEE view classification.

.DESCRIPTION
  Runs the full two-project pipeline across two ISOLATED conda envs:

    [1/3] dicom-deid     (env: dicom-deid,     Python 3.11) de-identifies the
          input DICOMs and exports MJPG AVIs to <Output>/avi/<patient>/.
    [2/3] stage_avis.py  (env: tee-view-class)             flattens + frame-
          filters those AVIs into <Output>/avi_staged/.
    [3/3] src.inference  (env: tee-view-class, Python 3.8)  classifies the
          staged clips into a predictions CSV.

  The two envs are isolated on purpose -- incompatible Python pins (3.11 vs 3.8)
  and conflicting OpenCV builds (opencv-python vs opencv-python-headless). They
  communicate ONLY through AVI files on disk; this script never mixes them in
  one interpreter.

  `conda run --no-capture-output` is used for every step: letting conda capture
  child output crashes on Windows (cp1252 cannot encode the Unicode that
  dicom-deid's Rich UI and tqdm emit). --no-capture-output streams it straight
  to the console instead.

.PARAMETER InputDir
  Directory of input DICOM files (walked recursively by dicom-deid).

.PARAMETER OutputDir
  Where de-identified DICOMs, the audit log, avi/, avi_staged/, and the
  predictions CSV are written. Created if missing.

.PARAMETER Config
  dicom-deid YAML config. Defaults to the DICOM project's configs/default.yaml.
  Must have pixel.avi_export.enabled: true or no AVIs are produced.

.PARAMETER Weights
  Classifier checkpoint. Defaults to <repo>/weights/weights.ckpt.

.PARAMETER Predictions
  Output CSV path. Defaults to <OutputDir>/predictions.csv.

.NOTES
  Requires $env:DICOM_DEID_SITE_SECRET to be set; the de-id step refuses to run
  without it. conda run inherits the environment, so the secret is passed
  through to the dicom-deid subprocess automatically.

.EXAMPLE
  $env:DICOM_DEID_SITE_SECRET = "<64-char hex>"
  ./integration/run_chain.ps1 -InputDir D:\incoming\study -OutputDir D:\deid\study
#>
[CmdletBinding()]
param(
    [Parameter(Mandatory)] [string] $InputDir,
    [Parameter(Mandatory)] [string] $OutputDir,
    [string] $Config,
    [string] $Weights,
    [string] $Predictions,
    [string] $DeidEnv       = "dicom-deid",
    [string] $ClassifierEnv = "tee-view-class"
)

# Stop on unexpected cmdlet failures; native exit codes are checked explicitly.
$ErrorActionPreference = "Stop"
$env:PYTHONIOENCODING = "utf-8"

function Fail([string] $Message, [int] $Code) {
    Write-Host "ERROR: $Message" -ForegroundColor Red
    exit $Code
}

# --- Resolve project locations relative to this script ----------------------
$ClassifierRoot = Split-Path $PSScriptRoot -Parent                       # View Classifier repo root
$ProjectsRoot   = Split-Path $ClassifierRoot -Parent                     # ...\VSCODE_Projects
$DeidRoot       = Join-Path $ProjectsRoot "DICOM DEIDENTIFICATION"

if (-not $Config)      { $Config      = Join-Path $DeidRoot "configs\default.yaml" }
if (-not $Weights)     { $Weights     = Join-Path $ClassifierRoot "weights\weights.ckpt" }
if (-not $Predictions) { $Predictions = Join-Path $OutputDir "predictions.csv" }
$Staging  = Join-Path $OutputDir "avi_staged"
$StageHlp = Join-Path $PSScriptRoot "stage_avis.py"

# --- Preflight --------------------------------------------------------------
if (-not $env:DICOM_DEID_SITE_SECRET) {
    Fail "DICOM_DEID_SITE_SECRET is not set; the de-identification step cannot run." 2
}
foreach ($p in @($InputDir, $Config, $Weights, $StageHlp)) {
    if (-not (Test-Path -LiteralPath $p)) { Fail "Path not found: $p" 2 }
}

# --- [1/3] De-identify ------------------------------------------------------
Write-Host "==> [1/3] De-identifying DICOMs (env: $DeidEnv)..." -ForegroundColor Cyan
conda run --no-capture-output -n $DeidEnv dicom-deid --input $InputDir --output $OutputDir --config $Config
$deidExit = $LASTEXITCODE
if ($deidExit -eq 2) { Fail "dicom-deid could not run (exit 2)." 2 }
if ($deidExit -eq 1) {
    Write-Host "WARN: dicom-deid reported per-file failures (exit 1); continuing with clips that succeeded." -ForegroundColor Yellow
}

# --- [2/3] Stage AVIs -------------------------------------------------------
Write-Host "==> [2/3] Staging AVIs for the classifier (env: $ClassifierEnv)..." -ForegroundColor Cyan
conda run --no-capture-output -n $ClassifierEnv python $StageHlp --deid-output $OutputDir --staging $Staging
$stageExit = $LASTEXITCODE
# stage_avis exit codes: 0 = clips staged; 3 = de-id produced no AVIs at all;
# 4 = AVIs exist but none had enough decodable frames. 3 and 4 are normal
# "nothing to classify" outcomes, not pipeline faults -- report them plainly but
# still stop with a non-zero code so callers can detect that no CSV was written.
switch ($stageExit) {
    0 { }
    3 { Write-Host "No clips to classify: the de-identification run produced no AVIs (no clips had a banner redacted, or pixel processing is disabled in the config). Stopping; nothing was misclassified." -ForegroundColor Yellow; exit 3 }
    4 { Write-Host "No clips to classify: AVIs were produced but every clip was shorter than the classifier's 32-frame minimum. Stopping." -ForegroundColor Yellow; exit 4 }
    default { Fail "Staging failed unexpectedly (stage_avis exit $stageExit)." $stageExit }
}

# --- [3/3] Classify ---------------------------------------------------------
Write-Host "==> [3/3] Classifying views (env: $ClassifierEnv)..." -ForegroundColor Cyan
# `python -m src.inference` resolves the `src` package from CWD, so run from the repo root.
Push-Location $ClassifierRoot
try {
    conda run --no-capture-output -n $ClassifierEnv python -m src.inference `
        --data_path $Staging --weights_path $Weights --save_predictions $Predictions
    $inferExit = $LASTEXITCODE
}
finally {
    Pop-Location
}
if ($inferExit -ne 0) { Fail "Inference failed (exit $inferExit)." $inferExit }

Write-Host ""
Write-Host "Done. Predictions written to: $Predictions" -ForegroundColor Green
