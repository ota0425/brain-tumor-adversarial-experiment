# Research Meeting Record — 1 September 2026

## Meeting decisions

- The FGSM phase is complete. Preserve the notebooks, saved outputs, models, and limitations as the FGSM baseline.
- The next research phase will study Projected Gradient Descent (PGD) attacks against the same four-class MobileNetV2 brain-tumor MRI classifier.
- MICAD 2026 was recommended as a possible conference for this work.

## Completed FGSM study

### Classifier and dataset

- Classes: glioma, meningioma, no tumor, and pituitary
- Training source images: 5,600
- Testing source images: 1,600
- Input: 224 x 224 x 3 on a 0–255 pixel scale
- Recorded clean Testing accuracy: 83.19% (1,331/1,600 correct)
- Attack: untargeted white-box FGSM

### FGSM vulnerability

An attack was successful when an initially correct clean prediction became incorrect after FGSM.

| Epsilon | Adversarial accuracy | Attack success rate |
|---:|---:|---:|
| 0.01 | 80.87% | 2.78% |
| 0.05 | 70.56% | 15.18% |
| 0.10 | 53.19% | 36.06% |
| 0.25 | 20.81% | 74.98% |
| 0.50 | 7.81% | 90.61% |
| 1.00 | 3.31% | 96.02% |

Even perturbations below one gray level on the 0–255 scale substantially increased misclassification. The main degradation region was epsilon 0.05–0.25.

## Detection Experiment 1

Experiment 1 labelled every FGSM image as adversarial, whether or not the attack changed the diagnosis. It used the final MobileNetV2 feature vector and fine-tuned the upper 30 backbone layers.

Fine-tuning produced only a small Validation improvement over the frozen baseline:

| Metric | Frozen | Fine-tuned |
|---|---:|---:|
| Binary accuracy | 0.5702 | 0.5801 |
| ROC-AUC | 0.6118 | 0.6329 |
| PR-AUC | 0.6395 | 0.6727 |
| False-positive rate | 0.5438 | 0.5009 |

On Testing, the false-positive rate was 51.75%. The detector frequently predicted "adversarial," so its apparently high successful-attack recall was not operationally useful. Its ROC-AUC for clean versus all attacks increased from 0.515 at epsilon 0.01 to 0.743 at epsilon 1.0.

## Detection Experiment 2

Experiment 2 focused on harmful attacks that changed an initially correct diagnosis. It used classifier probabilities, internal features, and consistency before and after light blur. The threshold was selected on Validation under an FPR constraint.

| Epsilon | Successful attacks | Successful-attack detection rate | Successful vs clean ROC-AUC | PR-AUC |
|---:|---:|---:|---:|---:|
| 0.01 | 37 | 70.27% | 0.8697 | 0.0891 |
| 0.05 | 202 | 85.15% | 0.9229 | 0.5717 |
| 0.10 | 480 | 92.29% | 0.9563 | 0.8688 |
| 0.25 | 998 | 97.39% | 0.9839 | 0.9770 |
| 0.50 | 1,206 | 98.34% | 0.9914 | 0.9905 |
| 1.00 | 1,278 | 98.83% | 0.9931 | 0.9930 |

- Testing clean false-positive rate: 14.06%
- The target detection rate of at least 80% was achieved for epsilon >= 0.05.
- The target FPR of at most 10% was not achieved.
- The epsilon 0.01 result is uncertain because only 37 attacks succeeded and its PR-AUC remained low.

## Fair comparison

The two detectors were subsequently compared on identical Testing images and identical positive subsets.

- For clean versus all FGSM attacks, Experiment 2 was clearly better from epsilon 0.05 upward; both methods were near random at epsilon 0.01 because most attacks did not change the input sufficiently for reliable detection.
- For clean versus successful attacks, Experiment 2 consistently achieved much higher ROC-AUC than Experiment 1.
- The improvement should be described as a better detector for harmful, diagnosis-changing attacks—not as a universal detector for every adversarial input.

## FGSM conclusion and limitations

1. The MRI classifier was highly vulnerable to FGSM as epsilon increased.
2. Detecting all very small perturbations was difficult when the attack did not affect the diagnosis.
3. Consistency-based features were effective for detecting diagnosis-changing attacks.
4. Clean FPR remains too high for practical use.
5. Results apply to this dataset, classifier, split, FGSM implementation, and white-box threat model only.
6. Patient-level independence could not be verified from the available metadata.
7. The current Google Drive `baseline_mobilenetv2.keras` produced 78.12% clean accuracy in a later check, whereas the recorded FGSM experiments used the 83.19% artifact. The original artifact must be restored for an exact rerun; the existing saved outputs remain the historical FGSM record.

## Next phase: PGD

### Primary question

> How vulnerable is the MRI classifier to iterative PGD, and do the FGSM-trained detectors generalize to PGD without retraining?

### Planned order

1. Freeze and archive all FGSM results.
2. Restore or version the exact classifier artifact and record a file hash.
3. Implement untargeted white-box L-infinity PGD with clipping to both the epsilon-ball and the valid 0–255 image range.
4. Verify the implementation with epsilon = 0 and check that every perturbation satisfies the norm constraint.
5. Evaluate classifier accuracy and attack success by epsilon, number of steps, step size, and random start.
6. Evaluate both FGSM detectors on PGD without retraining (zero-shot transfer).
7. Only after the zero-shot evaluation, consider a separately named PGD-trained or mixed-attack detector.
8. Keep model selection and threshold selection on Validation; reserve Testing for final evaluation.

Initial implementation candidates are 10 and 20 PGD steps with step size defined relative to epsilon. Exact settings must be fixed before Testing and reported with epsilon, step size, steps, random-start policy, loss, norm, and clipping range.

## MICAD 2026

The recommended venue is the 7th International Conference on Medical Imaging and Computer-Aided Diagnosis (MICAD 2026).

- Location: Edinburgh, United Kingdom
- Format: hybrid (online and onsite)
- Conference dates: 22–24 October 2026
- Final full-paper deadline: 15 September 2026 (AoE)
- Registration deadline listed by the organizer: 29 September 2026
- Language: English
- Proceedings: planned for Springer Lecture Notes in Electrical Engineering; the organizer states that proceedings will be submitted to EI Compendex, Scopus, and SpringerLink for evaluation/indexing.

The topic is relevant to MICAD because it combines MRI, deep learning, computer-aided diagnosis, and model robustness. The submission deadline is close, so scope, authorship, required additional PGD evidence, and readiness for submission should be confirmed with the supervisor immediately.

Official links:

- Conference: <https://www.micad.org/>
- Call for papers: <https://www.micad.org/cfp.html>
- Submission guidelines: <https://www.micad.org/submission.html>

## Immediate action items

- [ ] Confirm the intended MICAD paper scope and author list with the supervisor.
- [ ] Decide whether the current FGSM evidence is sufficient for a submission or whether PGD results are required before 15 September.
- [ ] Restore/version the exact 83.19% classifier artifact and record its hash.
- [ ] Create a separate PGD notebook without modifying the completed FGSM notebooks.
- [ ] Define the PGD threat model and hyperparameter grid before running Testing.
