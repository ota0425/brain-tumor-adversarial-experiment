"""Stage 2: FGSM attack sweep on the verified classifier (test set).

Reproduces the student's "fine" sweep (epsilon 0-1 on the 0-255 scale)
plus epsilon 2, 4, 8 from the coarse sweep, in one table.
Guards: classifier hash + clean accuracy re-verified before attacking.
"""
import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import accuracy_score

import common

EPSILONS = [0, 0.01, 0.05, 0.1, 0.25, 0.5, 1, 2, 4, 8]


def main():
    common.set_determinism()
    _, _, test_ds, class_names = common.make_datasets()
    test_ds = test_ds.prefetch(tf.data.AUTOTUNE)
    model = common.load_classifier_verified(test_ds)

    y_true, clean_pred = [], []
    adv_pred = {eps: [] for eps in EPSILONS}
    for images, labels in test_ds:
        clean_probs, signed = common.compute_fgsm_direction(model, images, labels)
        y_true.extend(labels.numpy())
        clean_pred.extend(tf.argmax(clean_probs, axis=1).numpy())
        for eps in EPSILONS:
            adv = common.create_adversarial_images(images, signed, eps)
            probs = model(adv, training=False)
            adv_pred[eps].extend(tf.argmax(probs, axis=1).numpy())

    y_true = np.array(y_true)
    clean_pred = np.array(clean_pred)
    clean_correct = clean_pred == y_true
    n_correct = int(clean_correct.sum())
    clean_acc = accuracy_score(y_true, clean_pred)

    rows = []
    for eps in EPSILONS:
        pred = np.array(adv_pred[eps])
        adv_acc = accuracy_score(y_true, pred)
        success = clean_correct & (pred != y_true)
        rows.append({
            "epsilon": eps,
            "clean_accuracy": clean_acc,
            "adversarial_accuracy": adv_acc,
            "accuracy_drop": clean_acc - adv_acc,
            "attack_success_rate": success.sum() / n_correct,
            "successful_attacks": int(success.sum()),
            "clean_correct_images": n_correct,
        })
    df = pd.DataFrame(rows)
    out = common.RESULTS_DIR / "fgsm_summary.csv"
    df.to_csv(out, index=False)
    print(df.to_string(index=False))
    print("saved:", out)


if __name__ == "__main__":
    main()
