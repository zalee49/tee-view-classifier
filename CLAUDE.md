# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this project is

Inference-only code for the paper ["Deep learning for transesophageal echocardiography view classification" (Steffner et al., 2023)](https://www.nature.com/articles/s41598-023-50735-8). Given a folder of AVI video clips, it predicts which of 9 TEE views each clip shows and writes per-class probabilities to a CSV. There is **no training, evaluation, or data-prep code** in this repo — only the forward-inference path.

This is a fork (`zalee49/tee-view-classifier`) of `echonet/tee-view-classifier`. `upstream` remote points at the original.

## Setup and commands

Python 3.8 via conda (the model weights were saved under this environment):

```
conda create --name tee-view-class python=3.8
conda activate tee-view-class
python -m pip install -r requirements.txt
```

Model weights are **not** in the repo (`weights/`, `*.ckpt`, `*.csv` are gitignored). Download `weights.ckpt` from the **upstream** repo's [Releases tab](https://github.com/echonet/tee-view-classifier/releases) (this fork has none of its own) and place it in a `weights/` folder.

Run inference (must be invoked as a module from the repo root — `src/inference.py` uses the relative import `from .data`):

```
python -m src.inference \
  --data_path "/path/to/folder/of/AVI/files" \
  --weights_path "weights/weights.ckpt"
```

Other flags: `--save_predictions` (default `predictions.csv`), `--batch_size` (default 8), `--num_workers` (default 1). CUDA is auto-selected when available, else CPU.

There is no test suite, linter config, or build step.

## Architecture

Two files, one data pipeline feeding one model.

- **[src/inference.py](src/inference.py)** — CLI entry point and the only orchestration. Builds `torchvision.models.video.r2plus1d_18(num_classes=9)`, loads the checkpoint with a plain `load_state_dict` (the print of its return value is the load-result report), runs `softmax` over each batch, accumulates predictions across batches, then explodes the prediction matrix into one CSV column per class.
- **[src/data.py](src/data.py)** — `EchoDataset` lists every file in `--data_path` and decodes each with OpenCV via `read_video` → `crop_resize`. No filtering, so the input folder must contain only readable video files.

### Invariants that are easy to break

- **`CLASS_LIST` order is the model's output contract.** Column index *i* of the model output corresponds to `CLASS_LIST[i]`; the CSV column names are derived by slugifying those strings (`" " → "_"`, `"-" → "_"`, lowercased, `_preds` suffix). Reordering or editing this list silently mislabels predictions and must stay in sync with how the checkpoint was trained.
- **Fixed clip sampling: 16 frames at `sample_period=2`** → every input video must be **at least 32 frames long**, or `read_video` raises. Frames are center-cropped to the model's aspect ratio and resized to **112×112**.
- **Tensor layout the model expects:** `read_video` returns `(n_frames, H, W, 3)` uint8; the dataset normalizes by `/255` and `movedim`s to channels-first `(3, 16, 112, 112)` float32. Changing resolution, frame count, or channel order here must match `r2plus1d_18`'s expectations.
- `predict()` runs entirely under `torch.inference_mode()` and `model.eval()` — keep new model calls inside that context.

## Local fork patch (diverges from upstream `echonet/tee-view-classifier`)

Each item below is marked `Fork patch` in the source. Re-check them when merging `upstream/main`.

- **`inference.py` — `torch.load(weights_path, map_location=DEVICE)`.** Upstream omits `map_location`; the released `weights.ckpt` was saved from `cuda:1` on a multi-GPU machine, so upstream crashes on single-GPU or CPU-only hosts (`Attempting to deserialize object on CUDA device 1`).
- **`inference.py` — `df.to_csv(..., index=False)`.** Upstream writes a stray unnamed RangeIndex column into the predictions CSV.
- **`data.py` `crop_resize` — guard `padding > 0` before slicing.** When a frame's aspect ratio is within rounding distance of the 1:1 target, `padding` rounds to 0 and `img[:, 0:-0]` slices to width 0, crashing the following `cv2.resize`. (Low risk for 4:3 TEE frames; a cheap guard against near-square inputs.)
- **`data.py` `read_video` — check the `cap.read()` success flag.** `CAP_PROP_FRAME_COUNT` can over-report for MJPG, so a clip can pass the length check yet fail to decode mid-stream; upstream passes the resulting `None` into `crop_resize` and dies with a cryptic `NoneType` error. The patch raises a clear `IOError` naming the file and frame.

## Integration with the DICOM de-identification pipeline

This repo is the downstream consumer of the sibling **DICOM DEIDENTIFICATION** project (`../DICOM DEIDENTIFICATION`). The two run in **separate conda envs that must not be merged** — `dicom-deid` (Python 3.11, `opencv-python`) vs `tee-view-class` (Python 3.8, `opencv-python-headless==4.5.5.64`); they share data only as AVI files on disk.

[integration/](integration/) holds the glue (isolated in one folder to stay separable from upstream):

- **[integration/run_chain.ps1](integration/run_chain.ps1)** — orchestrates the full flow across both envs via `conda run --no-capture-output -n <env>` (capture is required-off: conda re-encoding child output crashes on Windows cp1252 when dicom-deid's Rich UI / tqdm emit Unicode). Steps: de-identify → stage → classify. Needs `$env:DICOM_DEID_SITE_SECRET`.
- **[integration/stage_avis.py](integration/stage_avis.py)** — the necessary adapter between the two contracts. dicom-deid writes AVIs **nested** as `<output>/avi/<patient>/<clip>.avi`; `EchoDataset` needs a **flat dir of only AVIs**. This flattens to `<patient>__<clip>.avi` (keeps the classifier's `filename` column traceable) and **drops clips that can't supply 32 decodable frames** — it actually decodes up to `MIN_FRAMES` frames (the exact `n_frames * sample_period` sequence `read_video` reads), rather than trusting `CAP_PROP_FRAME_COUNT`, which can over-report for MJPG. Otherwise a short or truncated clip would raise inside `__getitem__` and abort the whole run.

When changing `N_FRAMES`/`SAMPLE_PERIOD` in `src/data.py`, update `MIN_FRAMES` in `stage_avis.py` to match.
