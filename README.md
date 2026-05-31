
# TEE View Classification

This repository contains inference code for the paper ["Deep learning for transesophageal echocardiography view classification" (Steffner et al., 2023)](https://www.nature.com/articles/s41598-023-50735-8)

To get started, clone this repository and navigate into it:
```
git clone https://github.com/echonet/tee-view-classifier.git
cd tee-view-classifier
```

Then, create a `conda` environment and install the required packages into it:
```
conda create --name tee-view-class python=3.8
conda activate tee-view-class
python -m pip install -r requirements.txt
```


Now that your environement is set up, download the model weights from the Releases tab on this repository. For this example, make a folder inside the repo called `weights` and place them inside it. Then, from the main repo folder, you should be able to run the inference script like this:

```
python -m src.inference \
--data_path "/path/to/folder/of/AVI/video/files" \
--weights_path "weights/weights.ckpt" 
```

---

## Fork additions (`zalee49/tee-view-classifier`)

This fork keeps the upstream inference code above and adds two things on top: small
robustness patches to the inference path, and an integration layer that chains this
classifier onto a DICOM de-identification pipeline. See [CLAUDE.md](CLAUDE.md) for the
full design notes.

> **Weights:** this fork has no Releases of its own — download `weights.ckpt` from the
> **upstream** repo's [Releases tab](https://github.com/echonet/tee-view-classifier/releases)
> into `weights/` (git-ignored).

### Local patches to upstream `src/`

These keep inference working on common hardware and noisy real-world AVIs (each is tagged
`Fork patch` in source; listed in [CLAUDE.md](CLAUDE.md) so they survive an upstream merge):

- **`inference.py`** — load the checkpoint with `map_location=DEVICE`. The released
  `weights.ckpt` was saved from `cuda:1`, so upstream crashes on single-GPU / CPU-only hosts
  without this.
- **`inference.py`** — write predictions with `index=False` (drops the stray index column).
- **`data.py` `crop_resize`** — guard `padding > 0` so near-square frames don't slice to
  width 0 and crash `cv2.resize`.
- **`data.py` `read_video`** — check the `cap.read()` flag and raise a clear error on an
  undecodable frame instead of passing `None` into `crop_resize`.

### De-identification → classification pipeline (`integration/`)

For chaining with the sibling **DICOM de-identification** project. That step writes AVIs
nested per pseudonymized patient (`<output>/avi/<patient>/<clip>.avi`), but this classifier
needs one **flat** folder of only AVIs. The glue bridges that gap (and runs across the two
projects' separate, incompatible conda envs):

- **[integration/stage_avis.py](integration/stage_avis.py)** — flattens the de-id `avi/`
  tree into one folder, renaming each clip `<patient>__<clip>.avi` (traceable, collision-free),
  and drops clips that can't supply the 32 decodable frames the model samples.
- **[integration/run_chain.ps1](integration/run_chain.ps1)** — orchestrates the full flow on
  Windows: **de-identify → stage → classify**.

Run the whole chain (the de-id step needs `DICOM_DEID_SITE_SECRET` set):

```powershell
./integration/run_chain.ps1 -InputDir <dicom_dir> -OutputDir <out_dir>
# -> <out_dir>/avi_staged/ (flat AVIs)  and  <out_dir>/predictions.csv
```

Or run the three steps by hand (works on macOS / Linux too, where `run_chain.ps1`
doesn't). **Each step runs in a different conda env** — de-id in `dicom-deid`
(Python 3.11), staging and inference in `tee-view-class` (Python 3.8); the two envs
must not be merged and share data only as AVIs on disk:

```bash
# 1. De-identify (in the sibling DICOM de-id repo; env: dicom-deid).
#    Needs DICOM_DEID_SITE_SECRET set. Writes <out_dir>/avi/<patient>/<clip>.avi.
dicom-deid --input <raw_dicom_dir> --output <out_dir> --config configs/default.yaml

# 2. Stage: flatten the nested avi/ tree into one folder of only AVIs (env: tee-view-class).
#    --deid-output is the dir CONTAINING avi/, not avi/ itself.
python integration/stage_avis.py --deid-output <out_dir> --staging <out_dir>/avi_staged

# 3. Classify the flat folder (env: tee-view-class). Run from the repo root.
python -m src.inference \
  --data_path <out_dir>/avi_staged \
  --weights_path weights/weights.ckpt \
  --save_predictions <out_dir>/predictions.csv
```

The predictions CSV has one row per clip (`filename` = `<patient>__<clip>.avi`) and one
probability column per view in `CLASS_LIST`; the predicted view is the column-wise argmax.
