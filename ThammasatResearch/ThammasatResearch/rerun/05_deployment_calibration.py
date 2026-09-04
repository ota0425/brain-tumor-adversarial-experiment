"""Stage 5: deployment-domain calibration of detector v2b.

Finding from stages 4/4b: the Training/ and Testing/ folders of this
dataset are different collections, so a threshold calibrated on any
Training-derived split cannot pin the test FPR (stable ~+3.8pt shift in
the clean-score upper tail). Standard remedy: calibrate the threshold on
a small held-out slice of the deployment distribution itself.

Protocol (stated plainly for the paper's methods section):
- Testing/ (1600) is split deterministically into calib 400 / eval 1200.
- The threshold is the smallest value with clean FPR <= 10% on the 400
  CLEAN calibration images only — no attack data needed to calibrate,
  which is deployment-realistic. A 7.5% margin variant is also recorded.
- All reported numbers come from the 1200 eval images only.
- The detector and classifier are untouched (hash-guarded); this changes
  the operating point, not the model.
"""
import json
from importlib import import_module

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import average_precision_score, roc_auc_score

import common

d3 = import_module("03_detector_v2")
d3b = import_module("03b_detector_v2_calibrated")

CALIB_SIZE = 400
TARGET_MAX_FPR = 0.10
MARGIN_MAX_FPR = 0.075
THRESHOLD_PATH = common.RESULTS_DIR / "deployment_calibration_threshold.json"
RESULTS_PATH = common.RESULTS_DIR / "detector_v2b_deploycal_eval_by_epsilon.csv"


def quantile_threshold(clean_scores, max_fpr):
    """Smallest threshold with FPR <= max_fpr on the given clean scores."""
    threshold = float(np.quantile(clean_scores, 1.0 - max_fpr,
                                  method="higher"))
    fpr = float(np.mean(clean_scores >= threshold))
    if fpr > max_fpr:  # ties at the quantile value can overshoot
        eligible = np.unique(clean_scores)
        eligible = eligible[[
            np.mean(clean_scores >= t) <= max_fpr for t in eligible
        ]]
        assert eligible.size, f"no threshold satisfies FPR <= {max_fpr}"
        threshold = float(eligible.min())
        fpr = float(np.mean(clean_scores >= threshold))
    return threshold, fpr


def main():
    common.set_determinism()
    _, _, test_ds, _ = common.make_datasets()
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
    test_data = d3.collect_split(classifier, extract, test_ds,
                                 common.ALL_EPSILONS, "Testing")

    n_test = test_data["clean_features"].shape[0]
    assert n_test == 1600, n_test
    rng = np.random.default_rng(common.SEED)
    perm = rng.permutation(n_test)
    calib_idx = np.sort(perm[:CALIB_SIZE])
    eval_idx = np.sort(perm[CALIB_SIZE:])
    assert not set(calib_idx) & set(eval_idx)

    clean_scores = detector.predict(
        test_data["clean_features"], batch_size=256).reshape(-1)
    calib_clean = clean_scores[calib_idx]
    eval_clean = clean_scores[eval_idx]

    threshold, calib_fpr = quantile_threshold(calib_clean, TARGET_MAX_FPR)
    margin_threshold, margin_calib_fpr = quantile_threshold(
        calib_clean, MARGIN_MAX_FPR)
    eval_fpr = float(np.mean(eval_clean >= threshold))
    eval_fpr_margin = float(np.mean(eval_clean >= margin_threshold))

    record = {
        "protocol": "deployment calibration: Testing split 400 calib / "
                    "1200 eval, threshold from clean calib scores only",
        "calib_size": CALIB_SIZE,
        "eval_size": int(eval_idx.size),
        "split_seed": common.SEED,
        "threshold": threshold,
        "calibration_fpr": calib_fpr,
        "margin_threshold": margin_threshold,
        "margin_calibration_fpr": margin_calib_fpr,
        "eval_clean_fpr": eval_fpr,
        "eval_clean_fpr_margin": eval_fpr_margin,
        "detector_sha256": actual,
    }
    THRESHOLD_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")

    initially_correct = test_data["clean_correct"][eval_idx]
    rows = []
    for eps in common.ALL_EPSILONS:
        rec = test_data["adversarial"][eps]
        adv_scores = detector.predict(
            rec["features"], batch_size=256).reshape(-1)[eval_idx]
        success = rec["success"][eval_idx]
        success_scores = adv_scores[success]
        labels = np.concatenate([np.zeros(eval_clean.size),
                                 np.ones(success_scores.size)])
        scores = np.concatenate([eval_clean, success_scores])
        rows.append({
            "epsilon": eps,
            "epsilon_status": ("known" if eps in common.TRAIN_EPSILONS
                               else "unseen"),
            "eval_images": int(eval_idx.size),
            "initially_correct_images": int(initially_correct.sum()),
            "successful_attacks": int(success.sum()),
            "clean_false_positive_rate": eval_fpr,
            "successful_attack_detection_rate":
                float(np.mean(success_scores >= threshold))
                if success_scores.size else np.nan,
            "successful_attack_detection_rate_margin":
                float(np.mean(success_scores >= margin_threshold))
                if success_scores.size else np.nan,
            "successful_vs_clean_roc_auc":
                float(roc_auc_score(labels, scores))
                if success_scores.size else np.nan,
            "successful_vs_clean_pr_auc":
                float(average_precision_score(labels, scores))
                if success_scores.size else np.nan,
            "selected_threshold": threshold,
        })
    df = pd.DataFrame(rows).sort_values("epsilon")
    df.to_csv(RESULTS_PATH, index=False)
    print(df.round(4).to_string(index=False))
    print("saved:", RESULTS_PATH, "and", THRESHOLD_PATH)
    print(f"threshold {threshold:.4f}: calib FPR {calib_fpr:.4f} -> "
          f"eval FPR {eval_fpr:.4f}")
    print(f"margin threshold {margin_threshold:.4f}: calib FPR "
          f"{margin_calib_fpr:.4f} -> eval FPR {eval_fpr_margin:.4f}")


if __name__ == "__main__":
    main()
