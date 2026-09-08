"""Clean-FPR under dataset-defect exclusions, plus calibration sensitivity.

The exclusion-robustness table could not report clean FPR because
attack_scores.npz stores per-attack scores only. This does the one GPU pass
needed, PERSISTS the clean scores so it never has to be repeated, and then
answers two questions:

  EVALUATION side - at the FIXED stage-5 threshold, does the clean FPR hold
  up when the contaminated subsets are removed from the eval set?

  CALIBRATION side - if the 400-image calibration set itself contains
  augmented or duplicated images, does re-deriving the threshold without
  them move it? This tests whether the deployment-calibration protocol is
  robust to the dataset defects, not just whether the evaluation is.

Splits and threshold are taken from the stage-5 artefact; nothing is
re-tuned except where explicitly stated. Hashes verified before use.
"""
import json
import os
from importlib import import_module

import numpy as np
import pandas as pd
import tensorflow as tf

import common

d3 = import_module("03_detector_v2")
d3b = import_module("03b_detector_v2_calibrated")
d5 = import_module("05_deployment_calibration")

CLEAN_NPZ = common.RESULTS_DIR / "clean_scores.npz"
OUT_CSV = common.RESULTS_DIR / "clean_fpr_exclusion.csv"


def main():
    common.set_determinism()
    _, _, test_ds, class_names = common.make_datasets()
    file_paths = list(test_ds.file_paths)
    names = np.array([os.path.basename(p) for p in file_paths])
    assert len(names) == 1600

    classifier = common.load_classifier_verified()
    manifest = common.load_manifest()
    actual = common.sha256_of(d3b.DETECTOR_PATH)
    assert actual == manifest["detector_v2b_sha256"], "detector hash mismatch"
    cal = json.loads(d5.THRESHOLD_PATH.read_text(encoding="utf-8"))
    assert cal["detector_sha256"] == actual
    threshold = cal["threshold"]
    detector = tf.keras.models.load_model(d3b.DETECTOR_PATH)
    print(f"hashes verified; stage-5 threshold {threshold:.12f}")

    rep = d3.build_representation_model(classifier)
    extract = d3.make_feature_fn(classifier, rep)

    print("computing per-image clean detector scores ...")
    scores, correct = [], []
    for images, labels in test_ds:
        probs = classifier(images, training=False).numpy()
        correct.append(np.argmax(probs, axis=1) == labels.numpy().reshape(-1))
        scores.append(detector.predict(extract(images).numpy(),
                                       batch_size=256, verbose=0).reshape(-1))
    clean_scores = np.concatenate(scores)
    clean_correct = np.concatenate(correct)
    assert clean_scores.shape[0] == 1600

    # verify against the persisted artefacts before trusting anything
    assert abs(clean_correct.mean() - manifest["clean_test_accuracy"]) < 1e-9
    z = np.load(common.RESULTS_DIR / "attack_scores.npz")
    assert (clean_correct == z["clean_correct"]).all(), (
        "clean_correct disagrees with attack_scores.npz - index mapping broken")
    print("index mapping verified against manifest and attack_scores.npz")

    # same deterministic split as stage 5
    rng = np.random.default_rng(common.SEED)
    perm = rng.permutation(1600)
    calib_idx = np.sort(perm[:d5.CALIB_SIZE])
    eval_idx = np.sort(perm[d5.CALIB_SIZE:])
    assert (eval_idx == z["eval_idx"]).all(), "eval split differs from stage 6b"

    np.savez_compressed(CLEAN_NPZ, clean_scores=clean_scores,
                        clean_correct=clean_correct, file_names=names,
                        calib_idx=calib_idx, eval_idx=eval_idx)
    print("persisted:", CLEAN_NPZ)

    # ---- exclusion sets
    leak = pd.read_csv(common.RESULTS_DIR / "pixel_leakage_scan.csv")
    leaked = set(leak[leak.confirmed_duplicate].test_file)
    is_aug = np.array(["aug" in n.lower() for n in names])
    is_leak = np.array([n in leaked for n in names])

    scenarios = {
        "all": np.ones(1600, dtype=bool),
        "no_aug": ~is_aug,
        "no_leak": ~is_leak,
        "no_either": ~(is_aug | is_leak),
    }

    rows = []
    print("\n=== CLEAN FPR AT THE FIXED STAGE-5 THRESHOLD "
          f"({threshold:.6f}) ===")
    for sname, keep in scenarios.items():
        m = np.zeros(1600, dtype=bool)
        m[eval_idx] = True
        m &= keep
        fpr = float((clean_scores[m] >= threshold).mean())
        n_drop_eval = int((np.isin(np.arange(1600), eval_idx) & ~keep).sum())
        rows.append({"analysis": "fixed_threshold", "scenario": sname,
                     "n_eval": int(m.sum()), "dropped_from_eval": n_drop_eval,
                     "threshold": threshold, "clean_fpr": fpr})
        print(f"  {sname:<10} n_eval={int(m.sum()):<5} "
              f"dropped={n_drop_eval:<4} clean_FPR={fpr:.4f}")

    stage5 = cal["eval_clean_fpr"]
    got_all = rows[0]["clean_fpr"]
    print(f"\n  consistency check vs stage 5: {got_all:.4f} vs "
          f"{stage5:.4f}  ->  "
          f"{'MATCH' if abs(got_all - stage5) < 1e-9 else 'MISMATCH'}")

    # ---- calibration sensitivity
    print("\n=== CALIBRATION SENSITIVITY ===")
    calib_aug = int(is_aug[calib_idx].sum())
    calib_leak = int(is_leak[calib_idx].sum())
    calib_bad = is_aug[calib_idx] | is_leak[calib_idx]
    print(f"  of the {d5.CALIB_SIZE} calibration images: "
          f"{calib_aug} augmented, {calib_leak} duplicated, "
          f"{int(calib_bad.sum())} affected in total")

    for label, sel in (("original (all 400)", np.ones(d5.CALIB_SIZE, bool)),
                       ("clean calibration set", ~calib_bad)):
        cs = clean_scores[calib_idx][sel]
        thr, cfpr = d5.quantile_threshold(cs, d5.TARGET_MAX_FPR)
        mthr, mfpr = d5.quantile_threshold(cs, d5.MARGIN_MAX_FPR)
        ev_all = clean_scores[eval_idx]
        ev_clean = clean_scores[eval_idx][~(is_aug | is_leak)[eval_idx]]
        rows.append({"analysis": "recalibrated", "scenario": label,
                     "n_calib": int(sel.sum()), "threshold": thr,
                     "calib_fpr": cfpr,
                     "clean_fpr": float((ev_all >= thr).mean()),
                     "eval_fpr_clean_subset": float((ev_clean >= thr).mean()),
                     "margin_threshold": mthr, "margin_calib_fpr": mfpr})
        print(f"  {label:<24} n={int(sel.sum()):<4} thr={thr:.6f}  "
              f"calib_FPR={cfpr:.4f}  eval_FPR(all)={float((ev_all >= thr).mean()):.4f}  "
              f"eval_FPR(clean)={float((ev_clean >= thr).mean()):.4f}")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    print("\nsaved:", OUT_CSV)


if __name__ == "__main__":
    main()
