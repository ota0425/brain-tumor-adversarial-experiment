# Referee 3 — Medical Imaging AI (clinical deployment)

**SUMMARY**: Calibration-transfer study for adversarial detection on the
Kaggle brain-tumor composite; includes a dataset audit (duplication,
synthetic padding, banner subpopulation) and a clean-images-only
deployment calibration protocol.

**THREAT MODEL**: the paper jumps straight to FGSM/PGD without one
sentence on *why* someone attacks an MRI classifier (insurance fraud,
trial manipulation, sabotage — the standard motivations are in
Finlayson et al., Science 2019). MICAD readers are clinicians and
engineers, not security people; the motivation paragraph is missing.
**FIX-NOW: two sentences + citation.**

**THE CLASSIFIER IS NOT A CLINICAL TOOL** and the paper never says so.
81.9% accuracy with meningioma at 64% would be malpractice as a
deployed diagnostic; as a *testbed* for the calibration question it is
fine. One sentence declaring the testbed status prevents the worst
possible misreading of this paper by a clinical reader. **FIX-NOW.**
Related: the audit's glioma-banner collapse (15% on flagged images) is
the paper's most clinically interesting number — a deployed model can
fail on an identifiable acquisition subpopulation while aggregate
accuracy looks acceptable — and the text could point that moral out in
one line.

**THE 10% FPR BUDGET IS UNJUSTIFIED**: in a reading-room workflow, a
10% per-scan false-alarm rate is a large operational cost. I accept it
as an illustrative budget — the transfer *failure* is budget-
independent — but the paper should say the budget is illustrative and
that the protocol pins whatever budget the site chooses (the 7.5%
margin variant already gestures at this). **FIX-NOW (one sentence).**

**CALIBRATION ASSUMPTION NOBODY STATES**: the 400 calibration images
are assumed attack-free. If an adversary can poison the calibration
set, the threshold moves at their discretion. In-hospital this is a
real question (who collects those 400 scans, from which PACS, audited
how?). The protocol survives the assumption being *stated*; it does not
survive it being *silent*. **FIX-NOW.**

**DATASET**: the audit is the best part of the paper for this venue —
this composite is used in hundreds of student papers and nobody checks
it. Duplication measured at the pixel level (not perceptual hash — the
false-alarm anecdote is worth keeping in the artifact trail), synthetic
padding disclosed, banner shift quantified per class. Two demands:
(i) the dataset citation is currently [NEEDS] — for a venue submission
this is not optional, and given the audit findings the provenance
paragraph must name the composite's constituent sources; (ii) the
figure exemplars were screened for watermarks/branding — good — but
camera-ready must use the full-resolution originals, and the caption
should keep the screening statement (it is a licensing defence).
**FIX-BEFORE-SUBMIT (human task), not fixable by the text alone.**

**FIGURE 1**: legible, correct, and the amplified-perturbation column
is honestly labelled. The coronal pituitary exemplar next to axial
slices will make a radiologist blink; acceptable for a computer-science
venue.

**SCORE: 5/10 as submitted → 6/10 with the four FIX-NOW sentences.**
The calibration message is genuinely useful to this community; the
missing clinical framing is what holds the score down, and it is cheap
to add.
