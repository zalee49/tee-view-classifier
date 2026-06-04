# AGENTS.md

Agent guidance for the `zalee49/tee-view-classifier` repository.

## What this project is

Inference-only code for ["Deep learning for transesophageal echocardiography view classification" (Steffner et al., 2023)](https://www.nature.com/articles/s41598-023-50735-8). Given a flat directory of AVI video clips, it predicts which of 9 TEE views each clip shows and writes per-class softmax probabilities to a CSV. There is **no training, evaluation, or data-prep code** — only the forward-inference path.

Fork of `echonet/tee-view-classifier`. The `upstream` remote points at the original.

## Repository layout

```
src/
  inference.py      # CLI entry point, model instantiation, prediction loop
  data.py           # EchoDataset, read_video, crop_resize
integration/
  run_chain.ps1     # End-to-end PowerShell orchestrator (deid → stage → classify)
  stage_avis.py     # AVI flattener / frame-filter adapter between the two projects
weights/            # gitignored; place weights.ckpt here
requirements.txt
```

## Environment setup

Python 3.8 via conda (the model weights require this exact environment):

```
conda create --name tee-view-class python=3.8
conda activate tee-view-class
python -m pip install -r requirements.txt
```

Model weights are **not** in the repo. Download `weights.ckpt` from the upstream repo's [Releases tab](https://github.com/echonet/tee-view-classifier/releases) and place it at `weights/weights.ckpt`.

There is no test suite, linter config, or build step.

## Running inference

Must be invoked as a module from the repo root (`src/inference.py` uses the relative import `from .data`):

```
python -m src.inference \
  --data_path "/path/to/flat/dir/of/AVI/files" \
  --weights_path "weights/weights.ckpt"
```

Flags: `--save_predictions` (default `predictions.csv`), `--batch_size` (default 8), `--num_workers` (default 1). CUDA is auto-selected when available, else CPU.

**Input requirement:** the `--data_path` folder must contain **only** readable AVI files (no subdirectories, no other file types — `EchoDataset` passes every `os.listdir` entry to `cv2.VideoCapture`).

## Architecture

### `src/inference.py`

- Builds `torchvision.models.video.r2plus1d_18(num_classes=9)`.
- Loads the checkpoint via `torch.load(weights_path, map_location=DEVICE)` then `load_state_dict`.
- Runs `torch.softmax` over each batch inside `torch.inference_mode()` / `model.eval()`.
- Expands the prediction matrix into one CSV column per class using `CLASS_LIST`.

### `src/data.py`

- `EchoDataset` — lists all files in `data_path` and decodes each with `read_video`.
- `read_video` — decodes 16 frames at `sample_period=2` (reads 32 sequential frames) via OpenCV, applies `crop_resize` to 112×112.
- `crop_resize` — center-crops to 1:1 aspect ratio then resizes.

## Hard invariants — do not break these

**`CLASS_LIST` order is the model's output contract.**
Column index *i* of the model output corresponds to `CLASS_LIST[i]`. CSV column names are derived by slugifying those strings (`" " → "_"`, `"-" → "_"`, lowercased, `_preds` suffix). Reordering or editing `CLASS_LIST` silently mislabels every prediction and must stay in sync with the training-time class order.

**Fixed clip sampling: 16 frames at `sample_period=2`.**
Every input video must be at least 32 frames long or `read_video` raises. Update `MIN_FRAMES` in `integration/stage_avis.py` whenever `N_FRAMES` or `SAMPLE_PERIOD` in `src/data.py` changes.

**Tensor layout.**
`read_video` returns `(n_frames, H, W, 3)` uint8. The dataset normalizes by `/255` and `movedim`s to channels-first `(3, 16, 112, 112)` float32. Changing resolution, frame count, or channel order must match `r2plus1d_18`'s expectations.

**Inference context.**
`predict()` runs entirely under `torch.inference_mode()` and `model.eval()`. Keep any new model calls inside that context.

## Fork patches (diverges from `echonet/tee-view-classifier`)

Each divergence is marked `Fork patch` in source. Re-check when merging `upstream/main`:

| File | Patch | Reason |
|------|-------|--------|
| `inference.py` | `torch.load(..., map_location=DEVICE)` | Checkpoint was saved from `cuda:1`; crashes without remapping on single-GPU or CPU hosts |
| `inference.py` | `df.to_csv(..., index=False)` | Upstream writes a stray unnamed RangeIndex column |
| `data.py` `crop_resize` | Guard `padding > 0` before slicing | `padding=0` causes `img[:, 0:-0]` → zero-width slice → `cv2.resize` crash |
| `data.py` `read_video` | Check `cap.read()` success flag | `CAP_PROP_FRAME_COUNT` over-reports for MJPG; upstream passes `None` to `crop_resize` |

## Integration with the DICOM de-identification pipeline

This classifier is the downstream consumer of the sibling **DICOM DEIDENTIFICATION** project (`../DICOM DEIDENTIFICATION`). The two projects run in **separate conda environments that must never be merged**:

| | DICOM DEIDENTIFICATION | View Classifier |
|---|---|---|
| Conda env | `dicom-deid` | `tee-view-class` |
| Python | 3.11 | 3.8 |
| OpenCV | `opencv-python` | `opencv-python-headless==4.5.5.64` |

They share data only as AVI files on disk.

### `integration/stage_avis.py`

Bridges the two output contracts:
- dicom-deid writes AVIs nested as `<output>/avi/<patient>/<clip>.avi`
- `EchoDataset` needs a **flat directory of only AVIs**

The script flattens to `<patient>__<clip>.avi` (preserves traceability in the predictions CSV) and **skips clips with fewer than `MIN_FRAMES` (32) actually-decodable frames** — it decodes up to that limit rather than trusting `CAP_PROP_FRAME_COUNT`. A skipped clip logs a warning; a clip that passes is guaranteed not to raise inside `__getitem__`.

Exit codes consumed by `run_chain.ps1`: `0` = clips staged, `3` = no `avi/` directory produced, `4` = clips exist but all too short.

### `integration/run_chain.ps1`

Orchestrates the full pipeline: de-identify → stage → classify. Each step runs via `conda run --no-capture-output -n <env>` (capture must be off: conda re-encoding Unicode from dicom-deid's Rich/tqdm output crashes on Windows cp1252).

Requires `$env:DICOM_DEID_SITE_SECRET` to be set.

```powershell
$env:DICOM_DEID_SITE_SECRET = "<64-char hex>"
./integration/run_chain.ps1 -InputDir D:\incoming\study -OutputDir D:\deid\study
```

Optional parameters: `-Config`, `-Weights`, `-Predictions`, `-DeidEnv`, `-ClassifierEnv`.

## What agents should avoid

- **Do not add training, evaluation, or data-prep code.** This is a pure inference repo.
- **Do not merge `tee-view-class` and `dicom-deid` conda environments.** The OpenCV and Python version pins conflict intentionally.
- **Do not reorder `CLASS_LIST`.** This silently corrupts all predictions.
- **Do not filter `EchoDataset` input.** All filtering (short clips, non-AVI files) happens in `stage_avis.py` before inference runs. `EchoDataset` receives a pre-validated flat directory.
- **Do not run `python src/inference.py` directly.** Always invoke as `python -m src.inference` from the repo root to resolve the relative import.
