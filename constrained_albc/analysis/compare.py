# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Comparison plots for ALBC evals (pure Python, no Isaac Sim).

Subcommands:
    dr      --dirs --labels --output   multi-policy eval_dr .npz comparison plot

Usage:
    python3 constrained_albc/analysis/compare.py dr --dirs A/ts B/ts --labels A B --output cmp.png
"""

from __future__ import annotations

import argparse
import os

import matplotlib
import matplotlib.pyplot as plt
import numpy as np
from common import DR_LEVELS, DR_SCALE
from matplotlib.ticker import MultipleLocator

matplotlib.use("Agg")


# ---------------------------------------------------------------------------
# dr helpers (verbatim from compare_dr.py)
# ---------------------------------------------------------------------------


def load_eval_data(eval_dir: str) -> dict[str, dict]:
    """Load all DR level .npz files from an eval directory."""
    data = {}
    for level in DR_LEVELS:
        path = os.path.join(eval_dir, f"data_{level}.npz")
        if os.path.exists(path):
            data[level] = dict(np.load(path, allow_pickle=True))
    return data


def compute_level_metrics(d: dict) -> dict:
    """Compute summary metrics for one DR level.

    Steady-state error uses per-segment last-50% averaging (matching eval.py).

    See TODO(metric-drift) in _analyze/recompute_metrics.py: this is one of three
    drifted, non-byte-equivalent duplicates of this metric logic -- do not merge
    without a before/after numeric-equivalence check.
    """
    error_roll = d["error_roll"]
    error_pitch = d["error_pitch"]
    terminated = d["terminated"]
    alive = ~terminated
    num_envs = error_roll.shape[1]

    error_norm = np.sqrt(error_roll**2 + error_pitch**2)

    total_mean = float(np.nanmean(np.where(alive, error_norm, np.nan))) if alive.any() else float("nan")
    survival = float(alive[-1].sum()) / num_envs * 100.0

    # Steady-state: per-segment last 50% averaging (consistent with eval.py)
    seg_steps = int(d["steps_per_segment"]) if "steps_per_segment" in d else 0
    if seg_steps > 0:
        num_segments = error_norm.shape[0] // seg_steps
        ss_errors = []
        for seg_idx in range(num_segments):
            s = seg_idx * seg_steps
            e = (seg_idx + 1) * seg_steps
            ss_start = s + int(seg_steps * 0.5)
            seg_ss = error_norm[ss_start:e]
            seg_alive = alive[ss_start:e]
            if seg_alive.any():
                ss_errors.append(float(np.nanmean(np.where(seg_alive, seg_ss, np.nan))))
        ss_mean = float(np.nanmean(ss_errors)) if ss_errors else float("nan")
    else:
        # Fallback for old .npz files without steps_per_segment
        ss_start = error_norm.shape[0] // 2
        ss_err = error_norm[ss_start:]
        ss_alive = alive[ss_start:]
        ss_mean = float(np.nanmean(np.where(ss_alive, ss_err, np.nan))) if ss_alive.any() else float("nan")

    return {"total_mean": total_mean, "ss_mean": ss_mean, "survival": survival}


def align_time_ranges(all_policy_data: dict, labels: list[str]) -> None:
    """Downsample longer datasets to match shortest, in place."""
    for lvl in DR_LEVELS:
        datasets = [(lbl, all_policy_data[lbl][lvl]) for lbl in labels if lvl in all_policy_data[lbl]]
        if len(datasets) < 2:
            continue
        min_steps = min(d["time"].shape[0] for _, d in datasets)
        for _lbl, d in datasets:
            n = d["time"].shape[0]
            if n > min_steps:
                end_time = d["time"][-1]
                ratio = n // min_steps
                for key in d:
                    arr = d[key]
                    if isinstance(arr, np.ndarray) and arr.shape[0] == n:
                        d[key] = arr[::ratio]
                d["time"] = np.linspace(0, end_time, len(d["time"]))


# ---------------------------------------------------------------------------
# Subcommand implementations
# ---------------------------------------------------------------------------


def cmd_dr(args: argparse.Namespace) -> None:
    """Multi-policy eval_dr .npz comparison plot."""
    assert len(args.dirs) == len(args.labels), "--dirs and --labels must have same length"

    POLICY_COLORS = ["#2196F3", "#F44336", "#4CAF50", "#FF9800"]
    POLICY_LINESTYLES = ["-", "--", "-.", ":"]

    labels = args.labels
    all_policy_data: dict[str, dict] = {}
    for label, eval_dir in zip(labels, args.dirs):
        all_policy_data[label] = load_eval_data(eval_dir)

    align_time_ranges(all_policy_data, labels)

    all_policy_metrics = {
        label: {lvl: compute_level_metrics(d) for lvl, d in all_policy_data[label].items()} for label in labels
    }

    levels = [lvl for lvl in DR_LEVELS if all(lvl in all_policy_data[lbl] for lbl in labels)]
    dr_pct = {lvl: int(DR_SCALE[lvl] * 100) for lvl in levels}

    # ---- Figure 1: Tracking error per DR level, policies overlaid ----
    fig1, axes1 = plt.subplots(len(levels), 2, figsize=(18, 3.5 * len(levels)), sharex=True)
    fig1.suptitle("Tracking Error: Policy Comparison across DR Levels", fontsize=14, y=0.99)

    for row, lvl in enumerate(levels):
        for pid, label in enumerate(labels):
            d = all_policy_data[label][lvl]
            color = POLICY_COLORS[pid % len(POLICY_COLORS)]
            ls = POLICY_LINESTYLES[pid % len(POLICY_LINESTYLES)]
            time_s = d["time"]
            alive = ~d["terminated"]

            for col, (err_key, tgt_key, axis_name) in enumerate(
                [
                    ("error_roll", "target_roll_deg", "Roll Error (deg)"),
                    ("error_pitch", "target_pitch_deg", "Pitch Error (deg)"),
                ]
            ):
                ax = axes1[row, col] if len(levels) > 1 else axes1[col]
                err_vals = np.where(alive, np.abs(d[err_key]), np.nan)
                mean = np.nanmean(err_vals, axis=1)
                std = np.nanstd(err_vals, axis=1)
                ax.plot(time_s, mean, color=color, linestyle=ls, linewidth=1.2, label=label)
                ax.fill_between(time_s, mean - std, mean + std, color=color, alpha=0.08)

                if pid == 0:
                    ax.plot(time_s, np.abs(d[tgt_key]), "k--", linewidth=0.8, alpha=0.3, label="target")

                ax.set_ylabel(axis_name, fontsize=9)
                ax.yaxis.set_major_locator(MultipleLocator(15))
                ax.grid(True, alpha=0.3)
                if col == 0:
                    ax.set_title(f"DR {dr_pct[lvl]}% ({lvl})", fontsize=11, fontweight="bold")
                if row == len(levels) - 1:
                    ax.set_xlabel("Time (s)")

    fig1.tight_layout()

    # ---- Figure 2: Summary bar charts (grouped bars) ----
    fig2, axes2 = plt.subplots(1, 3, figsize=(16, 5))
    fig2.suptitle("DR Robustness Comparison", fontsize=14)

    x = np.arange(len(levels))
    n_policies = len(labels)
    bar_width = 0.8 / n_policies

    metric_configs = [
        ("total_mean", "Total Mean Error (deg)", None),
        ("ss_mean", "Steady-State Error (deg)", None),
        ("survival", "Survival Rate (%)", (0, 105)),
    ]

    for ax_idx, (metric_key, ylabel, ylim) in enumerate(metric_configs):
        ax = axes2[ax_idx]
        for pid, label in enumerate(labels):
            vals = [all_policy_metrics[label][lvl][metric_key] for lvl in levels]
            color = POLICY_COLORS[pid % len(POLICY_COLORS)]
            offset = (pid - n_policies / 2 + 0.5) * bar_width
            bars = ax.bar(x + offset, vals, bar_width * 0.9, color=color, label=label, alpha=0.85)
            for bar, val in zip(bars, vals):
                if not np.isnan(val):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f"{val:.1f}",
                        ha="center",
                        va="bottom",
                        fontsize=7,
                    )
        ax.set_xticks(x)
        ax.set_xticklabels([f"{lvl}\n(DR {dr_pct[lvl]}%)" for lvl in levels], fontsize=9)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, axis="y")
        if ylim:
            ax.set_ylim(*ylim)

    fig2.tight_layout()

    # ---- Figure 3: Actual tracking per DR level ----
    fig3, axes3 = plt.subplots(len(levels), 2, figsize=(18, 3.5 * len(levels)), sharex=True)
    fig3.suptitle("Actual Tracking: Policy Comparison across DR Levels", fontsize=14, y=0.99)

    for row, lvl in enumerate(levels):
        for pid, label in enumerate(labels):
            d = all_policy_data[label][lvl]
            color = POLICY_COLORS[pid % len(POLICY_COLORS)]
            ls = POLICY_LINESTYLES[pid % len(POLICY_LINESTYLES)]
            time_s = d["time"]
            alive = ~d["terminated"]

            for col, (actual_key, tgt_key, axis_name) in enumerate(
                [
                    ("actual_roll_deg", "target_roll_deg", "Roll (deg)"),
                    ("actual_pitch_deg", "target_pitch_deg", "Pitch (deg)"),
                ]
            ):
                ax = axes3[row, col] if len(levels) > 1 else axes3[col]
                vals = np.where(alive, d[actual_key], np.nan)
                mean = np.nanmean(vals, axis=1)
                std = np.nanstd(vals, axis=1)
                ax.plot(time_s, mean, color=color, linestyle=ls, linewidth=1.2, label=label)
                ax.fill_between(time_s, mean - std, mean + std, color=color, alpha=0.08)

                if pid == 0:
                    ax.plot(time_s, d[tgt_key], "k--", linewidth=1.0, alpha=0.5, label="target")

                ax.set_ylabel(axis_name, fontsize=9)
                ax.yaxis.set_major_locator(MultipleLocator(15))
                ax.grid(True, alpha=0.3)
                if col == 0:
                    ax.set_title(f"DR {dr_pct[lvl]}% ({lvl})", fontsize=11, fontweight="bold")
                if row == len(levels) - 1:
                    ax.set_xlabel("Time (s)")

    fig3.tight_layout()

    # ---- Save ----
    if args.output:
        output_base = args.output.rsplit(".", 1)[0] if "." in args.output else args.output
    else:
        output_base = os.path.join(os.path.dirname(args.dirs[0]), "comparison")

    os.makedirs(os.path.dirname(output_base) or ".", exist_ok=True)

    fig1.savefig(f"{output_base}_error.png", dpi=150)
    fig2.savefig(f"{output_base}_summary.png", dpi=150)
    fig3.savefig(f"{output_base}_tracking.png", dpi=150)
    plt.close("all")

    print(f"Saved: {output_base}_error.png")
    print(f"Saved: {output_base}_summary.png")
    print(f"Saved: {output_base}_tracking.png")

    # ---- Console table ----
    print(f"\n{'':>20} ", end="")
    for lvl in levels:
        print(f"{'DR ' + str(dr_pct[lvl]) + '%':>14}", end="")
    print()

    for metric_key, metric_label in [
        ("total_mean", "Mean Error (deg)"),
        ("ss_mean", "SS Error (deg)"),
        ("survival", "Survival (%)"),
    ]:
        for label in labels:
            print(f"  {label + ' ' + metric_label:>38} ", end="")
            for lvl in levels:
                val = all_policy_metrics[label][lvl][metric_key]
                print(f"{val:13.1f}", end="")
            print()
        print()



# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Comparison plots for ALBC evals (pure Python, no Isaac Sim)."
    )
    sub = parser.add_subparsers(dest="mode", required=True)

    # -- dr --
    p_dr = sub.add_parser("dr", help="Multi-policy eval_dr .npz comparison plot.")
    p_dr.add_argument("--dirs", nargs="+", required=True, help="eval_dr output directories")
    p_dr.add_argument("--labels", nargs="+", required=True, help="Labels for each directory")
    p_dr.add_argument("--output", type=str, default=None, help="Output path prefix (default: auto)")
    p_dr.set_defaults(func=cmd_dr)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
