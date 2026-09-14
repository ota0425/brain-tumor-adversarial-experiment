# Meeting Record — 2026-09-04

> Historical meeting record. The checkpoint values and pending tasks below
> describe the state on 4 September, not the final published rerun. For the
> final results, see the root README and `docs/HANDOFF.md` (15 September update).

## Instruction from Mr. Surasak

The student's immediate task is to rerun the Python files prepared by Mr. Surasak and verify whether the reproduced results match the results reported in the paper.

## Required work

1. Use the scripts in `ThammasatResearch/rerun/`.
2. Run the main pipeline in the documented order, beginning with `01_train_classifier.py`.
3. Preserve the generated models, manifest, CSV files, thresholds, figures, and execution logs.
4. Compare the reproduced values with `papers/adversarial-mri-detection/paper.tex` and the reference artifacts in `papers/adversarial-mri-detection/exp1/`.
5. Record each result as matched, within an explicitly stated tolerance, or mismatched.
6. If an early checkpoint differs, stop and investigate the environment, dataset hash, model hash, seed, and dependency versions before running downstream stages.
7. Report any mismatch to Mr. Surasak. Do not silently change the paper to fit a new result.

## First checkpoint

The first required checkpoint is the classifier's clean test accuracy:

~~~text
Expected: 0.81875 (1,310 / 1,600)
~~~

If this value is not reproduced within the pipeline's permitted tolerance, later FGSM, detector, calibration, and PGD results must not be treated as a valid reproduction of the paper.

## Scope

The current assignment is reproduction and verification. Adding a new model, changing the method, or improving the paper is secondary and should not be done before the rerun comparison is complete.
