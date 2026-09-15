# Towards Trustworthy and Reliable Deployment of Adversarial Attack Detection for Brain MRI Classification

Authors: Ota Wakabayashi (National Institute of Technology, Nagano College), Surasak Phetmanee (Thammasat University; corresponding author).

Updated: 2026-09-15. This is a current Markdown research summary, not a verbatim transcription of the submitted PDF. It replaces the superseded draft preserved in [paper-pre-final-rerun.md](paper-pre-final-rerun.md). Manuscript wording and bibliography are in [the LaTeX source](overleaf_submission/paper.tex); that working source may differ from the submitted PDF. Numerical claims below are checked against the final CSV/JSON artifacts, which take precedence over stale prose. See [provenance](exp1/PROVENANCE.md) and the [Japanese summary](../../docs/RESEARCH_SUMMARY_JA.md).

## Abstract

This study evaluates whether an adversarial detector's threshold preserves its intended false-positive rate (FPR) when transferred between collections in a public four-class brain MRI dataset. Thresholds targeting at most 10% FPR on training-side validation data yielded 13.56% and 15.44% FPR on the 1,600-image test collection. Recalibration using 400 clean test-collection images yielded 10.75% FPR on a separate 1,200-image evaluation subset. This approaches, but does not meet, the 10% target. At that fixed threshold, an FGSM-trained detector detects successful unseen PGD attacks within two percentage points of FGSM on common success sets. The results concern non-adaptive attacks on one dataset and classifier; they do not establish clinical reliability or resistance to detector-aware attacks.

## Research question and contribution

High ROC-AUC describes discrimination across thresholds; it does not establish the FPR achieved at a particular threshold on a different collection. The contribution is an empirical evaluation of threshold transfer, clean-only target-collection recalibration, and cross-attack detection under a fixed operating threshold. Neither calibration itself nor cross-attack generalization is claimed as a new method.

## Experimental setup

- Data: the experimental 7,200-image Brain Tumor MRI archive, with glioma, meningioma, no-tumor, and pituitary classes; 5,600 Training and 1,600 Testing images. Images are resized to 224 × 224 × 3.
- Classifier: ImageNet-pretrained MobileNetV2 with frozen backbone and a trained classification head. Final clean test accuracy is **81.94% (1,311/1,600)**.
- Training-side split: 4,480 training and 1,120 validation source images. The v2b detector uses separate 560-image model-selection and 560-image calibration subsets. Disjoint source paths do not establish patient-level independence.
- Detector: a two-layer MLP (256/64 units, dropout) using classifier features, original/blurred predictions, consistency differences, and confidence, margin, and entropy summaries. Positive training examples are successful FGSM attacks at ε = 0.01, 0.1, 0.5.
- Attacks: untargeted white-box FGSM and random-start PGD-10/40, with PGD step size ε/4. They target the classifier, not the detector.
- **All ε values use the 0–255 pixel-input scale.** Thus ε = 1 corresponds to 1/255 on a normalized 0–1 scale. Values 0.05, 0.25, and 1.0 are unseen during detector training.
- Deployment-calibrated evaluation: 400 clean Testing images for threshold calibration, and a separate 1,200 for evaluation (979 initially classified correctly). Classifier accuracy and training-side-threshold test FPRs use all 1,600 test images; deployment-calibrated attack/detection metrics use the 1,200-image subset.

## Threshold transfer and recalibration

FPR is the fraction of clean images incorrectly flagged as adversarial. The target is at most 10% on the calibration sample, not a guarantee for future evaluation images.

| Calibration data | Evaluation data | Achieved clean FPR | Difference from 10% target |
|---|---|---:|---:|
| Full validation, 1,120 images (also used for selection) | Full test, 1,600 images | 13.56% | +3.56 percentage points |
| Disjoint val_B, 560 images | Full test, 1,600 images | 15.44% | +5.44 percentage points |
| Clean target-collection subset, 400 images | Held-out test subset, 1,200 images | 10.75% | +0.75 percentage points |

The deployment threshold is **0.32068297266960144**. Its calibration FPR is 10%, but held-out evaluation FPR is **10.75%**. The 7.5% calibration-budget margin variant uses threshold 0.4477800726890564 and yields evaluation FPR **8.25%**, with lower detection rates. These operating points must not be mixed.

For the final v2b detector, the full-validation clean-score 90th/95th percentiles are 0.1890/0.3996, compared with 0.3514/0.6868 on the full test collection. At threshold 0.15071886777877808, FPR is 10.98% on full validation and 15.44% on full test. The 560-image val_B calibration FPR is 8.93%; it has a different denominator from full validation. These results document a score-distribution shift; they do not isolate a single causal acquisition factor.

The three strategies do not all use identical evaluation samples and detectors. The table reports the recorded protocols and should not be described as a paired comparison holding every other factor fixed.

## FGSM detection at the deployment threshold

Detection is conditional on attacks that change an initially correct classification into an incorrect one. It is not classification accuracy, attack success rate, or detection among all perturbed images. All rows below use 1,200 clean evaluation images, clean FPR 10.75%, and threshold 0.32068297266960144. The margin column instead uses its own fixed threshold and clean FPR 8.25%.

