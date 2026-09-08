# The Operating Point Does Not Transfer: Deployment Calibration for Adversarial Attack Detection in Brain MRI

Authors: [NEEDS: student name and ordering decision], Surasak Phetmanee
[NEEDS: affiliations — Thammasat University?]

## Abstract

Adversarial-example detectors for medical imaging are usually reported
with threshold-free metrics (ROC-AUC) or with detection rates quoted "at
a false-positive rate of x%", where the threshold is calibrated on data
from the same side of the dataset as the training split. We show, on a
four-class brain-tumor MRI classification task, that this convention
systematically overstates deployed performance: a consistency-feature
detector reaches 0.887–0.995 ROC-AUC, yet every threshold calibrated on
training-side data misses its 10% FPR budget on the test collection by
+2.9 to +3.6 points — because the dataset's training and test folders
are different acquisition collections, and the clean-score upper tail
shifts while AUC stays flat. A leakage-free calibration split does not
fix this; 400 *clean* images from the deployment collection do (eval
FPR 9.83% against a 10% budget), a protocol that requires no labelled
attacks. At this honestly pinned operating point, we re-price all
detection rates and evaluate cross-attack transfer: the detector,
trained only on FGSM examples, detects successful PGD attacks it has
never seen within roughly one point of its FGSM performance on identical
images, with a regime crossover at ε≈0.25. As a by-product we observe
that the FGSM success set is a strict subset of the PGD success set at
every ε tested. All numbers trace to hash-guarded artifacts.

**Keywords:** adversarial examples · attack detection · medical imaging
· calibration · false-positive rate

## 1. Introduction

Deep networks for medical image classification are easy to fool with
imperceptible perturbations, and a body of work has answered with
detectors that flag adversarial inputs. For medical imaging the
literature's headline is optimistic: adversarial perturbations distort
feature statistics so strongly that simple detectors reach >98% AUC
[Ma et al. 2021]. Yet a detector is deployed at a *threshold*, not at an
AUC, and in a hospital the cost of a false alarm (a repeated scan, a
delayed diagnosis) makes the achieved false-positive rate a condition of
use rather than an implementation detail.

This paper asks what happens to the operating point between the lab and
deployment, using a brain-tumor MRI classifier as the test bed. Our
contributions:

1. **A measured failure of threshold transfer.** On a standard Kaggle
   brain-tumor dataset whose Training/ and Testing/ folders are distinct
   collections, a detector threshold selected for FPR ≤ 10% on
   validation data achieves 12.9% on test; a leakage-free calibration
   split makes it 13.6% (exp1/detector_v2b_test_by_epsilon.csv). The
   drift is confined to the upper tail of the clean score distribution
   (validation p90 = 0.151 vs test p90 = 0.355), exactly where
   thresholds operate, while ROC-AUC is unaffected — so the standard
   reporting convention cannot see it.
2. **A deployment-realistic fix.** Selecting the smallest threshold with
   FPR ≤ 10% on 400 clean images from the deployment collection pins the
   evaluated FPR at 9.83% (exp1/deployment_calibration_threshold.json).
   Calibration uses no attack examples at all — matching what a hospital
   actually has.
3. **Honest re-pricing, and cross-attack transfer at the pinned point.**
   At a true 10% FPR the detection rate for successful FGSM attacks is
   54.2% (ε=0.01), 70.3% (0.05), 87.6% (0.1), and 97.9–99.0% (ε ≥ 0.25)
   (exp1/detector_v2b_deploycal_eval_by_epsilon.csv). Trained on FGSM
   only, the detector detects successful PGD attacks (10 and 40 steps,
   random start) within ±1–3 points of these numbers on the *same*
   images (intersection protocol, exp1/attack_intersection_analysis.csv),
   with a crossover: below ε≈0.25 PGD is *more* detectable, above it
   about one point less.
