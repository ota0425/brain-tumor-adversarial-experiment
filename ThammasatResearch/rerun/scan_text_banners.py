"""Read-only scan for burned-in text / branding banners in the dataset.

Motivated by the Medscape watermark found in a notumor exemplar while
building the qualitative figure. Two questions:
  1. which images carry burned-in branding (so figures can avoid them)
  2. does prevalence differ between Training/ and Testing/ — if it does,
     that is direct, visible evidence for the collection-shift finding
     from stages 4/4b, not just a statistical inference

HEURISTIC (documented because it is a heuristic, not a text detector):

  Signal A - COLOUR. A genuine MRI slice is greyscale, so R=G=B for real
  image content. Any pixel with channel spread max(RGB)-min(RGB) > 30 is
  something that was composited on top: coloured logos, coloured text,
  coloured rules. We record the fraction of such pixels. This is the
  strong signal - real anatomy cannot produce it.

  Signal B - BRIGHT BORDER RUNS. White-on-black captions are greyscale and
  invisible to signal A, so we also look at the top and bottom 15% of rows
  and measure the fraction of near-white pixels (>= 200 on all channels)
  there. Anatomy does reach the border in some slices, so this signal is
  noisier and is reported separately rather than merged.

  An image is FLAGGED if colour_frac >= 0.0005 (0.05% of pixels, i.e. a
  few hundred coloured pixels in a typical slice) OR border_bright_frac
  >= 0.02 in either band. Thresholds are deliberately loose; the CSV keeps
  the raw numbers so they can be re-thresholded without re-running.

Writes results/text_banner_scan.csv and prints a summary. Reads nothing
but the extracted image files; changes no experiment artefact.
"""
import os
from collections import defaultdict

import numpy as np
import pandas as pd
from PIL import Image

import common

COLOUR_SPREAD = 30       # channel spread above this = composited colour
COLOUR_FRAC_FLAG = 0.0005
BRIGHT_LEVEL = 200
BRIGHT_FRAC_FLAG = 0.02
BAND = 0.15              # top/bottom fraction of rows treated as border
OUT_CSV = common.RESULTS_DIR / "text_banner_scan.csv"


def scan_image(path):
    with Image.open(path) as im:
        arr = np.asarray(im.convert("RGB"), dtype=np.int16)
    h = arr.shape[0]
    spread = arr.max(axis=2) - arr.min(axis=2)
    colour_frac = float((spread > COLOUR_SPREAD).mean())

    band = max(1, int(round(h * BAND)))
    bright = (arr >= BRIGHT_LEVEL).all(axis=2)
    top_frac = float(bright[:band].mean())
    bot_frac = float(bright[-band:].mean())

    # where the colour lives, if any - helps tell a banner from stray noise
    if colour_frac > 0:
        rows = np.flatnonzero((spread > COLOUR_SPREAD).any(axis=1))
        colour_in_band = bool(
            (rows < band).any() or (rows >= h - band).any())
    else:
        colour_in_band = False

    return {
        "colour_frac": colour_frac,
        "top_bright_frac": top_frac,
        "bottom_bright_frac": bot_frac,
        "colour_in_border_band": colour_in_band,
        "height": h,
        "width": arr.shape[1],
    }


def main():
    root = common.DATA_ROOT
    assert root.exists(), f"extracted dataset not found at {root}"
    rows = []
    for split in ("Training", "Testing"):
        split_dir = root / split
        for cls in sorted(p.name for p in split_dir.iterdir() if p.is_dir()):
            files = sorted((split_dir / cls).iterdir())
            for i, f in enumerate(files):
                if f.suffix.lower() not in {".jpg", ".jpeg", ".png", ".bmp"}:
                    continue
                rec = scan_image(f)
                rec.update({"split": split, "class": cls, "file": f.name,
                            "index_in_class": i})
                rec["flagged"] = bool(
                    rec["colour_frac"] >= COLOUR_FRAC_FLAG
                    or rec["top_bright_frac"] >= BRIGHT_FRAC_FLAG
                    or rec["bottom_bright_frac"] >= BRIGHT_FRAC_FLAG)
                rows.append(rec)
            print(f"  scanned {split}/{cls}: {len(files)} files")

    df = pd.DataFrame(rows)
    df.to_csv(OUT_CSV, index=False)

    print(f"\ntotal images scanned: {len(df)}")
    print(f"flagged (any signal): {int(df.flagged.sum())} "
          f"({df.flagged.mean():.2%})")

    print("\n=== FLAGGED COUNT BY SPLIT x CLASS ===")
    tab = df.pivot_table(index="class", columns="split", values="flagged",
                         aggfunc=["sum", "count"])
    print(tab.to_string())

    print("\n=== RATE BY SPLIT (the collection-shift question) ===")
    for split in ("Training", "Testing"):
        d = df[df.split == split]
        print(f"  {split:<9} n={len(d):<5} flagged={int(d.flagged.sum()):<5} "
              f"({d.flagged.mean():.2%})   "
              f"colour-signal only: {int((d.colour_frac >= COLOUR_FRAC_FLAG).sum())} "
              f"({(d.colour_frac >= COLOUR_FRAC_FLAG).mean():.2%})")

    print("\n=== COLOUR SIGNAL BY SPLIT x CLASS (strongest evidence) ===")
    df["colour_flag"] = df.colour_frac >= COLOUR_FRAC_FLAG
    print(df.pivot_table(index="class", columns="split", values="colour_flag",
                         aggfunc="mean").round(4).to_string())

    print("\n=== EXAMPLES: strongest colour signal ===")
    top = df.nlargest(8, "colour_frac")[
        ["split", "class", "file", "colour_frac", "colour_in_border_band"]]
    print(top.round(5).to_string(index=False))

    print("\n=== CLEANEST notumor CANDIDATES IN Testing (for the figure) ===")
    cand = df[(df.split == "Testing") & (df["class"] == "notumor")
              & ~df.flagged].nsmallest(
        6, ["colour_frac"])[["file", "index_in_class", "colour_frac",
                             "top_bright_frac", "bottom_bright_frac"]]
    print(cand.round(5).to_string(index=False))
    print("\nsaved:", OUT_CSV)


if __name__ == "__main__":
    main()
