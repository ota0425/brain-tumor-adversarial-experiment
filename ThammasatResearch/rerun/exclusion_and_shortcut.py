"""Shortcut check + exclusion-robustness recomputation. No GPU needed.

Two analyses over the persisted artefacts:

1. SHORTCUT CHECK. Banner-flagged images are heavily concentrated in the
   notumor class (~61%) and notumor is the classifier's best class. If the
   model is partly reading burned-in banners rather than anatomy, flagged
   images should be classified correctly more often than unflagged ones
   within the same class. Measured per class.

2. EXCLUSION ROBUSTNESS. Headline numbers recomputed with contaminated
   subsets removed. Two exclusions:
     - no_aug:    drop the 103 synthetic Te-aug-me images (as requested)
     - no_leak:   drop the meningioma test images confirmed by
                  pixel_leakage_scan.py to be pixel-identical duplicates of
                  training images. This one matters more: the augmented
                  images turned out to be clean, while 100 REAL test images
                  are verbatim copies of training data.
     - no_either: both removed

INDEX MAPPING is verified, not assumed: attack_scores.npz rows are in the
order produced by image_dataset_from_directory(shuffle=False), which is
test_ds.file_paths. The script re-derives file_paths and asserts the length
and the per-class counts line up before using any of it.

Read-only. Writes results/exclusion_no_aug.csv and
results/shortcut_check.csv.
"""
import json
import os
from importlib import import_module

import numpy as np
import pandas as pd

import common

d5 = import_module("05_deployment_calibration")

SCORES = common.RESULTS_DIR / "attack_scores.npz"
OUT_EXCL = common.RESULTS_DIR / "exclusion_no_aug.csv"
OUT_SHORT = common.RESULTS_DIR / "shortcut_check.csv"


def main():
    # ---- rebuild the filename order and VERIFY the mapping
    _, _, test_ds, class_names = common.make_datasets()
    file_paths = list(test_ds.file_paths)
    names = np.array([os.path.basename(p) for p in file_paths])
    labels = np.array([class_names.index(os.path.basename(os.path.dirname(p)))
                       for p in file_paths])
    assert len(names) == 1600, len(names)

    z = np.load(SCORES)
    clean_correct = z["clean_correct"]
    eval_idx = z["eval_idx"]
    assert clean_correct.shape[0] == 1600, clean_correct.shape
    # independent cross-check: per-class accuracy must reproduce the manifest
    manifest = common.load_manifest()
    acc = clean_correct.mean()
    assert abs(acc - manifest["clean_test_accuracy"]) < 1e-9, (
        f"index mapping suspect: npz accuracy {acc} vs manifest "
        f"{manifest['clean_test_accuracy']}")
    print(f"index mapping verified: npz clean accuracy {acc:.6f} == manifest")

    scan = pd.read_csv(common.RESULTS_DIR / "text_banner_scan.csv")
    scan_te = scan[scan.split == "Testing"].set_index("file")
    flagged = np.array([bool(scan_te.loc[n, "flagged"]) for n in names])

    # ---- 1. shortcut check
    print("\n=== SHORTCUT CHECK: accuracy on banner-flagged vs unflagged ===")
    rows = []
    for ci, cname in enumerate(class_names):
        m = labels == ci
        for tag, sel in (("flagged", m & flagged), ("unflagged", m & ~flagged)):
            n = int(sel.sum())
            a = float(clean_correct[sel].mean()) if n else np.nan
            rows.append({"class": cname, "group": tag, "n": n, "accuracy": a})
    sc = pd.DataFrame(rows)
    piv = sc.pivot(index="class", columns="group",
                   values=["n", "accuracy"])
    piv[("accuracy", "delta")] = (piv[("accuracy", "flagged")]
                                  - piv[("accuracy", "unflagged")])
    print(piv.round(4).to_string())
    sc.to_csv(OUT_SHORT, index=False)

    # ---- 2. exclusion robustness
    leak = pd.read_csv(common.RESULTS_DIR / "pixel_leakage_scan.csv")
    leaked_names = set(leak[leak.confirmed_duplicate].test_file)
    is_aug = np.array(["aug" in n.lower() for n in names])
    is_leak = np.array([n in leaked_names for n in names])
    print(f"\nexclusion sets: aug={int(is_aug.sum())} "
          f"leaked={int(is_leak.sum())} "
          f"either={int((is_aug | is_leak).sum())}")

    cal = json.loads(d5.THRESHOLD_PATH.read_text(encoding="utf-8"))
    threshold = cal["threshold"]
    eval_mask = np.zeros(1600, dtype=bool)
    eval_mask[eval_idx] = True

    scenarios = {
        "all": np.ones(1600, dtype=bool),
        "no_aug": ~is_aug,
        "no_leak": ~is_leak,
        "no_either": ~(is_aug | is_leak),
    }

    out = []
    for sname, keep in scenarios.items():
        acc = float(clean_correct[keep].mean())
        ev = eval_mask & keep
        # NOTE: clean detector scores are not in the npz (only per-attack
        # scores and success masks), so clean FPR cannot be recomputed under
        # exclusion here without a GPU pass. Reported below is the detection
        # side only; the clean FPR stays as measured in stage 5.
        base = {"scenario": sname,
                "n_images": int(keep.sum()),
                "clean_accuracy": acc,
                "n_eval": int(ev.sum())}
        for eps in common.ALL_EPSILONS:
            f_s = z[f"fgsm_success_eps{eps}"]
            p_s = z[f"pgd40_success_eps{eps}"]
            f_sc = z[f"fgsm_scores_eps{eps}"]
            p_sc = z[f"pgd40_scores_eps{eps}"]
            inter = f_s & p_s & ev
            row = dict(base)
            row.update({
                "epsilon": eps,
                "n_intersection": int(inter.sum()),
                "det_fgsm_intersection":
                    float((f_sc[inter] >= threshold).mean())
                    if inter.any() else np.nan,
                "det_pgd40_intersection":
                    float((p_sc[inter] >= threshold).mean())
                    if inter.any() else np.nan,
                "threshold": threshold,
            })
            out.append(row)

    df = pd.DataFrame(out)
    df.to_csv(OUT_EXCL, index=False)
    print("\n=== EXCLUSION ROBUSTNESS (detection on the FGSM/PGD "
          "intersection, eval subset) ===")
    print(df[["scenario", "n_images", "clean_accuracy", "epsilon",
              "n_intersection", "det_fgsm_intersection",
              "det_pgd40_intersection"]].round(4).to_string(index=False))

    print("\n=== CLEAN ACCURACY BY SCENARIO ===")
    for sname, keep in scenarios.items():
        print(f"  {sname:<10} n={int(keep.sum()):<5} "
              f"accuracy={float(clean_correct[keep].mean()):.4f}")
    print("\n  per-class accuracy, all vs no_leak:")
    for ci, cname in enumerate(class_names):
        m = labels == ci
        a_all = float(clean_correct[m].mean())
        m2 = m & ~is_leak
        a_nl = float(clean_correct[m2].mean())
        print(f"    {cname:<11} all={a_all:.4f} (n={int(m.sum())})   "
              f"no_leak={a_nl:.4f} (n={int(m2.sum())})   "
              f"delta={a_nl - a_all:+.4f}")
    print("\nsaved:", OUT_EXCL, "and", OUT_SHORT)


if __name__ == "__main__":
    main()
