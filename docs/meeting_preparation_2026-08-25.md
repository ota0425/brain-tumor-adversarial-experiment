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

- [ ] Run Steps 1–3 of `brain_tumor_adversarial_detection.ipynb` in Google Colab.
- [ ] Confirm that the clean classifier accuracy is approximately 83.19%.
- [ ] Confirm that the clean/adversarial detection labels are balanced 1:1.
- [ ] Record the best validation ROC-AUC: **[not measured yet]**
- [ ] Record the validation PR-AUC: **[not measured yet]**
- [ ] Record the validation precision and recall: **[not measured yet]**
- [ ] Save the learning curves and detector model to Google Drive.

## Questions for Mr. Surasak

- Is this detection approach appropriate for the next stage of the research?
- Which metric should I prioritize: ROC-AUC, recall, or false-positive rate?
- Should I evaluate the detector against PGD after completing the FGSM evaluation?
- Which part of the survey paper should I study more deeply?

## Careful wording

- Do not claim: “This model can detect any attack.”
- Say: “I want to investigate whether the detector can generalize to unseen perturbation strengths and different attacks.”

## Reference

- Anirban Chakraborty, Manaar Alam, Vishal Dey, Anupam Chattopadhyay, and Debdeep Mukhopadhyay, *Adversarial Attacks and Defences: A Survey*, arXiv:1810.00069, 2018.
- Local PDF: `docs/1810.00069v1.pdf`
- URL: https://arxiv.org/abs/1810.00069
