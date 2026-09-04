"""DIAGNOSTIC ONLY - read-only, writes nothing into results/.

Tests why the FPR<=10% operating point does not transfer to the test set,
even after the leakage-free calibration split of stage 3b.

Hypothesis: Training/ and Testing/ in this dataset are separate collections,
not a random split of one pool, so the detector's CLEAN score distribution
shifts between them. If true, no amount of calibration on validation (which
is carved out of Training/) can pin the test FPR.

Compares clean detector scores on validation (1120 imgs, from Training/)
against test (1600 imgs, from Testing/) and reports the FPR each would
imply at the thresholds already selected.
"""
import json
from importlib import import_module

import numpy as np
import tensorflow as tf

import common

d3 = import_module("03_detector_v2")
d3b = import_module("03b_detector_v2_calibrated")


def clean_scores(detector, extract, dataset):
    out = []
    for images, _ in dataset:
        out.append(detector(extract(images), training=False).numpy().reshape(-1))
    return np.concatenate(out)


def describe(name, s):
    q = np.percentile(s, [50, 75, 90, 95, 99])
    print(f"  {name:<12} n={s.size:<5} mean={s.mean():.4f} sd={s.std():.4f} "
          f"p50={q[0]:.4f} p75={q[1]:.4f} p90={q[2]:.4f} p95={q[3]:.4f} p99={q[4]:.4f}")


def main():
    common.set_determinism()
    _, val_ds, test_ds, _ = common.make_datasets()
    classifier = common.load_classifier_verified()
    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)

    rec = json.loads(d3b.THRESHOLD_PATH.read_text(encoding="utf-8"))
    thr, margin = rec["threshold"], rec["margin_threshold"]

    val_s = clean_scores(detector, extract, val_ds)
    test_s = clean_scores(detector, extract, test_ds)

    print("\nCLEAN detector-score distributions (v2b detector)")
    describe("validation", val_s)
    describe("test", test_s)

    print("\nImplied clean FPR at the SAME thresholds")
    for label, t in (("primary (cal 8.93%)", thr), ("margin (cal 7.14%)", margin)):
        fv, ft = float((val_s >= t).mean()), float((test_s >= t).mean())
        print(f"  {label:<22} thr={t:.4f}  validation={fv:.4f}  test={ft:.4f}  "
              f"shift={ft - fv:+.4f}")

    print("\nWhat threshold would test ACTUALLY need for 10% / 7.5% FPR?")
    for target in (0.10, 0.075):
        need = float(np.quantile(test_s, 1 - target))
        print(f"  test FPR {target:.3%} needs thr={need:.4f} "
              f"(vs {thr:.4f} chosen on calibration)")

    ks = None
    try:
        from scipy.stats import ks_2samp
        ks = ks_2samp(val_s, test_s)
        print(f"\nKS test val vs test: D={ks.statistic:.4f} p={ks.pvalue:.3e}")
        print("  -> distributions differ" if ks.pvalue < 0.01
              else "  -> no significant difference")
    except Exception as e:
        print("scipy unavailable:", e)


if __name__ == "__main__":
    main()
