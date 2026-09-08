"""Generate the paper's figures from the exp1 CSVs (clean-rerun era only).

Fig 1 (fig_fpr_transfer.pdf): claimed vs achieved FPR under the three
calibration strategies — the paper's lead result.
Fig 2 (fig_attack_detection.pdf): attack success and intersection
detection rates vs epsilon for FGSM / PGD-10 / PGD-40 at the pinned
deployment threshold.

Colors are the Okabe–Ito CVD-safe subset; series also differ by marker
and linestyle so the figures survive grayscale printing.
"""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = Path(__file__).parent
C_FGSM, C_PGD10, C_PGD40 = "#0072B2", "#E69F00", "#009E73"
plt.rcParams.update({"font.size": 9, "axes.titlesize": 10})

inter = pd.read_csv(HERE / "attack_intersection_analysis.csv")
cal = json.loads((HERE / "deployment_calibration_threshold.json").read_text())

EPS = sorted(inter["epsilon"].unique())
p10 = inter[inter["pair"] == "fgsm_vs_pgd10"].set_index("epsilon").loc[EPS]
p40 = inter[inter["pair"] == "fgsm_vs_pgd40"].set_index("epsilon").loc[EPS]
N_INITIALLY_CORRECT = 979  # eval-1200 subset, from the intersection CSV context

# ---- Fig 1: FPR transfer -------------------------------------------------
strategies = [
    ("Validation (1,120 imgs,\nalso used for selection)", 0.135625),
    ("Leakage-free split\n(560 imgs, val_B)", 0.154375),
    ("Deployment calibration\n(400 clean test-side imgs)", cal["eval_clean_fpr"]),
]
fig, ax = plt.subplots(figsize=(4.6, 2.2))
labels = [s[0] for s in strategies]
values = [s[1] * 100 for s in strategies]
colors = ["#8A9BA6", "#8A9BA6", C_FGSM]
bars = ax.barh(range(len(values))[::-1], values, color=colors, height=0.55)
for y, v in zip(range(len(values))[::-1], values):
    ax.text(v + 0.25, y, f"{v:.1f}%", va="center", fontsize=9)
ax.axvline(10, color="#444444", linestyle="--", linewidth=1)
ax.text(10.1, 2.42, "10% budget", fontsize=8, color="#444444")
ax.set_yticks(range(len(labels))[::-1], labels)
ax.set_xlabel("Achieved clean false-positive rate on test (%)")
ax.set_xlim(0, 18)
ax.spines[["top", "right"]].set_visible(False)
fig.tight_layout()
fig.savefig(HERE / "fig_fpr_transfer.pdf")
print("saved fig_fpr_transfer.pdf")

# ---- Fig 2: attack success + intersection detection ----------------------
fig, axes = plt.subplots(1, 2, figsize=(9.2, 2.9))

series = [
    ("FGSM", C_FGSM, "o", "-",
     p10["n_fgsm_success"] / N_INITIALLY_CORRECT,
     p10["det_fgsm_on_intersection"]),
    ("PGD-10", C_PGD10, "s", "--",
     p10["n_pgd_success"] / N_INITIALLY_CORRECT,
     p10["det_pgd_on_intersection"]),
    ("PGD-40", C_PGD40, "^", ":",
     p40["n_pgd_success"] / N_INITIALLY_CORRECT,
     p40["det_pgd_on_intersection"]),
]
for name, color, marker, ls, success, _ in series:
    axes[0].plot(EPS, success, color=color, marker=marker, linestyle=ls,
                 markersize=5, linewidth=1.6, label=name)
axes[0].set_title("Attack success rate")
axes[0].set_ylabel("Successful attacks / initially correct")
for name, color, marker, ls, _, det in series:
    axes[1].plot(EPS, det, color=color, marker=marker, linestyle=ls,
                 markersize=5, linewidth=1.6, label=name)
axes[1].set_title("Detection on the intersection of success sets")
axes[1].set_ylabel(f"Detection rate (clean FPR {cal['eval_clean_fpr']*100:.1f}%)")
for ax in axes:
    ax.set_xscale("log")
    ax.set_xticks(EPS, [str(e) for e in EPS])
    ax.set_xlabel(r"$\varepsilon$ (0–255 input scale, log axis)")
    ax.set_ylim(0, 1.02)
    ax.grid(True, linewidth=0.4, alpha=0.5)
    ax.spines[["top", "right"]].set_visible(False)
    ax.legend(frameon=False, fontsize=8)
fig.tight_layout()
fig.savefig(HERE / "fig_attack_detection.pdf")
print("saved fig_attack_detection.pdf")
