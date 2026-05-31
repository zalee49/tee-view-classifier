#!/usr/bin/env python
"""Stage de-identified AVI clips for the TEE view classifier.

This bridges two projects that deliberately cannot share a runtime:

  * The DICOM de-identification pipeline (env: ``dicom-deid``, Python 3.11)
    writes MJPG AVIs nested per pseudonymized patient::

        <deid_output>/avi/<patient_pseudonym>/<clip_stem>.avi

  * This classifier's ``EchoDataset`` (``src/data.py``, env ``tee-view-class``,
    Python 3.8) calls ``os.listdir(data_path)`` and tries to decode EVERY entry
    as a video. Its input must therefore be a FLAT directory containing only
    ``.avi`` files -- a subdirectory or a stray ``.dcm`` would be handed to
    ``cv2.VideoCapture`` and fail.

So this script flattens the per-patient tree into one staging directory and:

  * renames each clip ``<patient>__<clip>.avi`` so the classifier's output
    ``filename`` column stays traceable back to patient + original clip, and
    so two patients with an identically named clip don't collide;
  * SKIPS clips too short for the classifier's fixed sampling. ``read_video``
    pulls ``n_frames=16`` at ``sample_period=2`` and raises if the clip has
    fewer than ``16 * 2 = 32`` frames -- and because that raise happens inside
    ``__getitem__``, a single short clip aborts the entire inference run. We
    decode up to ``MIN_FRAMES`` frames to confirm they are actually readable --
    stricter than ``CAP_PROP_FRAME_COUNT``, which can over-report for MJPG -- so
    a clip we stage is guaranteed to satisfy ``read_video``.

Exit codes (consumed by run_chain.ps1):
    0  at least one clip staged
    3  no avi/ directory under the de-id output (the run produced no videos)
    4  an avi/ tree exists but no clip was long enough to classify
"""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

import cv2

# Must mirror src/data.py read_video(): n_frames=16, sample_period=2.
N_FRAMES = 16
SAMPLE_PERIOD = 2
MIN_FRAMES = N_FRAMES * SAMPLE_PERIOD  # 32


def decodable_frames(path: Path, limit: int) -> int:
    """How many frames actually decode, reading up to ``limit`` sequential frames.

    read_video() reads exactly ``n_frames * sample_period`` (== MIN_FRAMES)
    sequential frames from the start of the clip, so confirming the first
    ``limit`` frames decode *guarantees* the clip will not fail mid-read. This is
    stricter than ``CAP_PROP_FRAME_COUNT``, which can over-report for MJPG AVIs
    (a clip whose metadata claims 32 frames may only decode 25). Reading is
    capped at ``limit`` so large clips aren't fully decoded just to gate them.
    """
    cap = cv2.VideoCapture(str(path))
    try:
        decoded = 0
        while decoded < limit:
            ok, frame = cap.read()
            if not ok or frame is None:
                break
            decoded += 1
        return decoded
    finally:
        cap.release()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--deid-output", required=True, type=Path,
                    help="dicom-deid output directory (expects an avi/ subtree).")
    ap.add_argument("--staging", required=True, type=Path,
                    help="Flat directory to populate with classifier-ready AVIs.")
    ap.add_argument("--min-frames", type=int, default=MIN_FRAMES,
                    help=f"Minimum decodable frames to keep a clip (default {MIN_FRAMES}).")
    args = ap.parse_args()

    avi_root = args.deid_output / "avi"
    if not avi_root.is_dir():
        print(f"[stage] no avi/ directory under {args.deid_output} -- nothing to classify.",
              file=sys.stderr)
        print("[stage] (the de-id run produced no videos, e.g. no banners were redacted.)",
              file=sys.stderr)
        return 3

    args.staging.mkdir(parents=True, exist_ok=True)
    # Clear prior staging contents so reruns never mix old and new clips.
    for old in args.staging.glob("*.avi"):
        old.unlink()

    staged = 0
    skipped_short = 0
    for avi in sorted(avi_root.rglob("*.avi")):
        patient = avi.parent.name
        n = decodable_frames(avi, args.min_frames)
        if n < args.min_frames:
            print(f"[stage] SKIP {patient}/{avi.name}: only {n} decodable frame(s) < {args.min_frames}")
            skipped_short += 1
            continue
        dest = args.staging / f"{patient}__{avi.name}"
        shutil.copy2(avi, dest)
        staged += 1

    print(f"[stage] staged {staged} clip(s) -> {args.staging}")
    if skipped_short:
        print(f"[stage] skipped {skipped_short} clip(s) with fewer than {args.min_frames} decodable frames.")
    if staged == 0:
        print("[stage] no clips with enough decodable frames to classify; aborting before inference.",
              file=sys.stderr)
        return 4
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
