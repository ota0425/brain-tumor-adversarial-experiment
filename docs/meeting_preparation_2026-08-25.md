# Meeting Preparation — 25 August 2026

## Purpose

- Briefly explain what I learned from *Adversarial Attacks and Defences: A Survey*.
- Share the current FGSM experiment results.
- Explain the adversarial-input detector I am developing.
- Ask Mr. Surasak for feedback on the next evaluation step.

## What I learned from the paper

- Deep-learning models can be fooled by small perturbations that may be difficult for humans to notice.
- Adversarial attacks can be classified by the attack stage, the attacker's knowledge, and the attacker's goal.
- My FGSM experiment is a white-box, test-time evasion attack with an untargeted misclassification goal.
- Defence methods include adversarial training, gradient hiding, defensive distillation, feature squeezing, input detection, and input reforming.
- Each defence method has limitations; there is no universal defence against every attack.

## My experiment

- I trained a MobileNetV2 model to classify four brain MRI classes: glioma, meningioma, no tumor, and pituitary.
- The clean test accuracy was 83.19%.
- FGSM significantly reduced the classification accuracy as epsilon increased.
- I am now developing a binary detector that distinguishes clean images from adversarial images.
- Clean images are labelled as 0, and FGSM adversarial images are labelled as 1.
- The detector uses internal features extracted from the existing MRI classification model.
- The training epsilon values are 0.01, 0.1, and 0.5.
- I plan to test generalization using unseen epsilon values of 0.05, 0.25, and 1.0.

## Detection results to confirm before the meeting

- [x] Run Steps 1–3 of `brain_tumor_adversarial_detection.ipynb` in Google Colab.
- [x] Confirm that the clean/adversarial detection labels are balanced 1:1.
- [x] Record the best-model validation metrics at threshold 0.5.
- [x] Complete detector training and validation and save the configured artifacts to Google Drive.

### Recorded validation results

| Metric | Result |
|---|---:|
| Binary Accuracy | 0.5408 |
| Loss | 0.7049 |
| ROC-AUC | 0.6520 |
| PR-AUC | 0.6552 |
| Precision | 0.8425 |
| Recall | 0.1003 |

The detector performed only slightly better than random classification. Its high precision was accompanied by very low recall, so it missed approximately 90% of the adversarial validation examples at threshold 0.5. These values are preliminary because the Training/Validation split implementation must be corrected and the experiment rerun before the results are treated as final.

## Questions for Mr. Surasak

- Is this detection approach appropriate for the next stage of the research?
- Which metric should I prioritize: ROC-AUC, recall, or false-positive rate?
- Should I evaluate the detector against PGD after completing the FGSM evaluation?
- Which part of the survey paper should I study more deeply?

## Meeting outcomes

- I explained the structure and training workflow of the Detection Notebook to Mr. Surasak.
- I shared the initial validation results and explained that the detector's performance was close to random classification.
- We decided to improve the detector by fine-tuning the MobileNetV2 backbone that had been frozen in the initial experiment.
- This week's main task is to improve detection performance through fine-tuning.
- The provisional target is approximately 80% binary accuracy.
- Accuracy will not be used alone: ROC-AUC, PR-AUC, recall, and false-positive rate will also be reported.

## Action items after the meeting

- [x] Correct the Training/Validation split code so that the two sets are disjoint.
- [ ] Rerun the frozen-backbone experiment in Colab and verify zero overlapping source paths.
- [ ] Preserve the rerun frozen-backbone result as the baseline experiment.
- [ ] Unfreeze only the upper MobileNetV2 layers and fine-tune them with a small learning rate.
- [ ] Compare the fine-tuned model with the frozen baseline under the same seed, split, epsilon values, and metrics.
- [ ] Evaluate results separately for seen and unseen epsilon values after model selection is complete.

## Point to confirm at the next meeting

- Does “fine-tune MobileNetV2” mean fine-tuning the backbone jointly with the binary detector loss, or first fine-tuning the four-class MRI classifier and then rebuilding the detector? The current working plan is the former.

## Careful wording

- Do not claim: “This model can detect any attack.”
- Say: “I want to investigate whether the detector can generalize to unseen perturbation strengths and different attacks.”

## Reference

- Anirban Chakraborty, Manaar Alam, Vishal Dey, Anupam Chattopadhyay, and Debdeep Mukhopadhyay, *Adversarial Attacks and Defences: A Survey*, arXiv:1810.00069, 2018.
- Local PDF: `docs/1810.00069v1.pdf`
- URL: https://arxiv.org/abs/1810.00069
