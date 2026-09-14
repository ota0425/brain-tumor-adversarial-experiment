"""Stage 3: train the consistency-feature detector (student's Experiment 2)
and select the operating threshold on Validation (FPR <= 10%).

Positive class = successful attacks (clean correct -> adversarial wrong).
Features = GAP features + probabilities + blur-consistency + confidence/
margin/entropy, exactly as in the student's v2 notebook.
Guards: classifier hash + clean accuracy verified; detector hash and the
selected threshold are recorded in the manifest for the final-test guard.
"""
import argparse
import json

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import average_precision_score, roc_auc_score, roc_curve

import common

TARGET_MAX_FPR = 0.10
DETECTOR_PATH = common.MODELS_DIR / "detector_v2_seed42.keras"
THRESHOLD_PATH = common.RESULTS_DIR / "detector_v2_threshold.json"


def build_representation_model(classifier):
    gap_layers = [l for l in classifier.layers
                  if isinstance(l, tf.keras.layers.GlobalAveragePooling2D)]
    assert gap_layers, "GlobalAveragePooling2D not found in classifier"
    rep = tf.keras.Model(classifier.input,
                         [gap_layers[-1].output, classifier.output])
    rep.trainable = False
    return rep


def make_feature_fn(classifier, rep):
    @tf.function
    def extract(images):
        images = tf.cast(images, tf.float32)
        blurred = tf.nn.avg_pool2d(images, ksize=3, strides=1, padding="SAME")
        feats, probs = rep(images, training=False)
        bfeats, bprobs = rep(blurred, training=False)
        prob_diff = tf.abs(probs - bprobs)
        feat_diff = tf.abs(feats - bfeats)
        confidence = tf.reduce_max(probs, axis=1, keepdims=True)
        sorted_probs = tf.sort(probs, axis=1)
        margin = (sorted_probs[:, -1] - sorted_probs[:, -2])[:, None]
        entropy = -tf.reduce_sum(probs * tf.math.log(probs + 1e-7),
                                 axis=1, keepdims=True)
        diff_summary = tf.stack([
            tf.reduce_mean(feat_diff, axis=1),
            tf.math.reduce_std(feat_diff, axis=1),
            tf.reduce_max(feat_diff, axis=1),
        ], axis=1)
        return tf.concat([feats, probs, bprobs, prob_diff, confidence,
                          margin, entropy, diff_summary], axis=1)
    return extract


def collect_split(classifier, extract, dataset, epsilons, name):
    clean_feats, clean_correct = [], []
    adv = {e: {"features": [], "success": []} for e in epsilons}
    for i, (images, labels) in enumerate(dataset):
        labels_np = labels.numpy().reshape(-1)
        clean_feats.append(extract(images).numpy())
        probs = classifier(images, training=False).numpy()
        correct = np.argmax(probs, axis=1) == labels_np
        clean_correct.append(correct)
        _, signed = common.compute_fgsm_direction(classifier, images, labels)
        for eps in epsilons:
            adv_images = common.create_adversarial_images(images, signed, eps)
            adv_probs = classifier(adv_images, training=False).numpy()
            success = correct & (np.argmax(adv_probs, axis=1) != labels_np)
            adv[eps]["features"].append(extract(adv_images).numpy())
            adv[eps]["success"].append(success)
        if (i + 1) % 25 == 0:
            print(f"{name}: {i + 1} batches")
    return {
        "clean_features": np.concatenate(clean_feats),
        "clean_correct": np.concatenate(clean_correct),
        "adversarial": {
            e: {"features": np.concatenate(r["features"]),
                "success": np.concatenate(r["success"])}
            for e, r in adv.items()
        },
    }


def build_xy(data, epsilons):
    neg = data["clean_features"]
    pos_parts, counts = [], {}
    for eps in epsilons:
        rec = data["adversarial"][eps]
        sel = rec["features"][rec["success"]]
        pos_parts.append(sel)
        counts[str(eps)] = int(sel.shape[0])
    pos = np.concatenate(pos_parts)
    x = np.concatenate([neg, pos]).astype(np.float32)
    y = np.concatenate([np.zeros(len(neg), np.float32),
                        np.ones(len(pos), np.float32)])
    return x, y, counts


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
    rep = build_representation_model(classifier)
    extract = make_feature_fn(classifier, rep)

    train_data = collect_split(classifier, extract, train_ds,
                               common.TRAIN_EPSILONS, "Training")
    val_data = collect_split(classifier, extract, val_ds,
                             common.TRAIN_EPSILONS, "Validation")
    train_x, train_y, train_counts = build_xy(train_data, common.TRAIN_EPSILONS)
    val_x, val_y, val_counts = build_xy(val_data, common.TRAIN_EPSILONS)
    print("train:", train_x.shape, train_counts)
    print("val:", val_x.shape, val_counts)

    normalizer = tf.keras.layers.Normalization()
    normalizer.adapt(train_x)
    inputs = tf.keras.Input(shape=(train_x.shape[1],))
    h = normalizer(inputs)
    h = tf.keras.layers.Dense(256, activation="relu")(h)
    h = tf.keras.layers.Dropout(0.35)(h)
    h = tf.keras.layers.Dense(64, activation="relu")(h)
    h = tf.keras.layers.Dropout(0.20)(h)
    outputs = tf.keras.layers.Dense(1, activation="sigmoid")(h)
    detector = tf.keras.Model(inputs, outputs, name="detector_v2")
    detector.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="binary_crossentropy",
        metrics=[tf.keras.metrics.AUC(name="roc_auc"),
                 tf.keras.metrics.AUC(name="pr_auc", curve="PR")],
    )
    class_weight = {0: 1.0, 1: float((train_y == 0).sum() / (train_y == 1).sum())}
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
                           validation_data=(val_x, val_y),
                           epochs=30, batch_size=64,
                           class_weight=class_weight,
                           callbacks=callbacks, verbose=2)
    pd.DataFrame(history.history).to_csv(
        common.RESULTS_DIR / "detector_v2_history.csv", index_label="epoch")

    detector = tf.keras.models.load_model(DETECTOR_PATH)
    val_scores = detector.predict(val_x, batch_size=256).reshape(-1)
    fpr, tpr, thresholds = roc_curve(val_y, val_scores)
    eligible = np.flatnonzero(fpr <= TARGET_MAX_FPR)
    assert eligible.size, "no threshold satisfies the FPR constraint"
    best = eligible[np.argmax(tpr[eligible])]
    record = {
        "threshold": float(thresholds[best]),
        "validation_fpr": float(fpr[best]),
        "validation_tpr": float(tpr[best]),
        "validation_roc_auc": float(roc_auc_score(val_y, val_scores)),
        "validation_pr_auc": float(average_precision_score(val_y, val_scores)),
        "train_success_counts": train_counts,
        "validation_success_counts": val_counts,
    }
    THRESHOLD_PATH.write_text(json.dumps(record, indent=2), encoding="utf-8")
    common.update_manifest(
        detector_v2_path=str(DETECTOR_PATH),
        detector_v2_sha256=common.sha256_of(DETECTOR_PATH),
        detector_v2_threshold=record["threshold"],
    )
    print(json.dumps(record, indent=2))
    print("saved:", DETECTOR_PATH, "and", THRESHOLD_PATH)


if __name__ == "__main__":
    main()
