"""Compare classifier predictions against human ground-truth labels.

Reads two CSVs that share a `filename` column and the same 9 `*_preds`
class columns:
  - predictions CSV: softmax probabilities per class
  - ground-truth CSV: one-hot (0/1) labels per class, plus a human `category`

Reports overall accuracy, top-2 accuracy, a per-class breakdown, a
confusion matrix, and per-class / micro-averaged AUC (the metric the
source paper, Steffner et al. 2023, reports: micro-AUC 0.919 internal,
0.872 external). Truth and prediction are both taken as the argmax over
the shared class columns, so no class-index convention has to be assumed.
"""

import argparse
import os

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

CLASS_COLS = [
    "me_2_chamber_view_preds",
    "me_4_chamber_view_preds",
    "me_av_sax_view_preds",
    "me_bicaval_view_preds",
    "me_left_atrial_appendage_view_preds",
    "me_long_axis_view_preds",
    "tg_lv_sax_view_preds",
    "aortic_view_preds",
    "other_preds",
]
SHORT = [
    "ME 2-Chamber",
    "ME 4-Chamber",
    "ME AV SAX",
    "ME Bicaval",
    "ME LAA",
    "ME Long Axis",
    "TG LV SAX",
    "Aortic",
    "Other",
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--folder", default=r"Z:\DICOM Research\prunedavi_flat")
    ap.add_argument("--preds", default="predictions.csv")
    ap.add_argument("--truth", default="clip_classifications.csv")
    args = ap.parse_args()

    preds = pd.read_csv(os.path.join(args.folder, args.preds))
    truth = pd.read_csv(os.path.join(args.folder, args.truth))

    df = truth.merge(
        preds, on="filename", how="inner", suffixes=("_true", "_pred")
    )
    n_truth, n_preds, n_match = len(truth), len(preds), len(df)
    print(f"Ground-truth clips : {n_truth}")
    print(f"Predicted clips    : {n_preds}")
    print(f"Matched on filename: {n_match}")
    if n_match == 0:
        return

    true_cols = [c + "_true" for c in CLASS_COLS]
    pred_cols = [c + "_pred" for c in CLASS_COLS]

    y_true = df[true_cols].to_numpy().argmax(axis=1)
    prob = df[pred_cols].to_numpy()
    y_pred = prob.argmax(axis=1)

    # top-2: is the true class among the 2 highest-probability classes?
    top2 = np.argsort(prob, axis=1)[:, -2:]
    in_top2 = np.array([t in row for t, row in zip(y_true, top2)])

    correct = y_true == y_pred
    print(f"\nTop-1 accuracy: {correct.mean():.3f}  ({correct.sum()}/{n_match})")
    print(f"Top-2 accuracy: {in_top2.mean():.3f}  ({in_top2.sum()}/{n_match})")

    print("\nPer-class (true label):")
    print(f"  {'class':<14} {'n':>4} {'recall':>7} {'avg P(true)':>12}")
    for i, name in enumerate(SHORT):
        mask = y_true == i
        n = int(mask.sum())
        if n == 0:
            continue
        recall = correct[mask].mean()
        avg_p = prob[mask, i].mean()
        print(f"  {name:<14} {n:>4} {recall:>7.3f} {avg_p:>12.3f}")

    print("\nConfusion matrix (rows = true, cols = predicted):")
    cm = np.zeros((9, 9), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[t, p] += 1
    hdr = "      " + " ".join(f"{i:>4}" for i in range(9))
    print(hdr)
    for i in range(9):
        if cm[i].sum() == 0:
            continue
        row = " ".join(f"{cm[i, j]:>4}" for j in range(9))
        print(f"  {i}: {row}   {SHORT[i]}")
    print("\n  col index -> class:")
    for i, name in enumerate(SHORT):
        print(f"    {i} = {name}")

    # One-vs-rest AUC, the paper's primary metric. Each class column is a
    # binary problem (this view vs. all others) scored against its softmax
    # probability; row-normalisation is irrelevant since columns are scored
    # independently.
    y_onehot = df[true_cols].to_numpy()
    print("\nAUC (one-vs-rest, paper's metric):")
    print(f"  {'class':<14} {'n_pos':>5} {'AUC':>6}")
    aucs = []
    for i, name in enumerate(SHORT):
        pos = int(y_onehot[:, i].sum())
        if pos == 0 or pos == n_match:
            print(f"  {name:<14} {pos:>5} {'  n/a':>6}  (no contrast)")
            continue
        auc = roc_auc_score(y_onehot[:, i], prob[:, i])
        aucs.append(auc)
        print(f"  {name:<14} {pos:>5} {auc:>6.3f}")

    micro = roc_auc_score(y_onehot.ravel(), prob.ravel())
    macro = float(np.mean(aucs))
    print(f"\n  Micro-averaged AUC: {micro:.3f}   (paper: 0.919 internal / 0.872 external)")
    print(f"  Macro-averaged AUC: {macro:.3f}   (paper per-class range: 0.706-0.971)")


if __name__ == "__main__":
    main()