4. **A strict-dominance observation.** At every ε tested, every image
   broken by FGSM is also broken by PGD (n_fgsm_only = 0 in all 12
   pairings) — direct evidence that FGSM-only robustness evaluation is
   optimistic.

We deliberately label only *successful* attacks (a correct diagnosis
turned incorrect) as positives: unsuccessful perturbations are noise for
a clinical threat model. All experiments run under a pipeline in which
every model artifact is SHA-256-chained and every downstream stage
verifies hashes and clean accuracy before computing
(exp1/manifest.json, exp1/PROVENANCE.md).

## 2. Related Work

**Consistency-based detection.** Feature squeezing [Xu et al. 2018,
arXiv:1704.01155] compares predictions before and after input squeezing
(bit-depth reduction, blur) and thresholds the L1 difference, selecting
the threshold on clean data for a target FPR. Our detector learns from a
richer consistency representation (penultimate features, class
probabilities, blur-consistency summaries, confidence/margin/entropy)
but inherits the clean-calibrated-threshold idea — and measures what Xu
et al. did not: whether that threshold survives a collection shift.

**Detection in medical imaging.** Ma et al. [2021, arXiv:1907.10456]
established that medical adversarial examples are easy to detect
(>98% AUC on X-ray, fundoscopy, dermoscopy). Our AUCs agree; our point
is that the AUC-to-operating-point gap is where deployment fails. A
DFT-based detector for MRI has been proposed for Alzheimer's
classification [arXiv:2408.08489]; it labels all adversarial inputs
positive and does not examine FPR transfer.

**Defense on the same task.** A recent multi-layered defense for brain
tumor classification [Sci. Reports 2025,
doi:10.1038/s41598-025-00890-x] combines ensemble adversarial training
with feature squeezing on the same dataset family (VGG16; FGSM and PGD),
recovering 47–54% classification accuracy under attack. That is
complementary robustness, not detection; no detector, FPR, or
calibration is involved.

**Cross-attack generalization.** That detectors trained on one gradient
attack generalize to others is documented in the natural-image
literature; AED-PADA [arXiv:2404.12635] improves it further via
multi-source domain adaptation. We therefore do not claim cross-attack
transfer as novel; our contribution is measuring it *at a pinned
deployment operating point* and on an intersection of successes, which
removes the changing-denominator confound.

## 3. Experimental Setup

**Task and data.** Four-class brain-tumor MRI classification (glioma,
meningioma, no-tumor, pituitary), 5,600 training and 1,600 test images
(balanced, 224×224, pixel range 0–255). The training folder is split
80/20 into 4,480 train / 1,120 validation source images with verified
zero overlap. [NEEDS: exact dataset citation/provenance for the 7,200-
image Kaggle variant used]

**Classifier.** ImageNet-pretrained MobileNetV2, frozen backbone, light
augmentation, trained head (Adam 1e-3, ≤10 epochs, early stopping);
clean test accuracy 81.88% (1,310/1,600), manifest-recorded
(exp1/manifest.json). Training is fully seeded with op determinism, and
the canonical model file is never overwritten — downstream stages refuse
to run if its hash changes.

**Attacks.** Untargeted white-box FGSM on the 0–255 input scale at
ε ∈ {0.01, 0.05, 0.1, 0.25, 0.5, 1.0}; PGD with random start, step
α = ε/4, K ∈ {10, 40}, per-batch assertions keeping every perturbation
inside the ε-ball. FGSM at ε=1 already yields 95.0% attack success on
initially-correct images; PGD-40 reaches 100.0% (978/978 on the eval
split) — the undefended classifier offers no robustness at that budget.

**Detector.** A two-layer MLP (256/64, dropout) on a consistency feature
vector extracted from the *frozen* classifier: penultimate GAP features,
class probabilities before and after a light average-pool blur, their
differences, and confidence/margin/entropy summaries. Positives are
successful attacks only, at training ε ∈ {0.01, 0.1, 0.5}; class
weights balance the loss. Model selection uses a 560-image validation
half (val_A); the other 560 images (val_B) are reserved for threshold
calibration and touch neither training nor selection.

