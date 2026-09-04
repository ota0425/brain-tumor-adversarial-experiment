"""Qualitative example panels for the paper: Original / Perturbation / Adversarial.

Regenerates the figure from the CURRENT classifier (classifier_seed42.keras,
hash-checked against the manifest). The student's older PNGs came from a
pre-2026-09-01 model that has since been replaced, so they must not appear
in the paper alongside these results.

Two attacks, both at epsilon = 0.5 on the 0-255 input scale:
  fgsm    - single signed step
  pgd40   - 40 steps, alpha = eps/4, random start

Two row-selection variants, both deterministic (test_ds has shuffle=False):
  firstN   - first 3 initially-correct images of the first test batch,
             exactly as specified. On this dataset all three land in the
             same class (glioma), because Testing/ is ordered by class.
  perclass - the first initially-correct image of EACH of the 4 classes,
             scanning the test set in order. Better for a paper panel.

Perturbation column is displayed as (delta + eps) / (2 * eps) clipped to
[0, 1]; mid-grey means no change. It is rendered in colour because the
sign is per-channel, even though the underlying MRI is greyscale.

Outputs PNG at 300 dpi and PDF, sized for a single LNCS column.
"""
import json
import os
from importlib import import_module

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf

import common

d6 = import_module("06_pgd_eval")

EPSILON = 0.5
FIG_DIR = common.RESULTS_DIR / "figures"
LNCS_COL_INCHES = 4.8


def build_panel(title, originals, advs, class_names, meta, out_stem):
    n = len(originals)
    fig, axes = plt.subplots(
        n, 3, figsize=(LNCS_COL_INCHES, LNCS_COL_INCHES / 3.0 * n * 1.34))
    axes = np.atleast_2d(axes)
    for r in range(n):
        orig, adv = originals[r], advs[r]
        delta = adv - orig
        pert = np.clip((delta + EPSILON) / (2.0 * EPSILON), 0.0, 1.0)

        axes[r, 0].imshow(np.clip(orig / 255.0, 0, 1))
        axes[r, 0].set_title(
            f"true: {class_names[meta[r]['true']]}\n"
            f"pred: {class_names[meta[r]['clean_pred']]}", fontsize=6, pad=3)
        axes[r, 1].imshow(pert)
        axes[r, 1].set_title(
            rf"perturbation $\times$ display scale" "\n"
            rf"($\epsilon$={EPSILON:g})", fontsize=6, pad=3)
        flipped = meta[r]["adv_pred"] != meta[r]["true"]
        axes[r, 2].imshow(np.clip(adv / 255.0, 0, 1))
        axes[r, 2].set_title(
            f"adversarial\npred: {class_names[meta[r]['adv_pred']]}"
            f"{' (flipped)' if flipped else ' (unchanged)'}",
            fontsize=6, pad=3, color="crimson" if flipped else "black")
        for c in range(3):
            axes[r, c].set_xticks([])
            axes[r, c].set_yticks([])
    fig.suptitle(title, fontsize=8)
    fig.subplots_adjust(top=0.93, hspace=0.42, wspace=0.05)
    png = FIG_DIR / f"{out_stem}.png"
    pdf = FIG_DIR / f"{out_stem}.pdf"
    fig.savefig(png, dpi=300, bbox_inches="tight")
    fig.savefig(pdf, bbox_inches="tight")
    plt.close(fig)
    return png, pdf


