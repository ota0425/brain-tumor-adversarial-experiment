"""Stage 10: persist the clean-score distribution-shift diagnostic.

Compares clean detector scores on validation (1120 images from Training/)
against test (1600 images from Testing/). It reports and saves distribution
quantiles, FPRs at the v2b thresholds, and thresholds required by each split.
"""
import json
from importlib import import_module

import numpy as np
import pandas as pd
import tensorflow as tf

import common

d3 = import_module("03_detector_v2")
d3b = import_module("03b_detector_v2_calibrated")
RESULTS_PATH = common.RESULTS_DIR / "clean_score_distribution_shift.csv"


def clean_scores(detector, extract, dataset):
    out = []
    for images, _ in dataset:
        out.append(detector(extract(images), training=False).numpy().reshape(-1))
    return np.concatenate(out)


def result_row(name, scores, threshold, margin_threshold):
    q = np.percentile(scores, [50, 75, 90, 95, 99])
    return {
        "split": name,
        "n_clean_images": int(scores.size),
        "mean": float(scores.mean()),
        "std": float(scores.std()),
        "p50": float(q[0]),
        "p75": float(q[1]),
        "p90": float(q[2]),
        "p95": float(q[3]),
        "p99": float(q[4]),
        "detector_threshold": float(threshold),
        "clean_fpr_at_detector_threshold": float(
            np.mean(scores >= threshold)),
        "margin_threshold": float(margin_threshold),
        "clean_fpr_at_margin_threshold": float(
            np.mean(scores >= margin_threshold)),
        "threshold_required_for_10pct_fpr": float(
            np.quantile(scores, 0.90, method="higher")),
        "threshold_required_for_7_5pct_fpr": float(
            np.quantile(scores, 0.925, method="higher")),
    }


def main():
    common.set_determinism()
    _, val_ds, test_ds, _ = common.make_datasets()
    classifier = common.load_classifier_verified(
        test_ds.prefetch(tf.data.AUTOTUNE))

    manifest = common.load_manifest()
    assert "detector_v2b_sha256" in manifest, "run 03b first"
    actual = common.sha256_of(d3b.DETECTOR_PATH)
    assert actual == manifest["detector_v2b_sha256"], (
        "detector v2b file changed since training - mixed-era artifacts refused"
    )
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)

    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)

    record = json.loads(d3b.THRESHOLD_PATH.read_text(encoding="utf-8"))
    threshold = record["threshold"]
    margin_threshold = record["margin_threshold"]

    val_scores = clean_scores(detector, extract, val_ds)
    test_scores = clean_scores(detector, extract, test_ds)
    rows = [
        result_row("validation", val_scores, threshold, margin_threshold),
        result_row("test", test_scores, threshold, margin_threshold),
    ]
    frame = pd.DataFrame(rows)
    common.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(RESULTS_PATH, index=False)

    display_columns = [
        "split", "n_clean_images", "p50", "p75", "p90", "p95", "p99",
        "clean_fpr_at_detector_threshold",
        "clean_fpr_at_margin_threshold",
        "threshold_required_for_10pct_fpr",
    ]
    print("\nClean detector-score distribution shift (v2b detector)")
    print(frame[display_columns].round(4).to_string(index=False))
    print("\nsaved:", RESULTS_PATH)

    try:
        from scipy.stats import ks_2samp
        result = ks_2samp(val_scores, test_scores)
        print(f"KS test validation vs test: D={result.statistic:.4f} "
              f"p={result.pvalue:.3e}")
    except Exception as exc:
        print("scipy unavailable; KS test skipped:", exc)


if __name__ == "__main__":
    main()
