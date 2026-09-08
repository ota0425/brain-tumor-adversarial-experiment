# Colab rerun update (2026-09-08)

This folder was created from the latest Overleaf source archive and
updated using the student's final Colab rerun. The supervisor's
independent Colab rerun produced the same reported metrics.

Updated artifacts:

- `paper.tex`: environment, primary numerical claims, tables, and conclusions
- `exp1/*.csv` and `exp1/*.json`: final student Colab rerun artifacts
- `exp1/fig_fpr_transfer.pdf`: regenerated for FPR 13.56%, 15.44%, and 10.75%
- `exp1/fig_attack_detection.pdf`: regenerated from the final intersection data
- `exp1/PROVENANCE.md`: final result provenance

Important scientific change: the final shared rerun does not reproduce
the previously claimed consistent FGSM/PGD detectability crossover.
That claim was removed. The supported result is that PGD detection on
the shared success sets remains within two percentage points of FGSM.

The dataset audit and exclusion analysis were not part of stages 1--9.
Their dataset-intrinsic findings are retained, but classifier-specific
exclusion metrics should be rerun with the final model before submission.

Stage 10 was subsequently run on the same verified model. Its persisted
`exp1/clean_score_distribution_shift.csv` supplies the clean-score
quantiles and fixed-threshold FPRs restored in Table 3.
