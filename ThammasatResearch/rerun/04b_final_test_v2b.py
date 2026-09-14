"""Stage 4b: FINAL test of the calibrated detector (v2b), one run, guarded.

Same protocol as stage 4, but for the detector whose threshold was selected
on the leakage-free calibration split (val_B). The primary claim uses the
FPR<=10% threshold; the margin threshold (FPR<=7.5% on calibration) is
reported as one informational line, not a second bite at the test set.
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
    record = json.loads(d3b.THRESHOLD_PATH.read_text(encoding="utf-8"))
    threshold = record["threshold"]
    margin_threshold = record["margin_threshold"]
    assert abs(threshold - manifest["detector_v2b_threshold"]) < 1e-12
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)

    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)
    test_data = d3.collect_split(classifier, extract, test_ds,
                                 common.ALL_EPSILONS, "Testing")

    clean_scores = detector.predict(
        test_data["clean_features"], batch_size=256).reshape(-1)
    clean_fpr = float(np.mean(clean_scores >= threshold))
    clean_fpr_margin = float(np.mean(clean_scores >= margin_threshold))
    initially_correct = test_data["clean_correct"]

    rows = []
    for eps in common.ALL_EPSILONS:
        rec = test_data["adversarial"][eps]
        adv_scores = detector.predict(
            rec["features"], batch_size=256).reshape(-1)
        success = rec["success"]
        success_scores = adv_scores[success]
        labels = np.concatenate([np.zeros(clean_scores.size),
                                 np.ones(success_scores.size)])
        scores = np.concatenate([clean_scores, success_scores])
        rows.append({
            "epsilon": eps,
            "epsilon_status": ("known" if eps in common.TRAIN_EPSILONS
                               else "unseen"),
            "source_images": int(success.size),
            "initially_correct_images": int(initially_correct.sum()),
            "successful_attacks": int(success.sum()),
            "attack_success_rate_on_initially_correct":
                float(success.sum() / initially_correct.sum()),
            "clean_false_positive_rate": clean_fpr,
            "successful_attack_detection_rate":
                float(np.mean(success_scores >= threshold))
                if success_scores.size else np.nan,
            "successful_attack_detection_rate_margin":
                float(np.mean(success_scores >= margin_threshold))
                if success_scores.size else np.nan,
            "all_attack_detection_rate":
                float(np.mean(adv_scores >= threshold)),
            "successful_vs_clean_roc_auc":
                float(roc_auc_score(labels, scores))
                if success_scores.size else np.nan,
            "successful_vs_clean_pr_auc":
                float(average_precision_score(labels, scores))
                if success_scores.size else np.nan,
            "selected_threshold": threshold,
        })
    df = pd.DataFrame(rows).sort_values("epsilon")
    out = common.RESULTS_DIR / "detector_v2b_test_by_epsilon.csv"
    df.to_csv(out, index=False)
    print(df.round(4).to_string(index=False))
    print("saved:", out)
    print(f"clean test FPR at primary threshold: {clean_fpr:.4f} "
          f"(calibration FPR was {record['calibration_fpr']:.4f})")
    print(f"clean test FPR at margin threshold: {clean_fpr_margin:.4f} "
          f"(calibration FPR was {record['margin_fpr']:.4f})")


if __name__ == "__main__":
    main()