| ε | Successful attacks | Detection | Detection (margin) | ROC-AUC | PR-AUC |
|---:|---:|---:|---:|---:|---:|
| 0.01 | 25 | 36.0% | 28.0% | 0.876 | 0.075 |
| 0.05 | 139 | 73.4% | 63.3% | 0.918 | 0.496 |
| 0.10 | 310 | 86.1% | 83.2% | 0.956 | 0.833 |
| 0.25 | 665 | 96.5% | 95.8% | 0.985 | 0.973 |
| 0.50 | 865 | 98.3% | 97.9% | 0.993 | 0.991 |
| 1.00 | 929 | 98.5% | 98.3% | 0.995 | 0.994 |

At ε = 0.01, there are only 25 successful attacks, detection is 36.0%, and PR-AUC is 0.075. This sub-8-bit-intensity perturbation regime is reported for completeness; it does not demonstrate reliable detection of tiny attacks.

## FGSM-to-PGD transfer

The detector was trained on FGSM only. To avoid changing denominators when PGD succeeds on additional images, compare detection on images successfully attacked by both methods at the same deployment threshold.

| ε | Common successes per pairing | FGSM detection | PGD-10 detection | PGD-40 detection |
|---:|---:|---:|---:|---:|
| 0.01 | 25 | 36.0% | 36.0% | 36.0% |
| 0.05 | 139 | 73.4% | 74.8% | 74.1% |
| 0.10 | 310 | 86.1% | 87.7% | 88.1% |
| 0.25 | 665 | 96.5% | 96.5% | 96.7% |
| 0.50 | 865 | 98.3% | 97.9% | 98.3% |
| 1.00 | 929 | 98.5% | 99.0% | 98.9% |

Every paired difference is below two percentage points. This is a descriptive result, not a statistical equivalence claim. The final rerun does **not** support the earlier consistent crossover claim or a mechanism explaining such a crossover.

Across all 12 evaluated pairings, no image is successfully attacked only by FGSM. This is containment of FGSM success sets within PGD success sets in these experiments, not a universal theorem; at ε = 0.01 the FGSM and PGD-10 success sets are equal. At ε = 1, PGD-40 succeeds on all 979 initially correct evaluation images. Raw PGD results, whose denominators differ from the intersection table, are in [pgd_eval_by_epsilon.csv](exp1/pgd_eval_by_epsilon.csv).

## Dataset audit and limitations

The audit reports 100 meningioma test images duplicated from Training images, synthetic augmentations, and banner-marked subpopulations. Banner-flagged glioma test images have 15.1% classifier accuracy versus 74.4% for unflagged images. These are dataset-specific observations; they do not establish that banners cause the difference. Patient-level independence has not been established. Exclusion results require their own recorded sample definitions and must not be substituted for the full-test baseline.

Other limitations are one dataset, one classifier, one recorded seed, small success counts at low ε, and no attack optimized to evade the detector. Independent reproduction of the same seeded pipeline verifies reproducibility, not variation across seeds or clinical sites. The 400-image calibration subset is assumed clean. Clinical deployment was not evaluated.

## Reproducibility and status

The student and supervisor independently reran the pipeline on Google Colab Tesla T4 with TensorFlow 2.20.0 and seed 42 and obtained matching reported evaluation metrics. Model hashes are verified within each run; serialized model files need not be byte-identical between runs.

According to the [15 September handoff](../../docs/HANDOFF.md), the manuscript was submitted to MICAD 2026 (OpenConf ID 764); acceptance is not established. The Zenodo reproducibility record is [10.5281/zenodo.22682676](https://doi.org/10.5281/zenodo.22682676), containing code, checkpoints, results, and provenance, excluding the manuscript and original MRI images.

## Sources for figures and numbers

- Final results guide: `results/README.md` in the [Zenodo package](https://zenodo.org/records/22682676) and [provenance](exp1/PROVENANCE.md).
- Classifier report: `results/classifier_test_report.json` in the [Zenodo package](https://zenodo.org/records/22682676).
- Baseline test results: `results/detector_v2_test_by_epsilon.csv` in the [Zenodo package](https://zenodo.org/records/22682676) and [v2b test results](exp1/detector_v2b_test_by_epsilon.csv).
- [Deployment calibration](exp1/deployment_calibration_threshold.json) and [FGSM evaluation](exp1/detector_v2b_deploycal_eval_by_epsilon.csv).
- [Common-success comparisons](exp1/attack_intersection_analysis.csv) and [score distributions](exp1/clean_score_distribution_shift.csv).
- Literature references: [manuscript bibliography](overleaf_submission/refs.bib). This summary does not independently revalidate the literature review.

## Conclusion

Training-side threshold calibration did not preserve the intended 10% FPR on the test collection. Clean-only target-collection recalibration reduced the observed error to 10.75%, without guaranteeing the target. At that operating point, FGSM-to-PGD detection differences on common successes remained below two percentage points. Further work should test calibration stability and detector-aware attacks before making broader claims.
