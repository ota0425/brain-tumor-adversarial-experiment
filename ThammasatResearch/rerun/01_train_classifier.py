"""Stage 1: train the MobileNetV2 brain-tumor classifier, deterministically.

Same architecture and hyperparameters as the student's original notebook
(frozen ImageNet backbone, augmentation, GAP, dropout 0.2, Adam 1e-3,
10 epochs, checkpoint on val_accuracy, early stop on val_loss) — but with
full seeding, op determinism, a versioned model filename that is never
overwritten, and a manifest entry recording the model hash and clean
test accuracy for downstream guards.
"""
import argparse
import json

import numpy as np
import tensorflow as tf
from sklearn.metrics import classification_report, confusion_matrix

import common


def build_model(num_classes):
    layers = tf.keras.layers
    augmentation = tf.keras.Sequential([
        layers.RandomRotation(0.05),
        layers.RandomZoom(0.1),
        layers.RandomContrast(0.1),
    ], name="data_augmentation")
    base = tf.keras.applications.MobileNetV2(
        input_shape=(*common.IMAGE_SIZE, 3), include_top=False,
        weights="imagenet",
    )
    base.trainable = False
    inputs = layers.Input(shape=(*common.IMAGE_SIZE, 3))
    x = augmentation(inputs)
    x = tf.keras.applications.mobilenet_v2.preprocess_input(x)
    x = base(x, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.2)(x)
    outputs = layers.Dense(num_classes, activation="softmax")(x)
    model = tf.keras.Model(inputs, outputs)
    model.compile(
        optimizer=tf.keras.optimizers.Adam(learning_rate=1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    return model


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--force", action="store_true",
                        help="allow retraining even if the model file exists")
    args = parser.parse_args()

    if common.CLASSIFIER_PATH.exists() and not args.force:
        raise SystemExit(
            f"{common.CLASSIFIER_PATH} already exists. This pipeline never "
            "silently overwrites a canonical model - rerun with --force only "
            "if you intend to invalidate ALL downstream results."
        )

    common.set_determinism()
    train_ds, val_ds, test_ds, class_names = common.make_datasets()
    autotune = tf.data.AUTOTUNE
    train_ds_p = train_ds.prefetch(autotune)
    val_ds_p = val_ds.prefetch(autotune)
    test_ds_p = test_ds.prefetch(autotune)

    model = build_model(len(class_names))
    common.MODELS_DIR.mkdir(parents=True, exist_ok=True)
    callbacks = [
        tf.keras.callbacks.ModelCheckpoint(
            filepath=str(common.CLASSIFIER_PATH), monitor="val_accuracy",
            mode="max", save_best_only=True, verbose=1,
        ),
        tf.keras.callbacks.EarlyStopping(
            monitor="val_loss", patience=3, restore_best_weights=True,
            verbose=1,
        ),
    ]
    history = model.fit(train_ds_p, validation_data=val_ds_p, epochs=10,
                        callbacks=callbacks)

    best = tf.keras.models.load_model(common.CLASSIFIER_PATH)
    correct, total, y_true, y_pred = common.evaluate_clean(best, test_ds_p)
    accuracy = correct / total
    cm = confusion_matrix(y_true, y_pred)
    report = classification_report(y_true, y_pred, target_names=class_names,
                                   output_dict=True, zero_division=0)

    common.RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    (common.RESULTS_DIR / "classifier_history.json").write_text(
        json.dumps(history.history, indent=2), encoding="utf-8")
    (common.RESULTS_DIR / "classifier_test_report.json").write_text(
        json.dumps({
            "clean_test_accuracy": accuracy,
            "clean_correct": correct,
            "total": total,
            "confusion_matrix": cm.tolist(),
            "classification_report": report,
        }, indent=2), encoding="utf-8")
    common.update_manifest(
        classifier_path=str(common.CLASSIFIER_PATH),
        classifier_sha256=common.sha256_of(common.CLASSIFIER_PATH),
        clean_test_accuracy=accuracy,
        clean_correct=correct,
        class_names=class_names,
        seed=common.SEED,
        tensorflow_version=tf.__version__,
    )
    print(f"\nclean test accuracy: {accuracy:.4f} ({correct}/{total})")
    print("confusion matrix:")
    print(cm)
    print("manifest written:", common.MANIFEST_PATH)


if __name__ == "__main__":
    main()
