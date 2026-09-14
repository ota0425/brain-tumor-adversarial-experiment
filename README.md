# Adversarial Attack Detection for Brain MRI Classification

[![Open the rerun pipeline in Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/ota0425/brain-tumor-adversarial-experiment/blob/main/rerun_colab.ipynb)

This repository supports the manuscript **“Towards Trustworthy and Reliable Deployment of Adversarial Attack Detection for Brain MRI Classification”**, submitted to MICAD 2026. It studies whether an adversarial-attack detector's false-positive-rate (FPR) threshold transfers from training-side data to a distinct MRI test collection, and evaluates FGSM-to-PGD detection transfer at a fixed operating point. This is a research testbed, **not** a clinically validated system.

The [published Zenodo reproducibility package](https://doi.org/10.5281/zenodo.22682676) is the fixed archive of the reported code, model checkpoints, results, and provenance. The MRI dataset and the manuscript are not redistributed in that archive.

## Main findings

All results below refer to the final, independently reproduced Google Colab T4 reruns, not the earlier exploratory notebooks.

| Measure | Final result |
|---|---:|
| Clean MobileNetV2 test accuracy | 81.94% (1,311/1,600) |
| Test FPR using a threshold calibrated on the full validation set | 13.56% |
| Test FPR using a leakage-free validation calibration split | 15.44% |
| Evaluation FPR after recalibration with 400 clean images from the test collection | 10.75% |

The intended FPR budget was at most 10%. After deployment-side recalibration, FGSM and PGD detection was evaluated on a separate 1,200-image subset at the **same fixed threshold**. Successful-attack detection for FGSM was 36.0% at ε = 0.01, 73.4% at 0.05, 86.1% at 0.10, and at least 96.5% at ε ≥ 0.25. On images successfully attacked by both methods, PGD-10 and PGD-40 detection rates were within two percentage points of FGSM. Epsilon uses the **0–255 pixel-input scale**. The ε = 0.01 case is below one 8-bit intensity level and is reported for completeness, not as strong evidence of useful detection.

These results describe a shift between collections in a public dataset. They do not demonstrate performance in a hospital or against attacks adapted to evade the detector.

## Reproduce the reported results

1. Download the [Brain Tumor MRI Dataset by Masoud Nickparvar](https://www.kaggle.com/datasets/masoudnickparvar/brain-tumor-mri-dataset). The reported run used the 7,200-image archive; use the dataset digest and layout documented in the Zenodo package's `DATASET.md` to confirm that you have the same version. The images are not committed here.
2. In Google Drive, prepare `MyDrive/ThammasatResearch/` with `dataset/archive.zip`, `rerun/`, `models/`, and `results/`. Put the staged Python scripts from the [published package](https://doi.org/10.5281/zenodo.22682676) in `rerun/`. Keep prior runs separate; do not mix their model and result files.
3. Open [`rerun_colab.ipynb`](rerun_colab.ipynb) with the button above, select a T4 GPU, and run the cells in order. The notebook mounts Google Drive and executes stages 1–15. A stage is skipped when its declared outputs already exist; for a complete independent run, start with empty `models/` and `results/` directories.
4. Check `results/manifest.json` and `results/classifier_test_report.json` before interpreting downstream results. The pipeline verifies model SHA-256 hashes and refuses to combine incompatible artifacts. Compare the resulting CSV/JSON files with the archived [results guide](https://doi.org/10.5281/zenodo.22682676).

The archived run used Google Colab, an NVIDIA Tesla T4 GPU, Python 3.13.15, TensorFlow 2.20.0, and seed 42. The fixed Zenodo archive includes the three final Keras checkpoints, so the reported outputs can also be inspected without retraining. For exact run order and artifact descriptions, see its `code/rerun/README.md` and `results/README.md`.

## Repository map

| Path | Purpose |
|---|---|
| [`rerun_colab.ipynb`](rerun_colab.ipynb) | Main Colab entry point for the final staged rerun and dataset audits. |
| `ThammasatResearch/rerun/` | Local copy of the staged scripts. The Zenodo archive is the fixed publication snapshot. |
| `brain_tumor_adversarial_examples*.ipynb` and `brain_tumor_adversarial_detection*.ipynb` | Earlier FGSM and detector experiments, retained as research history. Their old model/results should not be mixed with the final rerun. |
| `papers/` | Manuscript source and working copies; the uploaded MICAD PDF is the submission copy. |
| `docs/` | Planning, meeting records, and historical handoff notes, some of which predate the final rerun. |

Patient-level independence between the original training and test collections has not been established. The dataset audit found duplicate and banner-marked images. See the manuscript and the Zenodo audit artifacts for the scope and limitations of these findings.

## Authors

- Ota Wakabayashi — National Institute of Technology, Nagano College
- Surasak Phetmanee — Thammasat University