**Evaluation protocol.** The 1,600 test images are split (seeded) into
400 calibration / 1,200 evaluation images. Every reported test number
comes from the 1,200 evaluation images at one fixed threshold; the test
set is never used for tuning. ε values 0.05, 0.25, 1.0 are unseen by the
detector.

## 4. The Operating Point Does Not Transfer

Three calibration strategies, one budget (FPR ≤ 10%):

| Calibration data | Claimed FPR | Achieved test FPR | Error |
|---|---|---|---|
| Validation, 1,120 imgs (also used for model selection) | ≤10% | 12.94% | +2.9 |
| val_B, 560 imgs (leakage-free) | ≤10% | 13.63% | +3.6 |
| 400 clean deployment-collection imgs | ≤10% | **9.83%** | **−0.2** |

(Sources: exp1/detector_v2b_threshold.json,
exp1/detector_v2b_test_by_epsilon.csv,
exp1/deployment_calibration_threshold.json.)

Removing selection leakage (row 2) does not help — the cause is not
overfitting but a collection shift: the clean-score distributions of the
Training-derived and Testing images share a median of 0.000 but diverge
in the upper tail (p90 0.151 → 0.355, p95 0.423 → 0.649), producing a
stable ≈ +3.8-point FPR offset at any Training-side threshold
[NEEDS: diag_score_shift output file copied into exp1/]. ROC-AUC moves
by <0.01 under the same shift, which is why AUC-only reporting cannot
detect the problem. The margin variant (calibrating to 7.5% for
headroom) shifts the number without fixing it (12.06%).

Calibrating on 400 clean images from the deployment collection lands the
threshold at 0.361 — almost exactly the value the tail analysis predicts
for a true 10% FPR — and requires no labelled attacks: a realistic
protocol for a hospital that has clean scans but no attack examples.

**Cost of honesty.** At the pinned threshold, low-ε detection is lower
than the mis-calibrated numbers suggested: 70.3% instead of 81.6% at
ε=0.05. The earlier figure was bought with ~36% more false alarms than
claimed. At ε=0.01, PR-AUC is 0.080 (24 positives vs 1,200 cleans):
tiny attacks remain essentially undetectable, and ROC-AUC (0.887)
flatters this regime badly — we quote PR-AUC alongside ROC-AUC at all
small ε.

## 5. Cross-Attack Transfer at the Pinned Operating Point

Trained on FGSM only, evaluated against PGD it has never seen, at the
same fixed threshold (exp1/pgd_eval_by_epsilon.csv). To avoid the
changing-denominator confound (PGD breaks more images than FGSM), we
compare on the intersection of success sets
(exp1/attack_intersection_analysis.csv):

| ε | n (intersection) | det. FGSM | det. PGD-10 | det. PGD-40 |
|---|---|---|---|---|
| 0.01 | 24 | 54.2% | 54.2% | 54.2% |
| 0.05 | 138 | 70.3% | 71.7% | 73.2% |
| 0.10 | 307 | 87.6% | 90.2% | 89.9% |
| 0.25 | 664 | 97.9% | 96.7% | 96.7% |
| 0.50 | 865 | 99.0% | 97.7% | 97.8% |
| 1.00 | 928 | 98.7% | 98.2% | 98.2% |

Three observations:

1. **Transfer holds.** Cross-family detection costs at most ~1.2 points
   at high ε and is *better* than FGSM by 1.4–2.9 points at low ε.
   ROC-AUC is nearly identical throughout (0.887–0.994 for both
   families).
