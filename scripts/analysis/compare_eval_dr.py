"""Compare eval_dr results from two different policies side-by-side.

Usage:
    python scripts/analysis/compare_eval_dr.py \
        --dirs logs/eval_dr/heroagent_encoder_base/2026-03-03_10-26-27 \
              logs/eval_dr/heroagent_tdc/2026-03-03_10-31-49 \
        --labels "Encoder-Base" "TDC" \
        --output logs/eval_dr/comparison_encoder_vs_tdc.png
"""

import argparse
import os

import matplotlib
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np

matplotlib.use("Agg")

DR_LEVELS = ["none", "soft", "medium", "hard"]
DR_SCALE = {"none": 0, "soft": 30, "medium": 60, "hard": 100}


def load_eval_data(eval_dir: str) -> dict[str, dict]:
    """Load all DR level .npz files from an eval directory."""
    data = {}
    for level in DR_LEVELS:
        path = os.path.join(eval_dir, f"eval_{level}.npz")
        if os.path.exists(path):
            data[level] = dict(np.load(path, allow_pickle=True))
    return data


def compute_level_metrics(d: dict) -> dict:
    """Compute summary metrics for one DR level."""
    error_roll = d["error_roll"]
    error_pitch = d["error_pitch"]
    terminated = d["terminated"]
    alive = ~terminated
    num_envs = error_roll.shape[1]

    error_norm = np.sqrt(error_roll**2 + error_pitch**2)

    total_mean = float(np.nanmean(np.where(alive, error_norm, np.nan))) if alive.any() else float("nan")
    survival = float(alive[-1].sum()) / num_envs * 100.0

    # Steady-state: last 50% of entire trajectory
    ss_start = error_norm.shape[0] // 2
    ss_err = error_norm[ss_start:]
    ss_alive = alive[ss_start:]
    ss_mean = float(np.nanmean(np.where(ss_alive, ss_err, np.nan))) if ss_alive.any() else float("nan")

    return {"total_mean": total_mean, "ss_mean": ss_mean, "survival": survival}


