"""Verify the near-duplicate hits at the PIXEL level, not by hash.

check_aug_leakage.py reported that 93.9% of the REAL meningioma test images
(Te-me, the control group that should NOT match anything) are within
Hamming distance 4 of a Training image, with a median distance of 0. That
is extraordinary enough that it must be confirmed against the pixels
before anyone acts on it: a 64-bit perceptual hash can collapse on
low-contrast images and manufacture false matches.

Three checks:
  1. HASH DEGENERACY. Count distinct dHash/pHash values among the 1400
     training images. If far below 1400, the hash is collapsing and the
     distance-0 hits are artefacts, not duplicates.
  2. PIXEL COMPARISON of the reported pairs. Load both images at native
     resolution, resize the training one to the test one's shape, and
     compute mean absolute difference and the fraction of exactly equal
     pixels. Identical files give MAE 0.
  3. FILE-LEVEL. Compare sha256 of the raw bytes and the image dimensions.

Read-only. Prints a verdict; writes results/duplicate_verification.csv.
"""
import hashlib

import numpy as np
import pandas as pd
from PIL import Image

import common

OUT_CSV = common.RESULTS_DIR / "duplicate_verification.csv"
N_PAIRS = 25


def file_sha(p):
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def pixel_compare(p_test, p_train):
    with Image.open(p_test) as a, Image.open(p_train) as b:
        ga = np.asarray(a.convert("L"), dtype=np.int16)
        gb_img = b.convert("L")
        same_size = gb_img.size == a.size
        gb = np.asarray(gb_img.resize(a.size, Image.LANCZOS), dtype=np.int16)
    diff = np.abs(ga - gb)
    return {
        "same_dimensions": bool(same_size),
        "test_shape": f"{ga.shape[1]}x{ga.shape[0]}",
        "mae": float(diff.mean()),
        "max_abs_diff": int(diff.max()),
        "frac_exact_equal": float((diff == 0).mean()),
    }


def main():
    root = common.DATA_ROOT
    tr_dir = root / "Training" / "meningioma"
    te_dir = root / "Testing" / "meningioma"

    # ---- check 1: hash degeneracy
    import importlib
    leak = importlib.import_module("check_aug_leakage")
    tr_files = sorted(tr_dir.glob("*.jpg"))
    dh = np.array([leak.dhash(p) for p in tr_files], dtype=np.uint64)
    ph = np.array([leak.phash(p) for p in tr_files], dtype=np.uint64)
    print("=== CHECK 1: hash degeneracy on 1400 training images ===")
    print(f"  distinct dHash values: {len(np.unique(dh))} / {len(dh)}")
    print(f"  distinct pHash values: {len(np.unique(ph))} / {len(ph)}")
    if len(np.unique(dh)) < len(dh) * 0.9:
        print("  WARNING: dHash is collapsing - distance-0 hits may be artefacts")
    else:
        print("  hashes are well spread; distance-0 hits are NOT hash collapse")

    # ---- check 2/3: pixel + file comparison of reported pairs
    res = pd.read_csv(common.RESULTS_DIR / "aug_leakage_check.csv")
    sample = pd.concat([
        res[res.test_is_aug].nsmallest(N_PAIRS // 2, "min_distance"),
        res[~res.test_is_aug].nsmallest(N_PAIRS - N_PAIRS // 2,
                                        "min_distance"),
    ])
    print(f"\n=== CHECK 2/3: pixel comparison of {len(sample)} reported pairs ===")
    rows = []
    for _, r in sample.iterrows():
        pt = te_dir / r.test_file
        pr = tr_dir / r.best_dhash_match
        if not pr.exists():
            continue
        rec = pixel_compare(pt, pr)
        rec.update({
            "test_file": r.test_file,
            "test_is_aug": bool(r.test_is_aug),
            "train_match": r.best_dhash_match,
            "hash_distance": int(r.min_distance),
            "identical_bytes": file_sha(pt) == file_sha(pr),
        })
        rows.append(rec)
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)
    cols = ["test_file", "test_is_aug", "train_match", "hash_distance",
            "same_dimensions", "mae", "frac_exact_equal", "identical_bytes"]
    print(df[cols].round(3).to_string(index=False))

    print("\n=== VERDICT ===")
    for label, sub in (("augmented (Te-aug-me)", df[df.test_is_aug]),
                       ("real (Te-me)", df[~df.test_is_aug])):
        if not len(sub):
            continue
        print(f"  {label}: n={len(sub)}  "
              f"byte-identical={int(sub.identical_bytes.sum())}  "
              f"mean MAE={sub.mae.mean():.2f}  "
              f"mean exact-pixel fraction={sub.frac_exact_equal.mean():.3f}")
    print("\nInterpretation guide: MAE near 0 with a high exact-pixel "
          "fraction means the same underlying image. MAE above ~15 means the "
          "hash matched structure but the pixels differ - a false alarm.")
    print("saved:", OUT_CSV)


if __name__ == "__main__":
    main()