2. **A crossover at ε ≈ 0.25.** Below it PGD is more detectable than
   FGSM on identical images; above it slightly less. A mechanism
   consistent with all rows — FGSM always sits at the corner of the
   ε-ball, while PGD can stop inside it once the decision boundary is
   crossed, leaving a smaller effective perturbation when the budget has
   slack — is plausible but *not measured here*; verifying it via
   perturbation norms on the intersection images is future work.
3. **Strict dominance.** n_fgsm_only = 0 in every pairing: no image at
   any ε is broken by FGSM but not by PGD. Reporting robustness against
   FGSM alone is therefore provably optimistic on this task. The images
   only PGD can break at ε ≥ 0.25 are detected at 98–100% — resisting a
   one-shot attack forces a perturbation the detector sees clearly.

## 6. Limitations

- **ε = 0.01 is below input precision.** On the 0–255 scale it is less
  than one 8-bit quantization level; FGSM and PGD-10 coincide to four
  decimals there. We keep the row for completeness but it should not be
  read as a meaningful attack setting.
- **No adaptive attacks.** All attacks target the classifier; none
  optimize to evade the detector. A Carlini-style adaptive evaluation is
  the necessary next step before any strong defensive claim.
- **One dataset, one classifier.** The FPR-transfer finding is measured
  on one (widely used) dataset whose Training/Testing split happens to
  be a collection split; breadth across modalities and backbones is
  future work. The evaluation set is 75% of the original test set (400
  images are spent on calibration).
- **Mechanism unmeasured.** The crossover explanation in §5 is a
  hypothesis; the artifacts (per-image scores and masks) are persisted
  so the norm analysis needs no retraining.

## 7. Conclusion

On a real medical-imaging dataset, the gap between a detector's AUC and
its deployed operating point is where the security claim quietly breaks:
every training-side threshold missed its FPR budget, while 400 clean
deployment images — no attacks required — pinned it. We recommend that
detection papers (i) report the achieved FPR on the evaluation
distribution next to every detection rate, (ii) treat threshold-free
metrics as insufficient for deployment claims, and (iii) compare attack
families on intersections of success sets. Under this stricter
accounting our FGSM-trained consistency detector remains effective:
≥87.6% detection of successful attacks at ε ≥ 0.1 at a true 10% FPR,
transferring across attack families at a cost of about one point.

## References

- [Goodfellow et al. 2015] I. Goodfellow, J. Shlens, C. Szegedy.
  Explaining and Harnessing Adversarial Examples. ICLR 2015.
  arXiv:1412.6572
- [Madry et al. 2018] A. Madry, A. Makelov, L. Schmidt, D. Tsipras,
  A. Vladu. Towards Deep Learning Models Resistant to Adversarial
  Attacks. ICLR 2018. arXiv:1706.06083
- [Xu et al. 2018] W. Xu, D. Evans, Y. Qi. Feature Squeezing: Detecting
  Adversarial Examples in Deep Neural Networks. NDSS 2018.
  arXiv:1704.01155
- [Ma et al. 2021] X. Ma et al. Understanding Adversarial Attacks on
  Deep Learning Based Medical Image Analysis Systems. Pattern
  Recognition 110 (2021). arXiv:1907.10456
- [Sci. Reports 2025] A multi-layered defense against adversarial
  attacks in brain tumor classification using ensemble adversarial
  training and feature squeezing. Scientific Reports (2025).
  doi:10.1038/s41598-025-00890-x [VERIFY: author list]
- [AED-PADA 2024] Improving Generalizability of Adversarial Example
  Detection via Principal Adversarial Domain Adaptation.
  arXiv:2404.12635 [VERIFY: venue/author list]
- [DFT-MRI 2024] DFT-Based Adversarial Attack Detection in MRI Brain
  Imaging. arXiv:2408.08489 [VERIFY: author list]
- [Sandler et al. 2018] M. Sandler et al. MobileNetV2: Inverted
  Residuals and Linear Bottlenecks. CVPR 2018. arXiv:1801.04381
- [NEEDS: dataset citation]
