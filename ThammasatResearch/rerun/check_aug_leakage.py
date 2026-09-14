"""Near-duplicate check: are Testing images augmentations of Training images?

The meningioma class is padded with files named *aug* in BOTH splits
(Tr-aug-me 100, Te-aug-me 103). If the Testing augmentations derive from
images that also appear in Training, the test set is contaminated and every
accuracy number in the study is optimistic. This script measures that.

METHOD (documented because thresholds are judgement calls):

  Two independent 64-bit hashes per image, both on a greyscale copy:
    dHash - 9x8 resize, bit i = (pixel[i] > pixel[i+1]) along rows.
            Sensitive to local gradient structure.
    pHash - 32x32 resize, 2-D DCT, keep the top-left 8x8 block excluding
            the DC term, bit = (coefficient > median). Robust to scale and
            mild intensity changes.

  CRITICAL: plain perceptual hashing is NOT invariant to rotation or
  reflection, and augmentation pipelines routinely use both. So every
  TRAINING image is hashed under all 8 dihedral transforms (identity, 3
  rotations, and those 4 mirrored). A Testing image is matched against
  that expanded set, so a flip/rotate augmentation still matches its
  source. Without this the check would report a clean bill of health for
  exactly the augmentations we are worried about.

  Hamming distance on 64 bits. Reported bands:
    <= 4   near-identical (same image, at most requantised)
    <= 10  near-duplicate (standard threshold for "same content")
    > 10   distinct

Comparisons run: Te-aug-me vs all Training meningioma; Te-me vs all
Training meningioma (the control - real test images should NOT match);
and the reverse direction Tr-aug-me vs all Testing meningioma.

Read-only. Writes results/aug_leakage_check.csv only.
"""
import numpy as np
import pandas as pd
from PIL import Image
from scipy.fftpack import dct

import common

OUT_CSV = common.RESULTS_DIR / "aug_leakage_check.csv"
NEAR_IDENTICAL = 4
NEAR_DUPLICATE = 10


def _gray(path, size):
    with Image.open(path) as im:
        return np.asarray(im.convert("L").resize(size, Image.LANCZOS),
                          dtype=np.float64)


def dhash(path):
    a = _gray(path, (9, 8))
    bits = (a[:, :-1] > a[:, 1:]).flatten()
    return np.packbits(bits).view(">u8")[0]


def phash(path):
    a = _gray(path, (32, 32))
    d = dct(dct(a, axis=0, norm="ortho"), axis=1, norm="ortho")[:8, :8]
    flat = d.flatten()[1:]           # drop DC
    bits = flat > np.median(flat)
    bits = np.append(bits, False)    # pad back to 64
    return np.packbits(bits).view(">u8")[0]


def dihedral_hashes(path):
    """All 8 dihedral variants, for both hash types."""
    with Image.open(path) as im:
        g = im.convert("L")
        variants = []
        for mirror in (False, True):
            base = g.transpose(Image.FLIP_LEFT_RIGHT) if mirror else g
            for k in range(4):
                variants.append(base.rotate(90 * k, expand=True))
    dh, ph = [], []
    for v in variants:
        a = np.asarray(v.resize((9, 8), Image.LANCZOS), dtype=np.float64)
        dh.append(np.packbits((a[:, :-1] > a[:, 1:]).flatten()).view(">u8")[0])
        b = np.asarray(v.resize((32, 32), Image.LANCZOS), dtype=np.float64)
        d = dct(dct(b, axis=0, norm="ortho"), axis=1, norm="ortho")[:8, :8]
        flat = d.flatten()[1:]
        bits = np.append(flat > np.median(flat), False)
        ph.append(np.packbits(bits).view(">u8")[0])
    return np.array(dh, dtype=np.uint64), np.array(ph, dtype=np.uint64)


def hamming(a, b):
    return np.bitwise_count(np.bitwise_xor(a, b)).astype(np.int16)


def main():
    root = common.DATA_ROOT
    tr = sorted((root / "Training" / "meningioma").glob("*.jpg"))
    te = sorted((root / "Testing" / "meningioma").glob("*.jpg"))
    print(f"Training meningioma: {len(tr)}   Testing meningioma: {len(te)}")

    print("hashing training set under 8 dihedral transforms ...")
    tr_d, tr_p, tr_names = [], [], []
    for p in tr:
        d8, p8 = dihedral_hashes(p)
        tr_d.append(d8)
        tr_p.append(p8)
        tr_names.append(p.name)
    tr_d = np.stack(tr_d)          # (n_train, 8)
    tr_p = np.stack(tr_p)
    print(f"  {tr_d.shape[0]} training images x 8 variants")

    print("hashing testing set ...")
    rows = []
    for p in te:
        d = np.uint64(dhash(p))
        h = np.uint64(phash(p))
        dd = hamming(tr_d, d)      # (n_train, 8)
        dp = hamming(tr_p, h)
        best_d = dd.min()
        best_p = dp.min()
        i_d = np.unravel_index(dd.argmin(), dd.shape)
        i_p = np.unravel_index(dp.argmin(), dp.shape)
        combined = min(int(best_d), int(best_p))
        rows.append({
            "test_file": p.name,
            "test_is_aug": "aug" in p.name.lower(),
            "best_dhash_distance": int(best_d),
            "best_dhash_match": tr_names[i_d[0]],
            "best_dhash_transform": int(i_d[1]),
            "best_phash_distance": int(best_p),
            "best_phash_match": tr_names[i_p[0]],
            "best_phash_transform": int(i_p[1]),
            "min_distance": combined,
            "near_identical": combined <= NEAR_IDENTICAL,
            "near_duplicate": combined <= NEAR_DUPLICATE,
        })
    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print("\n================ VERDICT ================")
    for label, sub in (("Te-aug-me (augmented test)", df[df.test_is_aug]),
                       ("Te-me (real test, control)", df[~df.test_is_aug])):
        n = len(sub)
        ni = int(sub.near_identical.sum())
        nd = int(sub.near_duplicate.sum())
        print(f"\n{label}: n={n}")
        print(f"  near-identical (<= {NEAR_IDENTICAL}): {ni} ({ni/n:.1%})")
        print(f"  near-duplicate (<= {NEAR_DUPLICATE}): {nd} ({nd/n:.1%})")
        q = np.percentile(sub.min_distance, [0, 5, 25, 50, 75, 100])
        print(f"  min-distance percentiles 0/5/25/50/75/100: "
              f"{q[0]:.0f} {q[1]:.0f} {q[2]:.0f} {q[3]:.0f} {q[4]:.0f} {q[5]:.0f}")

    print("\n=== closest pairs overall ===")
    print(df.nsmallest(10, "min_distance")[
        ["test_file", "test_is_aug", "min_distance", "best_dhash_match",
         "best_dhash_transform", "best_phash_match"]].to_string(index=False))
    print("\nsaved:", OUT_CSV)


if __name__ == "__main__":
    main()