def main():
    parser = argparse.ArgumentParser(description="Compare eval_dr results from multiple policies.")
    parser.add_argument("--dirs", nargs="+", required=True, help="eval_dr output directories")
    parser.add_argument("--labels", nargs="+", required=True, help="Labels for each directory")
    parser.add_argument("--output", type=str, default=None, help="Output path (default: auto)")
    args = parser.parse_args()

    assert len(args.dirs) == len(args.labels), "--dirs and --labels must have same length"

    # Policy colors (up to 4 policies)
    POLICY_COLORS = ["#2196F3", "#F44336", "#4CAF50", "#FF9800"]
    POLICY_LINESTYLES = ["-", "--", "-.", ":"]

    labels = args.labels
    all_policy_data = {}
    all_policy_metrics = {}
    for label, eval_dir in zip(labels, args.dirs):
        all_policy_data[label] = load_eval_data(eval_dir)

    # Align time ranges: downsample longer datasets by 2x to match shortest
    for lvl in DR_LEVELS:
        datasets = [(l, all_policy_data[l][lvl]) for l in labels if lvl in all_policy_data[l]]
        if len(datasets) < 2:
            continue
        min_steps = min(d["time"].shape[0] for _, d in datasets)
        for l, d in datasets:
            n = d["time"].shape[0]
            if n > min_steps:
                ratio = n // min_steps
                for key in d:
                    arr = d[key]
                    if isinstance(arr, np.ndarray) and arr.shape[0] == n:
                        d[key] = arr[::ratio]
                # Rescale time to match shorter range
                d["time"] = np.linspace(0, datasets[0][1]["time"][-1], len(d["time"]))

    for label in labels:
        all_policy_metrics[label] = {
            lvl: compute_level_metrics(d) for lvl, d in all_policy_data[label].items()
        }

    levels = [lvl for lvl in DR_LEVELS if all(lvl in all_policy_data[l] for l in labels)]

    # ---- Figure 1: Tracking error over time (per DR level, policies overlaid) ----
    fig1, axes1 = plt.subplots(len(levels), 2, figsize=(18, 3.5 * len(levels)), sharex=True)
    fig1.suptitle("Tracking Error: Policy Comparison across DR Levels", fontsize=14, y=0.99)

    for row, lvl in enumerate(levels):
        dr_pct = DR_SCALE[lvl]
        for pid, label in enumerate(labels):
            d = all_policy_data[label][lvl]
            color = POLICY_COLORS[pid % len(POLICY_COLORS)]
            ls = POLICY_LINESTYLES[pid % len(POLICY_LINESTYLES)]
            time_s = d["time"]
            alive = ~d["terminated"]

            for col, (err_key, tgt_key, axis_name) in enumerate([
                ("error_roll", "target_roll_deg", "Roll Error (deg)"),
                ("error_pitch", "target_pitch_deg", "Pitch Error (deg)"),
            ]):
                ax = axes1[row, col] if len(levels) > 1 else axes1[col]
                err_vals = np.where(alive, np.abs(d[err_key]), np.nan)
                mean = np.nanmean(err_vals, axis=1)
                std = np.nanstd(err_vals, axis=1)

                ax.plot(time_s, mean, color=color, linestyle=ls, linewidth=1.2, label=label)
                ax.fill_between(time_s, mean - std, mean + std, color=color, alpha=0.08)

                # Target reference (only once per subplot)
                if pid == 0:
                    ax.plot(time_s, np.abs(d[tgt_key]), "k--", linewidth=0.8, alpha=0.3, label="target")

                ax.set_ylabel(axis_name, fontsize=9)
                ax.yaxis.set_major_locator(MultipleLocator(15))
                ax.grid(True, alpha=0.3)

                if col == 0:
                    ax.set_title(f"DR {dr_pct}% ({lvl})", fontsize=11, fontweight="bold")
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
            # Value labels on bars
            for bar, val in zip(bars, vals):
                if not np.isnan(val):
                    ax.text(
                        bar.get_x() + bar.get_width() / 2,
                        bar.get_height() + 0.3,
                        f"{val:.1f}",
                        ha="center", va="bottom", fontsize=7,
                    )

        ax.set_xticks(x)
        ax.set_xticklabels([f"{lvl}\n(DR {DR_SCALE[lvl]}%)" for lvl in levels], fontsize=9)
        ax.set_ylabel(ylabel)
        ax.grid(True, alpha=0.3, axis="y")
        if ylim:
            ax.set_ylim(*ylim)

    fig2.tight_layout()

    # ---- Figure 3: Actual tracking (roll/pitch) per DR level ----
    fig3, axes3 = plt.subplots(len(levels), 2, figsize=(18, 3.5 * len(levels)), sharex=True)
    fig3.suptitle("Actual Tracking: Policy Comparison across DR Levels", fontsize=14, y=0.99)

    for row, lvl in enumerate(levels):
        dr_pct = DR_SCALE[lvl]
        for pid, label in enumerate(labels):
            d = all_policy_data[label][lvl]
            color = POLICY_COLORS[pid % len(POLICY_COLORS)]
            ls = POLICY_LINESTYLES[pid % len(POLICY_LINESTYLES)]
            time_s = d["time"]
            alive = ~d["terminated"]

            for col, (actual_key, tgt_key, axis_name) in enumerate([
                ("actual_roll_deg", "target_roll_deg", "Roll (deg)"),
                ("actual_pitch_deg", "target_pitch_deg", "Pitch (deg)"),
            ]):
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
                    ax.set_title(f"DR {dr_pct}% ({lvl})", fontsize=11, fontweight="bold")
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
        print(f"{'DR ' + str(DR_SCALE[lvl]) + '%':>14}", end="")
    print()

    for metric_key, metric_label in [("total_mean", "Mean Error (deg)"), ("ss_mean", "SS Error (deg)"), ("survival", "Survival (%)")]:
        for label in labels:
            print(f"  {label + ' ' + metric_label:>38} ", end="")
            for lvl in levels:
                val = all_policy_metrics[label][lvl][metric_key]
                print(f"{val:13.1f}", end="")
            print()
        print()


if __name__ == "__main__":
    main()
