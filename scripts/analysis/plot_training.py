# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Plot encoder training metrics from TensorBoard logs.

Creates a 6-panel dashboard: encoder z statistics, gradient norm,
attitude error, reward, DORAEMON DR progress, and reward breakdown.

Usage:
    python scripts/analysis/plot_training.py <log_dir_or_index> [--output <path>]
    python scripts/analysis/plot_training.py 0              # latest run
    python scripts/analysis/plot_training.py /path/to/run/  # explicit path
"""

import argparse
from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

from common import load_tb_scalars, resolve_run_path, smooth

matplotlib.use("Agg")


def plot_encoder_dashboard(log_dir: str, output: str | None = None):
    data = load_tb_scalars(log_dir)
    tags = set(data.keys())

    def _steps_vals(tag):
        if tag not in data:
            return None, None
        entries = data[tag]
        return np.array([s for s, _ in entries]), np.array([v for _, v in entries])

    fig, axes = plt.subplots(3, 2, figsize=(16, 14))
    fig.suptitle(f"Encoder Training: {Path(log_dir).name}", fontsize=14, fontweight="bold")

    # -- Panel 1: Encoder z statistics --
    ax = axes[0, 0]
    for tag, label, color in [
        ("Encoder/z_mean", "z_mean", "#2196F3"),
        ("Encoder/z_std", "z_std", "#FF9800"),
        ("Encoder/z_min", "z_min", "#F44336"),
        ("Encoder/z_max", "z_max", "#4CAF50"),
    ]:
        steps, vals = _steps_vals(tag)
        if steps is not None:
            ax.plot(steps, vals, alpha=0.25, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.axhline(y=1.0, color="gray", linestyle="--", alpha=0.3, label="tanh bounds")
    ax.axhline(y=-1.0, color="gray", linestyle="--", alpha=0.3)
    ax.axhline(y=0.99, color="red", linestyle=":", alpha=0.3, label="saturation zone")
    ax.axhline(y=-0.99, color="red", linestyle=":", alpha=0.3)
    ax.set_ylabel("z value")
    ax.set_title("Encoder z Statistics")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 2: Encoder grad norm --
    ax = axes[0, 1]
    steps, vals = _steps_vals("Encoder/grad_norm")
    if steps is not None:
        ax.plot(steps, vals, alpha=0.25, color="#9C27B0", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#9C27B0", label="grad_norm", linewidth=1.5)
    ax.set_ylabel("Gradient Norm")
    ax.set_title("Encoder Gradient Norm")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 3: Attitude Error --
    ax = axes[1, 0]
    for tag, label, color in [
        ("Attitude_Error/roll_deg", "Roll Error", "#E91E63"),
        ("Attitude_Error/pitch_deg", "Pitch Error", "#3F51B5"),
    ]:
        steps, vals = _steps_vals(tag)
        if steps is not None:
            ax.plot(steps, vals, alpha=0.2, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.axhline(y=5.0, color="green", linestyle="--", alpha=0.4, label="5 deg target")
    ax.axhline(y=2.0, color="green", linestyle=":", alpha=0.4, label="2 deg target")
    ax.set_ylabel("Error (degrees)")
    ax.set_title("Attitude Error")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 4: Mean Reward --
    ax = axes[1, 1]
    for tag, label, color in [
        ("Train/mean_reward", "mean_reward", "#009688"),
        ("Episode_Reward/total", "episode_total", "#FF5722"),
    ]:
        steps, vals = _steps_vals(tag)
        if steps is not None:
            ax.plot(steps, vals, alpha=0.2, color=color, linewidth=0.5)
            ax.plot(steps, smooth(vals), color=color, label=label, linewidth=1.5)
    ax.set_ylabel("Reward")
    ax.set_title("Training Reward")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 5: DORAEMON DR progress --
    ax = axes[2, 0]
    steps, vals = _steps_vals("DORAEMON/success_rate")
    if steps is not None:
        ax.plot(steps, vals, alpha=0.2, color="#795548", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#795548", label="success_rate", linewidth=1.5)
    steps_e, vals_e = _steps_vals("DORAEMON/entropy")
    if steps_e is not None:
        ax2 = ax.twinx()
        ax2.plot(steps_e, vals_e, alpha=0.2, color="#607D8B", linewidth=0.5)
        ax2.plot(steps_e, smooth(vals_e), color="#607D8B", label="entropy", linewidth=1.5)
        ax2.set_ylabel("Entropy", color="#607D8B")
        ax2.legend(loc="lower right", fontsize=8)
    ax.set_ylabel("Success Rate", color="#795548")
    ax.set_xlabel("Iteration")
    ax.set_title("DORAEMON DR Scheduling")
    ax.legend(loc="upper left", fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 6: Reward Breakdown --
    ax = axes[2, 1]
    reward_tags = [
        ("Episode_Reward/tracking", "tracking", "#4CAF50"),
        ("Episode_Reward/settling", "settling", "#2196F3"),
        ("Episode_Reward/linear_error", "linear_error", "#F44336"),
        ("Episode_Reward/progress", "progress", "#FF9800"),
        ("Episode_Reward/joint_velocity", "joint_vel", "#9C27B0"),
        ("Episode_Reward/joint_oscillation", "joint_osc", "#795548"),
    ]
    for tag, label, color in reward_tags:
        steps, vals = _steps_vals(tag)
        if steps is not None:
            ax.plot(steps, smooth(vals, window=25), color=color, label=label, linewidth=1.2)
    ax.set_ylabel("Episode Reward Component")
    ax.set_xlabel("Iteration")
    ax.set_title("Reward Breakdown")
    ax.legend(fontsize=7, ncol=2)
    ax.grid(True, alpha=0.3)

    plt.tight_layout()

    if output is None:
        output = str(Path(log_dir) / "encoder_dashboard.png")
    plt.savefig(output, dpi=150, bbox_inches="tight")
    print(f"Saved: {output}")
    plt.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Plot encoder training dashboard")
    parser.add_argument("run", help="Path to log directory, run index (0=latest), or substring match")
    parser.add_argument("--output", "-o", help="Output image path (default: <log_dir>/encoder_dashboard.png)")
    args = parser.parse_args()

    run_path = resolve_run_path(args.run)
    print(f"[INFO] Run: {run_path}")
    plot_encoder_dashboard(str(run_path), args.output)
