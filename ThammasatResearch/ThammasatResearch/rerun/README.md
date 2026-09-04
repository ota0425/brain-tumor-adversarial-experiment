# Rerun pipeline — student run guide

This script set replaces all three original notebooks. Every number in
the paper (`papers/adversarial-mri-detection/`) comes from running it.
Ground rules:

- **Every run is designed to be reproducible and auditable.**
- Every stage verifies the **SHA-256 of each model against
  `results/manifest.json`** before doing any work — if a model file has
  been touched, the stage errors out immediately. This is deliberate:
  a silently retrained model is exactly the bug that invalidated the
  original results.
- Training scripts **refuse to overwrite an existing model** — you must
  pass `--force` yourself, understanding that every downstream result
  becomes invalid.

## Environment

```bash
# Python 3.12 + TF 2.20 (on the GPU machine this lives in WSL2)
python3 -m venv ~/venvs/tf220
~/venvs/tf220/bin/pip install "tensorflow[and-cuda]==2.20.*" scikit-learn pandas matplotlib pillow
```

- Working directory: `~/ThammasatResearch/` (override with the
  `TR_BASE` env var)
- Place the dataset at `~/ThammasatResearch/dataset/archive.zip` —
  its sha256 must be `8828172500…fdb4` (the scripts verify this for
  you)
- Recommended: `export CUDA_VISIBLE_DEVICES=0` and
  `export TF_FORCE_GPU_ALLOW_GROWTH=true`

## Run order (main pipeline — in this folder)

| # | File | What it does | Time on an RTX 3070 |
|---|---|---|---|
| 0 | `common.py` | Shared helpers: seeding/determinism, dataset guard, manifest, FGSM (not run directly) | — |
| 1 | `01_train_classifier.py` | Train the MobileNetV2 classifier (seed 42, deterministic) and record its hash/accuracy in the manifest | ~2.5 min |
| 2 | `02_fgsm_sweep.py` | FGSM sweep, ε 0–8, on the test set | ~1.5 min |
| 3 | `03_detector_v2.py` | Train the consistency detector (baseline, calibrated on the full validation set) | ~5 min |
| 4 | `04_final_test_v2.py` | Final test of detector v2 | ~1.5 min |
| 5 | `03b_detector_v2_calibrated.py` | Train detector v2b: val_A (model selection) / val_B (threshold) split | ~5 min |
| 6 | `04b_final_test_v2b.py` | Final test of v2b — demonstrates the FPR transfer failure | ~1.5 min |
| 7 | `05_deployment_calibration.py` | Deployment calibration: Testing → 400 calib / 1,200 eval, threshold from clean images only | ~2.5 min |
| 8 | `06_pgd_eval.py` | PGD (K=10/40) against the detector at the pinned threshold | ~20 min |
| 9 | `06b_intersection_analysis.py` | FGSM/PGD comparison on the intersection of success sets; persists per-image scores to `attack_scores.npz` | ~20 min |
| — | `make_figures.py` (in `papers/…/exp1/`) | Generates the paper's Fig 2–3 from the CSVs | seconds |

Run them in order:
```bash
cd ~/ThammasatResearch/scripts/rerun
~/venvs/tf220/bin/python 01_train_classifier.py
```
(then each subsequent file the same way)

## Audit scripts (dataset integrity)

⚠️ **These are not standalone**: they must run from inside this folder
(they import the stage modules via `import_module("03_detector_v2")`
etc.), and several require artifacts in `results/` produced by earlier
stages (`attack_scores.npz`, `clean_scores.npz`,
`text_banner_scan.csv`, `pixel_leakage_scan.csv`, `manifest.json`) —
they assert immediately if anything is missing (intentional,
fail-closed).

| File | What it does |
|---|---|
| `scan_text_banners.py` | Scans all 7,200 images for burned-in banners/text → found the glioma collection shift (1.2% vs 13.3%) |
| `check_aug_leakage.py` | ⚠️ **This file's results were REFUTED — never trust its numbers**: 64-bit perceptual hashes false-alarm catastrophically on MRI slices (it reported 93.9% near-identical, which is wrong). Kept unmodified as an audit-trail lesson; real duplication numbers come from `pixel_leakage_scan.py` only |
| `pixel_leakage_scan.py` | The correct duplication detector (pixel-level) → found 100/400 meningioma test images duplicated from Training |
| `verify_duplicates.py` | Confirms candidate duplicate pairs at full resolution |
| `exclusion_and_shortcut.py` | Detection rates under exclusions + the shortcut check (glioma collapses on banner images: 15.1%) |
| `clean_fpr_exclusion.py` | Clean FPR under exclusions + calibration sensitivity |
| `make_example_figure.py` | Generates Fig 1 (per-class MRI examples, exemplars screened to be clean) |
| `diag_score_shift.py` | Diagnostic of the clean-score distribution shift (validation vs test) |

## Expected checkpoint numbers (verify against the paper)

- Clean test accuracy **0.81875 (1,310/1,600)** — if you get anything
  else, your environment differs; stop and investigate rather than
  pushing on.
- Stage 7: threshold 0.3612, eval FPR **0.0983**
- Stages 8–9: PGD detection within ~1 point of FGSM on the intersection

Full provenance: `papers/adversarial-mri-detection/exp1/PROVENANCE.md`
and `papers/adversarial-mri-detection/review-synthesis.md`
