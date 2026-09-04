"""Stage 6: PGD cross-attack evaluation of the FGSM-trained detector.

The detector (v2b) and its deployment-calibrated threshold were built from
FGSM data only. Here we attack the classifier with PGD (Madry et al.,
random start, alpha = eps/4, K in {10, 40}) — an attack family the
detector has NEVER seen — and measure whether it still detects the
successful attacks. Nothing is retrained; this is pure evaluation.

Protocol:
- Same Testing calib-400 / eval-1200 split as stage 5 (same seed) so every
  number is comparable row-for-row with the FGSM deploycal table.
- All reported metrics come from the 1200 eval images only.
- Thresholds are the stage-5 deployment values, loaded and hash-checked —
  Testing is never used to re-tune anything here.
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
d5 = import_module("05_deployment_calibration")

PGD_STEPS = (10, 40)
RESULTS_PATH = common.RESULTS_DIR / "pgd_eval_by_epsilon.csv"

_scce = tf.keras.losses.SparseCategoricalCrossentropy()


def make_pgd_fn(model, epsilon, alpha, steps):
    @tf.function
    def pgd_attack(images, labels):
        images = tf.cast(images, tf.float32)
        labels_i = tf.cast(labels, tf.int32)
        delta = tf.random.uniform(tf.shape(images), -epsilon, epsilon)
        adv = tf.clip_by_value(images + delta, 0.0, 255.0)
        for _ in tf.range(steps):
            with tf.GradientTape() as tape:
                tape.watch(adv)
                predictions = model(adv, training=False)
                loss = _scce(labels_i, predictions)
            gradients = tape.gradient(loss, adv)
            adv = adv + alpha * tf.sign(gradients)
            adv = tf.clip_by_value(adv, images - epsilon, images + epsilon)
            adv = tf.clip_by_value(adv, 0.0, 255.0)
        return adv
    return pgd_attack


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
    assert d5.THRESHOLD_PATH.exists(), "run 05 first"
    cal = json.loads(d5.THRESHOLD_PATH.read_text(encoding="utf-8"))
    assert cal["detector_sha256"] == actual
    threshold = cal["threshold"]
    margin_threshold = cal["margin_threshold"]
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)

    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)

    # same deterministic calib/eval split as stage 5
    rng = np.random.default_rng(common.SEED)
    perm = rng.permutation(1600)
    eval_idx = np.sort(perm[d5.CALIB_SIZE:])

    # clean pass, once
    clean_scores_all, clean_correct_all = [], []
    for images, labels in test_ds:
        probs = classifier(images, training=False).numpy()
        clean_correct_all.append(
            np.argmax(probs, axis=1) == labels.numpy().reshape(-1))
        clean_scores_all.append(detector.predict(
            extract(images).numpy(), batch_size=256, verbose=0).reshape(-1))
    clean_correct = np.concatenate(clean_correct_all)
    clean_scores = np.concatenate(clean_scores_all)
    assert clean_correct.size == 1600
    eval_clean_scores = clean_scores[eval_idx]
    eval_clean_correct = clean_correct[eval_idx]
    eval_clean_fpr = float(np.mean(eval_clean_scores >= threshold))
    print(f"clean eval FPR at deployment threshold: {eval_clean_fpr:.4f} "
          f"(stage 5 recorded {cal['eval_clean_fpr']:.4f})")

    rows = []
    for steps in PGD_STEPS:
        for eps in common.ALL_EPSILONS:
            alpha = eps / 4.0
            pgd = make_pgd_fn(classifier, float(eps), float(alpha), int(steps))
            adv_scores_all, success_all = [], []
            for images, labels in test_ds:
                labels_np = labels.numpy().reshape(-1)
                adv = pgd(images, labels)
                perturbation = adv - tf.cast(images, tf.float32)
                max_pert = float(tf.reduce_max(tf.abs(perturbation)))
                assert max_pert <= eps + 1e-4, (eps, steps, max_pert)
                adv_probs = classifier(adv, training=False).numpy()
                batch_clean_correct = (
                    np.argmax(classifier(images, training=False).numpy(),
                              axis=1) == labels_np)
                success_all.append(
                    batch_clean_correct
                    & (np.argmax(adv_probs, axis=1) != labels_np))
                adv_scores_all.append(detector.predict(
                    extract(adv).numpy(), batch_size=256,
                    verbose=0).reshape(-1))
            success = np.concatenate(success_all)[eval_idx]
            adv_scores = np.concatenate(adv_scores_all)[eval_idx]
            success_scores = adv_scores[success]
            labels_bin = np.concatenate([
                np.zeros(eval_clean_scores.size),
                np.ones(success_scores.size)])
            scores_bin = np.concatenate([eval_clean_scores, success_scores])
            row = {
                "attack": f"pgd{steps}",
                "pgd_steps": steps,
                "epsilon": eps,
                "epsilon_status": ("known" if eps in common.TRAIN_EPSILONS
                                   else "unseen"),
                "eval_images": int(eval_idx.size),
                "initially_correct_images": int(eval_clean_correct.sum()),
                "successful_attacks": int(success.sum()),
                "attack_success_rate_on_initially_correct":
                    float(success.sum() / eval_clean_correct.sum()),
                "clean_false_positive_rate": eval_clean_fpr,
                "successful_attack_detection_rate":
                    float(np.mean(success_scores >= threshold))
                    if success_scores.size else np.nan,
                "successful_attack_detection_rate_margin":
                    float(np.mean(success_scores >= margin_threshold))
                    if success_scores.size else np.nan,
                "successful_vs_clean_roc_auc":
                    float(roc_auc_score(labels_bin, scores_bin))
                    if success_scores.size else np.nan,
                "successful_vs_clean_pr_auc":
                    float(average_precision_score(labels_bin, scores_bin))
                    if success_scores.size else np.nan,
                "selected_threshold": threshold,
            }
            rows.append(row)
            print(f"pgd{steps} eps={eps}: success="
                  f"{row['attack_success_rate_on_initially_correct']:.4f} "
                  f"detect={row['successful_attack_detection_rate']:.4f} "
                  f"roc_auc={row['successful_vs_clean_roc_auc']:.4f}")

    df = pd.DataFrame(rows).sort_values(["pgd_steps", "epsilon"])
    df.to_csv(RESULTS_PATH, index=False)
    print(df.round(4).to_string(index=False))
    print("saved:", RESULTS_PATH)


if __name__ == "__main__":
    main()
