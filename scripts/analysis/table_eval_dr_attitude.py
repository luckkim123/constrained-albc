"""Render Table 1 (attitude SS error under DR) as paper-style image (PNG)."""
from __future__ import annotations

import json
import os

import matplotlib.pyplot as plt
import matplotlib as mpl

TDC = "/workspace/isaaclab/logs/rsl_rl/full_dof_tdc/classical_baseline/eval_dr/enhanced_summary.json"
V5  = "/workspace/isaaclab/logs/rsl_rl/full_dof_ablation/2026-04-22_01-41-00_ablation_v5_pureppo/eval_dr/enhanced_summary.json"
R13 = "/workspace/isaaclab/logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/eval_dr/enhanced_summary.json"

OUT = "/workspace/isaaclab/logs/rsl_rl/full_dof_tdc/classical_baseline/table1_eval_dr_attitude.png"


def main():
    tdc = json.load(open(TDC))
    v5 = json.load(open(V5))
    r13 = json.load(open(R13))

    levels = ["none", "soft", "medium", "hard"]
    controllers = [
        ("TDC+PD",                  tdc, "#C74E47"),
        ("PurePPO (no enc, no IPO)", v5,  "#2E7D32"),
        ("r13_A (RL+Encoder)",       r13, "#1565C0"),
    ]

    def cell(d, axis, key="ss_error"):
        return d[axis][key], d[axis][key + "_std"]

    # Build table rows
    header_top = ["DR", "Controller", "Roll  SS err (deg)", "Pitch  SS err (deg)"]
    rows, best_mask = [], []  # best_mask[i] = list of bool per cell in row (for bold)
    for lvl in levels:
        # Determine best (min mean) per axis across controllers for this DR
        roll_means = [cell(d[lvl], "roll")[0] for _, d, _ in controllers]
        pitch_means = [cell(d[lvl], "pitch")[0] for _, d, _ in controllers]
        best_roll_idx = roll_means.index(min(roll_means))
        best_pitch_idx = pitch_means.index(min(pitch_means))

        for ci, (name, d, _) in enumerate(controllers):
            roll_m, roll_s = cell(d[lvl], "roll")
            pitch_m, pitch_s = cell(d[lvl], "pitch")
            roll_str = f"{roll_m:.2f} ± {roll_s:.2f}"
            pitch_str = f"{pitch_m:.2f} ± {pitch_s:.2f}"
            # Only first row of each DR block prints the DR label
            dr_cell = lvl if ci == 0 else ""
            rows.append([dr_cell, name, roll_str, pitch_str])
            best_mask.append([False, False, ci == best_roll_idx, ci == best_pitch_idx])

    # Render
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["mathtext.fontset"] = "stix"
    fig_w, fig_h = 9.5, 0.50 + 0.44 * (len(rows) + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    table = ax.table(
        cellText=[header_top] + rows,
        cellLoc="center",
        colWidths=[0.08, 0.35, 0.27, 0.27],
        loc="center",
        edges="open",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 1.55)

    n_rows = len(rows) + 1  # incl. header
    for (r, c), cell_obj in table.get_celld().items():
        cell_obj.set_edgecolor("none")
        cell_obj.set_linewidth(0)
        # Top rule above header, midrule below header, bottom rule at bottom
        if r == 0:
            cell_obj.set_text_props(weight="bold")
            cell_obj.visible_edges = "TB"
            cell_obj.set_linewidth(1.2)
        elif r == n_rows - 1:
            cell_obj.visible_edges = "B"
            cell_obj.set_linewidth(1.2)
        # Bold best values
        if r > 0 and best_mask[r - 1][c]:
            cell_obj.set_text_props(weight="bold")
        # DR block separators: draw a light line above first row of each block (ci==0)
        if r > 0 and (r - 1) % 3 == 0 and r != 1:
            cell_obj.visible_edges = "T"
            cell_obj.set_linewidth(0.5)
            cell_obj.set_edgecolor("#AAAAAA")

    # Title
    fig.suptitle(
        "Table 1. Attitude steady-state error under domain randomization\n"
        "(deg, mean ± std across 64 environments; lower is better)",
        fontsize=11, y=0.98, weight="bold",
    )

    # Caveat note
    fig.text(
        0.5, 0.02,
        "Note: TDC uses single-step DLS IK (compute-matched fairness). Bold = best per DR level per axis.",
        ha="center", fontsize=8.5, style="italic", color="#555555",
    )

    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved: {OUT}")


if __name__ == "__main__":
    main()
