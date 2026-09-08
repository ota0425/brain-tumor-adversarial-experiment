# Referee 2 — Adversarial ML (defense-evaluation school)

**SUMMARY**: FGSM-trained consistency detector on brain MRI; central
claims are about FPR calibration transfer, not robustness. PGD (random
start, α=ε/4, K∈{10,40}) evaluated at a fixed clean-calibrated
threshold; comparisons on intersections of success sets.

**THE QUESTION I ALWAYS ASK FIRST**: is there an adaptive attack? No —
and the paper says so in Limitations. For a *defense* paper that is
disqualifying; for a *measurement* paper it is survivable IF no
sentence can be quoted as a security claim. The Conclusion currently
says "our FGSM-trained consistency detector remains effective" — that
sentence, quoted alone, is a robustness claim licensed by nothing in
the paper. An attacker who knows the detector exists optimizes against
classifier+detector jointly, and consistency features of exactly this
kind (squeezing-based) have been broken adaptively before. **FIX-NOW:
qualify every effectiveness statement with "against the non-adaptive
attacks evaluated here" and say once, plainly, that adaptive
evaluation is required before any defensive deployment claim.**

**BUDGET UNITS**: ε on a 0–255 scale is nonstandard and will confuse
every reader used to L∞ on [0,1]. ε=1 here is ≈0.0039 normalized
(1/255); ε=0.05 is ≈2×10⁻⁴ — genuinely tiny budgets, which makes the
95–100% attack success MORE alarming, not less, and the paper never
cashes that in. **FIX-NOW: one footnote with the conversion.** Related:
the ε=0.01 sub-quantization observation is correct and I appreciate a
paper that says its smallest setting is physically meaningless — but
then the tables must carry the mark, not just §6.

**PGD COMPETENCE CHECK**: random start, α=ε/4, K=10 vs 40 nearly
identical → converged; per-batch ball assertions; strict dominance over
FGSM at every tested ε (consistent with FGSM's known one-step
suboptimality at small budgets; note the paper's own coarse-sweep data
show FGSM success *decreasing* at ε=8, so dominance must stay scoped to
tested ε — it is). No restarts beyond the random start: acceptable at
these success rates. Configuration is competent.

**DETECTOR SIDE**: training positives = successful attacks only is a
sensible label definition for the stated threat model and is honestly
inherited from the feature-squeezing lineage. No gradient masking
concern arises because the detector never enters any attack loop —
which is precisely why the non-adaptive caveat above is load-bearing.

**STATISTICS**: same complaint as Referee 1, from my side of the fence:
detection-rate differences of ~1pt at n≈900 and ~3pt at n≈138–307 are
quoted without intervals. The comparisons are paired on identical
images; a McNemar-style test from the persisted per-image outputs would
settle the crossover claim at zero GPU cost. Until then the crossover
is an observation, not a finding. **FIX-NOW wording; RUN-LATER test.**

**WHAT I LIKE**: the intersection protocol is exactly the right answer
to the changing-denominator confound and I would like to see it become
standard; the persisted per-image score/mask store is how these
evaluations should always ship; the calibration-sensitivity analysis
(re-deriving the threshold from the cleaned calibration set) tests the
mechanism, not just the number.

**SCORE: 6/10** — the measurement core is solid and the artifact trail
is exemplary; the score is conditioned on the robustness-claim
qualifiers and the units footnote. If any effectiveness sentence
survives unqualified: 3.
