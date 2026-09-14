"""Stage 3b: retrain detector v2 with a leakage-free calibration split.

Fix for the threshold-generalization gap found in stage 4: previously the
FPR<=10% threshold was selected on the SAME 1120-image validation set used
for the detector's early stopping / checkpointing, so the operating point
was tuned on data that had already influenced model selection.

Here the 1120 validation source images are split deterministically into
  val_A (560): model selection only (checkpoint + early stopping)
  val_B (560): threshold calibration only - never touches training
The detector is retrained from scratch (cheap), saved under a NEW name,
and the threshold json records both the primary FPR<=10% threshold and a
margin variant at FPR<=7.5% for reference.
"""
import argparse
import json
from importlib import import_module

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

import common

d3 = import_module("03_detector_v2")

TARGET_MAX_FPR = 0.10
MARGIN_MAX_FPR = 0.075
DETECTOR_PATH = common.MODELS_DIR / "detector_v2b_seed42.keras"
THRESHOLD_PATH = common.RESULTS_DIR / "detector_v2b_threshold.json"


def split_indices(n, seed=common.SEED):
    rng = np.random.default_rng(seed)
    perm = rng.permutation(n)
    half = n // 2
    return np.sort(perm[:half]), np.sort(perm[half:])


def subset_split_data(data, indices):
    """Restrict a collect_split() result to a subset of source images."""
    return {
        "clean_features": data["clean_features"][indices],
        "clean_correct": data["clean_correct"][indices],
        "adversarial": {
            eps: {"features": rec["features"][indices],
                  "success": rec["success"][indices]}
            for eps, rec in data["adversarial"].items()
        },
    }


def pick_threshold(y, scores, max_fpr):
    fpr, tpr, thresholds = roc_curve(y, scores)
    eligible = np.flatnonzero(fpr <= max_fpr)
    assert eligible.size, f"no threshold satisfies FPR <= {max_fpr}"
    best = eligible[np.argmax(tpr[eligible])]
    return float(thresholds[best]), float(fpr[best]), float(tpr[best])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if DETECTOR_PATH.exists() and not args.force:
        raise SystemExit(f"{DETECTOR_PATH} exists; use --force to retrain")

    common.set_determinism()
    train_ds, val_ds, test_ds, _ = common.make_datasets()
    classifier = common.load_classifier_verified(
        test_ds.prefetch(tf.data.AUTOTUNE))
    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)

    train_data = d3.collect_split(classifier, extract, train_ds,
                                  common.TRAIN_EPSILONS, "Training")
    val_data = d3.collect_split(classifier, extract, val_ds,
                                common.TRAIN_EPSILONS, "Validation")

    n_val = val_data["clean_features"].shape[0]
    assert n_val == 1120, n_val
    idx_a, idx_b = split_indices(n_val)
    assert idx_a.size == 560 and idx_b.size == 560
    assert not set(idx_a) & set(idx_b)
    val_a = subset_split_data(val_data, idx_a)
    val_b = subset_split_data(val_data, idx_b)

    train_x, train_y, train_counts = d3.build_xy(train_data,
                                                 common.TRAIN_EPSILONS)
    val_a_x, val_a_y, val_a_counts = d3.build_xy(val_a, common.TRAIN_EPSILONS)
    val_b_x, val_b_y, val_b_counts = d3.build_xy(val_b, common.TRAIN_EPSILONS)
    print("train:", train_x.shape, train_counts)
    print("val_A (model selection):", val_a_x.shape, val_a_counts)
    print("val_B (calibration):", val_b_x.shape, val_b_counts)

    normalizer = tf.keras.layers.Normalization()
    normalizer.adapt(train_x)
    inputs = tf.keras.Input(shape=(train_x.shape[1],))
    h = normalizer(inputs)
    h = tf.keras.layers.Dense(256, activation="relu")(h)
    h = tf.keras.layers.Dropout(0.35)(h)
    h = tf.keras.layers.Dense(64, activation="relu")(h)
    h = tf.keras.layers.Dropout(0.20)(h)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(h)
    detector = tf.keras.Model(inputs, outputs, name="detector_v2b")
    detector.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=[tf.keras.metrics.AUC(name="roc_auc"),
                 tf.keras.metrics.AUC(name="pr_auc", curve="PR")],
    )
    class_weight = {0: 1.0,
                    1: float((train_y == 0).sum() / (train_y == 1).sum())}
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(str(DETECTOR_PATH),
                                           monitor="val_roc_auc", mode="max",
                                           save_best_only=True),
        tf.keras.callbacks.EarlyStopping(monitor="val_roc_auc", mode="max",
                                         patience=5,
                                         restore_best_weights=True),
        tf.keras.callbacks.ReduceLROnPlateau(monitor="val_roc_auc", mode="max",
                                             patience=2, factor=0.5,
                                             min_lr=1e-6),
    ]
    history = detector.fit(train_x, train_y,
                           validation_data=(val_a_x, val_a_y),
                           epochs=30, batch_size=64,
                           class_weight=class_weight,
                           callbacks=callbacks, verbose=2)
    pd.DataFrame(history.history).to_csv(
        common.RESULTS_DIR / "detector_v2b_history.csv", index_label="epoch")

    detector = tf.keras.models.load_model(DETECTOR_PATH)
    val_b_scores = detector.predict(val_b_x, batch_size=256).reshape(-1)
    threshold, cal_fpr, cal_tpr = pick_threshold(val_b_y, val_b_scores,
                                                 TARGET_MAX_FPR)
    margin_threshold, margin_fpr, margin_tpr = pick_threshold(
        val_b_y, val_b_scores, MARGIN_MAX_FPR)

    record = {
        "threshold": threshold,
        "calibration_fpr": cal_fpr,
        "calibration_tpr": cal_tpr,
        "calibration_roc_auc": float(roc_auc_score(val_b_y, val_b_scores)),
        "calibration_pr_auc": float(
            average_precision_score(val_b_y, val_b_scores)),
        "margin_threshold": margin_threshold,
        "margin_fpr": margin_fpr,
        "margin_tpr": margin_tpr,
        "split": {"val_A_model_selection": 560, "val_B_calibration": 560,
                  "split_seed": common.SEED},
        "train_success_counts": train_counts,
        "val_a_success_counts": val_a_counts,
        "val_b_success_counts": val_b_counts,
    }
    THRESHOLD_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")
    common.update_manifest(
        detector_v2b_path=str(DETECTOR_PATH),
        detector_v2b_sha256=common.sha256_of(DETECTOR_PATH),
        detector_v2b_threshold=threshold,
        detector_v2b_margin_threshold=margin_threshold,
    )
    print(json.dumps(record, indent=2))
    print("saved:", DETECTOR_PATH, "and", THRESHOLD_PATH)


if __name__ == "__main__":
    main()
