# Professor-provided rerun workspace

`ThammasatResearch` is the name of the workspace supplied by Surasak Phetmanee and used in Google Drive during the study. It is retained here to make the repository's source material and the Colab paths easy to match. This directory is part of the same research project, not a separate repository.

| Path | What it contains |
|---|---|
| [`rerun/`](rerun/) | Staged Python scripts for classifier training, FGSM and PGD evaluation, detector calibration, and dataset audits. Start with its [`README.md`](rerun/README.md). |
| `Adversarial MRI Rerun.pdf` | Professor-provided explanation of the rerun and audit. |
| `Rerun pipeline — student run guide.pdf` | Original student-facing run guide. Its earlier checkpoint values may differ from the final published rerun. |

The final reported execution used [`../rerun_colab.ipynb`](../rerun_colab.ipynb), which expects the scripts under `MyDrive/ThammasatResearch/rerun/` in Google Drive. The dataset, model checkpoints, and result files are deliberately not stored in this GitHub directory. The fixed final versions of the scripts, checkpoints, and outputs are in the [Zenodo reproducibility package](https://doi.org/10.5281/zenodo.22682676).

For the final paper numbers, follow the root [README](../README.md) and the Zenodo `results/PROVENANCE.md`. The original guide PDFs are preserved for provenance, not as current numerical specifications.
