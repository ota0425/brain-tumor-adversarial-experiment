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

The dataset audit and exclusion analysis were added as stages 11--15 and
rerun with the final verified model. The resulting classifier-specific
audit metrics reproduce the values reported in the paper: 100 confirmed
meningioma duplicates, 15.1% accuracy on banner-flagged glioma images,
and 81.94% overall clean accuracy.

Stage 10 was subsequently run on the same verified model. Its persisted
`exp1/clean_score_distribution_shift.csv` supplies the clean-score
quantiles and fixed-threshold FPRs restored in Table 3.

## Documentation reconciliation — 2026-09-15

`paper.md` now summarizes final CSV/JSON results; the superseded prose is preserved as `paper-pre-final-rerun.md`. Historical plans and reviews are labeled. `docs/RESEARCH_SUMMARY_JA.md` provides the Japanese presentation reference.

Corrections include the achieved 10.75% FPR (not attainment of the 10% target), ε = 0.01 ROC-AUC 0.876, distinct 1,600/1,200-image evaluation denominators, and removal of the unsupported consistent crossover interpretation. Success-set containment includes equality in the ε = 0.01 FGSM/PGD-10 case; it is not strict containment in every pairing.

Working LaTeX sources still contain prose requiring a separate manuscript revision: the `Cost of honesty` paragraph quotes ROC-AUC 0.887 despite the final table value 0.876, and older uncertainty/exclusion prose retains sign-pattern or pre-final-run descriptions. Consult final artifacts before reusing those passages. This documentation update does not edit the submitted PDF, LaTeX, experimental artifacts, or the fixed publication archive.
