"""Shared helpers for the deterministic re-run of the brain-tumor adversarial pipeline.

Every stage script imports this module. Chain-of-custody rules:
- the dataset zip must match DATASET_SHA256 before extraction
- every trained model's SHA-256 goes into results/manifest.json
- every downstream stage verifies the classifier hash AND its clean test
  accuracy against the manifest before doing any work (fail-closed)
"""
import hashlib
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import tensorflow as tf

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 32
VALIDATION_SPLIT = 0.20
TRAIN_EPSILONS = (0.01, 0.1, 0.5)
UNSEEN_EPSILONS = (0.05, 0.25, 1.0)
ALL_EPSILONS = tuple(sorted(set(TRAIN_EPSILONS + UNSEEN_EPSILONS)))

BASE = Path(os.environ.get("TR_BASE", str(Path.home() / "ThammasatResearch")))
DATASET_ZIP = BASE / "dataset" / "archive.zip"
DATA_ROOT = BASE / "dataset" / "extracted"
MODELS_DIR = BASE / "models"
RESULTS_DIR = BASE / "results"
MANIFEST_PATH = RESULTS_DIR / "manifest.json"

CLASSIFIER_PATH = MODELS_DIR / "classifier_seed42.keras"
DATASET_SHA256 = "882817250048c78ef7a759cf23e540d7b581f2327b16663c9d3db12f5d2ffdb4"

ACCURACY_TOLERANCE = 0.003  # allowed drift when re-verifying clean accuracy


def set_determinism():
    os.environ["PYTHONHASHSEED"] = str(SEED)
    tf.keras.utils.set_random_seed(SEED)
    tf.config.experimental.enable_op_determinism()


def sha256_of(path, chunk=1 << 20):
    digest = hashlib.sha256()
    with open(path, "rb") as handle:
        while True:
            block = handle.read(chunk)
            if not block:
                break
            digest.update(block)
    return digest.hexdigest()


def load_manifest():
    if MANIFEST_PATH.exists():
        return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def update_manifest(**entries):
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    manifest = load_manifest()
    manifest.update(entries)
    MANIFEST_PATH.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def ensure_dataset():
    assert DATASET_ZIP.exists(), f"dataset zip missing: {DATASET_ZIP}"
    actual = sha256_of(DATASET_ZIP)
    assert actual == DATASET_SHA256, (
        f"dataset zip hash mismatch:\n  expected {DATASET_SHA256}\n  actual   {actual}"
    )
    train_dir = DATA_ROOT / "Training"
    test_dir = DATA_ROOT / "Testing"
    if not (train_dir.exists() and test_dir.exists()):
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(DATASET_ZIP) as zf:
            zf.extractall(DATA_ROOT)
    assert train_dir.exists() and test_dir.exists()
    return train_dir, test_dir


def make_datasets():
    train_dir, test_dir = ensure_dataset()
    train_ds, val_ds = tf.keras.utils.image_dataset_from_directory(
        train_dir, validation_split=VALIDATION_SPLIT, subset="both",
        seed=SEED, image_size=IMAGE_SIZE, batch_size=BATCH_SIZE,
        label_mode="int", shuffle=True,
    )
    test_ds = tf.keras.utils.image_dataset_from_directory(
        test_dir, image_size=IMAGE_SIZE, batch_size=BATCH_SIZE,
        label_mode="int", shuffle=False,
    )
    class_names = list(train_ds.class_names)
    assert class_names == list(val_ds.class_names) == list(test_ds.class_names)
    train_paths = set(train_ds.file_paths)
    val_paths = set(val_ds.file_paths)
    assert not (train_paths & val_paths), "train/val overlap"
    assert len(train_paths) == 4480, len(train_paths)
    assert len(val_paths) == 1120, len(val_paths)
    assert len(test_ds.file_paths) == 1600, len(test_ds.file_paths)
    return train_ds, val_ds, test_ds, class_names


def evaluate_clean(model, test_ds):
    """Return (correct_count, total, y_true, y_pred) on the test set."""
    y_true, y_pred = [], []
    for images, labels in test_ds:
        probs = model(images, training=False).numpy()
        y_pred.extend(np.argmax(probs, axis=1))
        y_true.extend(labels.numpy())
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)
    return int((y_true == y_pred).sum()), len(y_true), y_true, y_pred


def load_classifier_verified(test_ds=None):
    """Load the canonical classifier, verifying hash and (optionally) accuracy."""
    manifest = load_manifest()
    assert "classifier_sha256" in manifest, (
        "manifest has no classifier entry - run 01_train_classifier.py first"
    )
    actual = sha256_of(CLASSIFIER_PATH)
    assert actual == manifest["classifier_sha256"], (
        "classifier file hash does not match manifest - the model file changed "
        "since training. Refusing to run on mixed-era artifacts.\n"
        f"  manifest {manifest['classifier_sha256']}\n  actual   {actual}"
    )
    model = tf.keras.models.load_model(CLASSIFIER_PATH)
    model.trainable = False
    if test_ds is not None:
        correct, total, _, _ = evaluate_clean(model, test_ds)
        expected = manifest["clean_test_accuracy"]
        got = correct / total
        assert abs(got - expected) <= ACCURACY_TOLERANCE, (
            f"clean accuracy drifted: manifest {expected:.4f}, got {got:.4f}"
        )
        print(f"classifier verified: sha256 ok, clean acc {got:.4f} "
              f"({correct}/{total})")
    return model


# ---- FGSM (identical math to the student's notebooks, 0-255 input scale) ----
_scce = tf.keras.losses.SparseCategoricalCrossentropy()


def compute_fgsm_direction(model, images, labels):
    images = tf.cast(images, tf.float32)
    labels = tf.cast(labels, tf.int32)
    with tf.GradientTape() as tape:
        tape.watch(images)
        predictions = model(images, training=False)
        loss = _scce(labels, predictions)
    gradients = tape.gradient(loss, images)
    if gradients is None:
        raise RuntimeError("FGSM input gradients could not be computed")
    return predictions, tf.sign(gradients)


def create_adversarial_images(images, signed_gradients, epsilon):
    images = tf.cast(images, tf.float32)
    adv = images + tf.cast(epsilon, tf.float32) * signed_gradients
    return tf.clip_by_value(adv, 0.0, 255.0)
