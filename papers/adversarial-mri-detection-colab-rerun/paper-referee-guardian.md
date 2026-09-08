# Referee 1 — Paradigm Guardian (adversarial epistemics)

**SUMMARY**: Measurement paper: on a 4-class brain-MRI task, thresholds
for an adversarial-attack detector calibrated on training-side data miss
their FPR budget on the test collection (+2.9/+3.6pt) while AUC is
flat; 400 clean deployment images pin it (9.83%); detection re-priced at
the pinned point; cross-attack transfer measured on intersections;
dataset audit finds duplication, synthetic padding, and a banner
subpopulation on which glioma collapses. Artifact discipline (hash
chain, fail-closed guards, disclosed incident) is unusually strong.

**STRAWMAN CHECK** — my core mandate. The paper's villain is "the
standard reporting convention" (AUC-only, or FPR quoted from
training-side calibration). Is that a real practice or a convenient
ghost? Real: Ma et al. lead with AUC; Xu et al. calibrate on clean
*source-side* data and never re-measure on a shifted collection. But
the paper must not imply the *community is unaware* thresholds drift
under shift — the OOD/conformal literature knows it well. The honest
claim is narrower: *nobody had measured it for adversarial detection on
a medical collection split, and the size of the miss (a third more
false alarms than claimed) is decision-relevant*. The current §1 mostly
stays on the right side of this line. **WATCH, minor rewording only.**

**NEAR-TAUTOLOGY CHECK** — the sharpest thing I have. Contribution 2
("a deployment-realistic fix") risks reading as: calibrating on the
deployment distribution pins the FPR on the deployment distribution.
That is true by construction. What is *not* tautological: (i) 400
images suffice; (ii) clean images alone suffice (no attack data);
(iii) the transfer error is −0.2pt vs +3.6pt, i.e., the miss was
entirely a collection effect, not a finite-sample effect. The paper
must say explicitly that the protocol is standard practice and the
contribution is the *measurement* of both failure and remedy.
**FIX-NOW.**

**STATISTICAL RESOLUTION CHECK** — the paper quotes detection gaps of
~1pt at high ε and a "crossover" of +1.4–2.9pt at low ε with NO
uncertainty quantification anywhere. At p≈0.98, n≈865–928, the 95%
binomial half-width is roughly ±1pt — the individual high-ε gaps are at
the edge of resolution, and the ε=0.05 rows (n=138) carry ±7pt. The
saving grace is consistency of sign across three ε values and both K,
and that the comparisons are *paired* (same images), which the text
never exploits. As written, observation (2) "a crossover at ε≈0.25"
overstates what one unpaired read of the table supports. **FIX-NOW:
state per-row uncertainty honestly, downgrade the crossover to a
consistent-sign observation pending a paired (McNemar-style) test on
the persisted per-image scores — which the artifact store makes free.**

**SELECTION-ARTIFACT CHECK**: The 70.3%-vs-81.6% "cost of honesty"
comparison mixes eval sets (81.6% was measured on the full 1,600-image
test at 13.6% FPR; 70.3% on the 1,200-image eval subset). Direction and
magnitude survive, but a footnote must own the mismatch. **FIX-NOW
(one sentence).** The ε=0.01 rows are kept in three tables while §6
declares them meaningless; either drop them or mark them in the tables
themselves — a reader of Table 3 alone will quote 54.2%. **FIX-NOW
(caption marks).**

**WHAT IS GENUINELY GOOD**: the audit that finds the paper's own
dataset defective and shows the conclusions survive (FPR *improves*
under exclusion) is the strongest epistemic move here; the inverted
leakage result (real images duplicated, synthetic ones clean) is
reported against the authors' own prior hypothesis, which I award
points for. The strict-dominance observation (FGSM ⊂ PGD at every ε
tested) is crisp and properly scoped.

**SCORE: 6/10** — conditioned on the near-tautology framing fix and the
statistical-resolution fix. Without them: 4.
