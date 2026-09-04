"""Definitive pixel-level train/test duplicate scan for meningioma.

WHY THIS EXISTS: check_aug_leakage.py used 64-bit perceptual hashes and
reported that 93.9% of real test images were "near-identical" to a training
image. verify_duplicates.py checked those hits against the pixels and found
most were FALSE ALARMS - mean MAE about 14-21 grey levels, not duplicates.
A 64-bit hash is too coarse for this data: every slice is a bright ellipse
on black, so unrelated slices collide. The hash result must not be reported
as a leakage rate.

But the same verification found genuine exact duplicates (MAE 0.000,
100% of pixels equal) among the sampled pairs, so the leakage is real and
needs measuring properly.

METHOD: every Training and Testing meningioma image is downsampled once to
64x64 greyscale and z-normalised per image (so JPEG requantisation and
global brightness shifts do not matter). Full pairwise mean-absolute-
difference is computed in chunks; for each test image the closest training
image is kept. Candidates below the duplicate threshold are then re-checked
at FULL resolution to confirm.

  MAE_64 < 0.02 (on z-normalised images)  -> candidate duplicate
  confirmed if full-resolution exact-pixel fraction >= 0.99

Because normalisation is applied, this also catches re-encoded or
rescaled copies, which byte-level hashing would miss.

Read-only. Writes results/pixel_leakage_scan.csv.
"""
import numpy as np
import pandas as pd
from PIL import Image

import common

OUT_CSV = common.RESULTS_DIR / "pixel_leakage_scan.csv"
SMALL = 64
CAND_MAE = 0.02
CONFIRM_FRAC = 0.99
CHUNK = 64


def load_small(paths):
    out = np.empty((len(paths), SMALL * SMALL), dtype=np.float32)
    for i, p in enumerate(paths):
        with Image.open(p) as im:
            a = np.asarray(im.convert("L").resize((SMALL, SMALL),
                                                  Image.LANCZOS),
                           dtype=np.float32)
        a = a.reshape(-1)
        sd = a.std()
        out[i] = (a - a.mean()) / (sd if sd > 1e-6 else 1.0)
    return out


def full_res_equal(p_test, p_train):
    with Image.open(p_test) as a, Image.open(p_train) as b:
        ga = np.asarray(a.convert("L"), dtype=np.int16)
        gb = np.asarray(b.convert("L").resize(a.size, Image.LANCZOS),
                        dtype=np.int16)
    diff = np.abs(ga - gb)
    return float((diff == 0).mean()), float(diff.mean())


def main():
    root = common.DATA_ROOT
    tr = sorted((root / "Training" / "meningioma").glob("*.jpg"))
    te = sorted((root / "Testing" / "meningioma").glob("*.jpg"))
    print(f"Training {len(tr)}   Testing {len(te)}   downsampling to "
          f"{SMALL}x{SMALL} and z-normalising ...")
    TR = load_small(tr)
    TE = load_small(te)

    print("pairwise scan ...")
    best_mae = np.full(len(te), np.inf, dtype=np.float32)
    best_j = np.zeros(len(te), dtype=np.int32)
    for s in range(0, len(te), CHUNK):
        block = TE[s:s + CHUNK]                       # (b, D)
        d = np.abs(block[:, None, :] - TR[None, :, :]).mean(axis=2)
        j = d.argmin(axis=1)
        m = d[np.arange(d.shape[0]), j]
        upd = m < best_mae[s:s + CHUNK]
        best_mae[s:s + CHUNK] = np.where(upd, m, best_mae[s:s + CHUNK])
        best_j[s:s + CHUNK] = np.where(upd, j, best_j[s:s + CHUNK])

    rows = []
    for i, p in enumerate(te):
        j = int(best_j[i])
        rec = {"test_file": p.name,
               "test_is_aug": "aug" in p.name.lower(),
               "closest_train": tr[j].name,
               "mae64_normalised": float(best_mae[i]),
               "candidate": bool(best_mae[i] < CAND_MAE)}
        if rec["candidate"]:
            frac, mae = full_res_equal(p, tr[j])
            rec["fullres_exact_frac"] = frac
            rec["fullres_mae"] = mae
            rec["confirmed_duplicate"] = frac >= CONFIRM_FRAC
        else:
            rec["fullres_exact_frac"] = np.nan
            rec["fullres_mae"] = np.nan
            rec["confirmed_duplicate"] = False
        rows.append(rec)

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print("\n================ PIXEL-LEVEL VERDICT ================")
    for label, sub in (("Te-aug-me (augmented)", df[df.test_is_aug]),
                       ("Te-me (real)", df[~df.test_is_aug]),
                       ("ALL meningioma test", df)):
        n = len(sub)
        c = int(sub.confirmed_duplicate.sum())
        cand = int(sub.candidate.sum())
        print(f"  {label:<24} n={n:<4} candidates={cand:<4} "
              f"CONFIRMED duplicates={c:<4} ({c/n:.1%})")

    print("\n  normalised-MAE percentiles (lower = more similar):")
    for label, sub in (("aug ", df[df.test_is_aug]),
                       ("real", df[~df.test_is_aug])):
        q = np.percentile(sub.mae64_normalised, [0, 5, 25, 50, 75])
        print(f"    {label}: {q[0]:.4f} {q[1]:.4f} {q[2]:.4f} {q[3]:.4f} "
              f"{q[4]:.4f}")

    conf = df[df.confirmed_duplicate]
    if len(conf):
        print(f"\n=== confirmed duplicate pairs (showing up to 15 of "
              f"{len(conf)}) ===")
        print(conf.nsmallest(15, "mae64_normalised")[
            ["test_file", "test_is_aug", "closest_train",
             "mae64_normalised", "fullres_exact_frac"]].round(4)
            .to_string(index=False))
    print("\nsaved:", OUT_CSV)


if __name__ == "__main__":
    main()