def main():
    common.set_determinism()
    _, _, test_ds, class_names = common.make_datasets()

    manifest = common.load_manifest()
    actual = common.sha256_of(common.CLASSIFIER_PATH)
    assert actual == manifest["classifier_sha256"], (
        "classifier hash does not match manifest - refusing to make figures "
        "from a model that is not the one the results came from"
    )
    print(f"classifier sha256 verified: {actual[:16]}...")
    assert list(class_names) == list(manifest["class_names"])
    classifier = tf.keras.models.load_model(common.CLASSIFIER_PATH)
    classifier.trainable = False

    # ---- selection 1: first 3 initially-correct of the first batch (spec)
    images, labels = next(iter(test_ds))
    labels_np = labels.numpy().reshape(-1)
    pred = np.argmax(classifier(images, training=False).numpy(), axis=1)
    idx = np.flatnonzero(pred == labels_np)[:3]
    assert idx.size == 3
    selections = {
        "firstN": {
            "images": tf.gather(images, idx),
            "labels": tf.gather(labels, idx),
            "clean_pred": pred[idx],
            "note": f"first batch indices {idx.tolist()}",
        }
    }

    # ---- selection 2: first initially-correct image of each class that the
    # text-banner scan does NOT flag. A Medscape watermark was found in the
    # naive first-notumor pick, so exemplars are screened for burned-in
    # branding using results/text_banner_scan.csv (scan_text_banners.py).
    import pandas as pd
    scan_csv = common.RESULTS_DIR / "text_banner_scan.csv"
    assert scan_csv.exists(), (
        "run scan_text_banners.py first - exemplars must be screened for "
        "burned-in branding before they go in the paper"
    )
    scan = pd.read_csv(scan_csv)
    clean_names = set(
        scan[(scan.split == "Testing") & (~scan.flagged)].file)
    # exclude synthetic augmentations - a paper figure should show real data
    clean_names = {n for n in clean_names if "aug" not in n.lower()}
    # exclude images confirmed to be pixel-identical copies of training data
    leak_csv = common.RESULTS_DIR / "pixel_leakage_scan.csv"
    if leak_csv.exists():
        leak = pd.read_csv(leak_csv)
        leaked = set(leak[leak.confirmed_duplicate].test_file)
        clean_names -= leaked
        print(f"excluded {len(leaked)} train/test duplicate images")
    print(f"exemplar pool: {len(clean_names)} of "
          f"{int((scan.split == 'Testing').sum())} Testing images are "
          f"unflagged, real and not leaked")

    file_paths = list(test_ds.file_paths)
    want = list(range(len(class_names)))
    picked_img, picked_lab, picked_pred, picked_note = [], [], [], []
    pos = 0
    for images_b, labels_b in test_ds:
        n_b = int(labels_b.shape[0])
        if want:
            lb = labels_b.numpy().reshape(-1)
            pb = np.argmax(classifier(images_b, training=False).numpy(),
                           axis=1)
            for cls in list(want):
                hits = np.flatnonzero((lb == cls) & (pb == cls))
                for j in hits:
                    fname = os.path.basename(file_paths[pos + int(j)])
                    if fname in clean_names:
                        picked_img.append(images_b[int(j)])
                        picked_lab.append(labels_b[int(j)])
                        picked_pred.append(cls)
                        picked_note.append(f"{class_names[cls]}:{fname}")
                        want.remove(cls)
                        break
        pos += n_b
        if not want and pos >= len(file_paths):
            break
    assert not want, want
    order = np.argsort(picked_pred)
    selections["perclass"] = {
        "images": tf.stack([picked_img[i] for i in order]),
        "labels": tf.stack([picked_lab[i] for i in order]),
        "clean_pred": np.array([picked_pred[i] for i in order]),
        "note": "one per class: " + ", ".join(picked_note[i] for i in order),
    }

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    report = {}
    for sel_name, sel in selections.items():
        sel_images, sel_labels = sel["images"], sel["labels"]
        originals = sel_images.numpy().astype(np.float32)
        _, signed = common.compute_fgsm_direction(classifier, sel_images,
                                                  sel_labels)
        advs = {
            "fgsm": common.create_adversarial_images(
                sel_images, signed, EPSILON).numpy(),
            "pgd40": d6.make_pgd_fn(
                classifier, float(EPSILON), float(EPSILON) / 4.0, 40
            )(sel_images, sel_labels).numpy(),
        }
        titles = {
            "fgsm": f"FGSM, $\\epsilon$={EPSILON:g} (0-255 scale)",
            "pgd40": f"PGD-40, $\\epsilon$={EPSILON:g}, "
                     f"$\\alpha=\\epsilon/4$ (0-255 scale)",
        }
        for tag, adv in advs.items():
            max_pert = float(np.max(np.abs(adv - originals)))
            assert max_pert <= EPSILON + 1e-4, (tag, max_pert)
            adv_pred = np.argmax(
                classifier(adv, training=False).numpy(), axis=1)
            lab = sel_labels.numpy().reshape(-1)
            meta = [{"true": int(lab[r]),
                     "clean_pred": int(sel["clean_pred"][r]),
                     "adv_pred": int(adv_pred[r])}
                    for r in range(len(originals))]
            stem = f"{tag}_examples_eps{EPSILON:g}_{sel_name}"
            png, pdf = build_panel(titles[tag], originals, adv, class_names,
                                   meta, stem)
            report[stem] = {"png": png.name, "pdf": pdf.name,
                            "selection": sel["note"], "rows": meta}
            print(f"\n{stem}  ({sel['note']})")
            for r, m in enumerate(meta):
                print(f"  row {r}: true={class_names[m['true']]:<11} "
                      f"clean={class_names[m['clean_pred']]:<11} "
                      f"adv={class_names[m['adv_pred']]:<11} "
                      f"{'FLIPPED' if m['adv_pred'] != m['true'] else 'unchanged'}")

    (FIG_DIR / "figure_provenance.json").write_text(
        json.dumps({"classifier_sha256": actual, "epsilon": EPSILON,
                    "class_names": list(class_names), "panels": report},
                   indent=2), encoding="utf-8")
    print("\nprovenance written:", FIG_DIR / "figure_provenance.json")


if __name__ == "__main__":
    main()
