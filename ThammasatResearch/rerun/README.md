# Rerun pipeline — student run guide

This script set replaces the three exploratory notebooks as the source of the
final reported results. The current manuscript source is in
`papers/adversarial-mri-detection-colab-rerun/`; the published, fixed snapshot
of code, models, and results is at https://doi.org/10.5281/zenodo.22682676.
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

The reported rerun used Google Colab, an NVIDIA Tesla T4 GPU, Python 3.13.15,
TensorFlow 2.20.0, and seed 42. Open the repository's `rerun_colab.ipynb` in
Colab for the recorded stage order. The local setup below is an alternative,
not the environment used for the final reported run.

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
| 10 | `diag_score_shift.py` | Save validation/test clean-score quantiles and FPR transfer diagnostics to `clean_score_distribution_shift.csv` | ~1 min |
| 11 | `scan_text_banners.py` | Recreate the dataset-intrinsic banner/text scan | minutes |
| 12 | `pixel_leakage_scan.py` | Recreate the definitive pixel-level duplicate scan | minutes |
| 13 | `exclusion_and_shortcut.py` | Recompute banner-group accuracy and exclusion results from the final persisted predictions | seconds |
| 14 | `clean_fpr_exclusion.py` | Recompute clean FPR after dataset-defect exclusions with the final models | minutes |
| 15 | `make_example_figure.py` | Regenerate Figure 1 from the final classifier and attacks at 300-DPI raster resolution inside PDF | minutes |
| — | `make_figures.py` (in `papers/…/exp1/`) | Generates the paper's Fig 2–3 from the CSVs | seconds |

Run them in order:
```bash
cd ~/ThammasatResearch/rerun
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
| `diag_score_shift.py` | Main Stage 10; persists the clean-score distribution shift (validation vs test) for the paper table |

## Expected checkpoint numbers (verify against the paper)

- Clean test accuracy **0.819375 (1,311/1,600)**. Verify the classifier
  checkpoint against `results/manifest.json` before using downstream outputs.
- Stage 7: threshold approximately **0.320683**, evaluation FPR **0.1075**.
- Stages 8–9: on shared successful images, PGD-10 and PGD-40 detection rates
  are within two percentage points of FGSM at the same threshold.

Full provenance: the published archive's `results/PROVENANCE.md` and
`results/manifest.json`. Earlier 0.81875 / 0.0983 checkpoints belong to a
different run and must not be mixed with the final model artifacts.
