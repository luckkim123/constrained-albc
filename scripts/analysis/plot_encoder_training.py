"""Plot encoder training metrics from TensorBoard logs.

Creates a comprehensive dashboard with encoder z statistics, training performance,
attitude error, DORAEMON DR progress, and reward breakdown.

Usage:
    python scripts/analysis/plot_encoder_training.py <log_dir> [--output <path>]
"""

import argparse
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from tensorboard.backend.event_processing.event_accumulator import EventAccumulator


def load_scalars(ea: EventAccumulator, tag: str):
    """Extract steps and values from a TensorBoard scalar tag."""
    events = ea.Scalars(tag)
    steps = np.array([e.step for e in events])
    values = np.array([e.value for e in events])
    return steps, values


def smooth(values: np.ndarray, window: int = 15) -> np.ndarray:
    """Simple moving average smoothing."""
    if len(values) < window:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")


def plot_encoder_dashboard(log_dir: str, output: str | None = None):
    ea = EventAccumulator(log_dir)
    ea.Reload()
    tags = set(ea.Tags()["scalars"])

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
        if tag in tags:
            steps, vals = load_scalars(ea, tag)
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
    if "Encoder/grad_norm" in tags:
        steps, vals = load_scalars(ea, "Encoder/grad_norm")
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
        if tag in tags:
            steps, vals = load_scalars(ea, tag)
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
    if "Train/mean_reward" in tags:
        steps, vals = load_scalars(ea, "Train/mean_reward")
        ax.plot(steps, vals, alpha=0.2, color="#009688", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#009688", label="mean_reward", linewidth=1.5)
    if "Episode_Reward/total" in tags:
        steps, vals = load_scalars(ea, "Episode_Reward/total")
        ax.plot(steps, vals, alpha=0.2, color="#FF5722", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#FF5722", label="episode_total", linewidth=1.5)
    ax.set_ylabel("Reward")
    ax.set_title("Training Reward")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3)

    # -- Panel 5: DORAEMON DR progress --
    ax = axes[2, 0]
    if "DORAEMON/success_rate" in tags:
        steps, vals = load_scalars(ea, "DORAEMON/success_rate")
        ax.plot(steps, vals, alpha=0.2, color="#795548", linewidth=0.5)
        ax.plot(steps, smooth(vals), color="#795548", label="success_rate", linewidth=1.5)
    if "DORAEMON/entropy" in tags:
        steps, vals = load_scalars(ea, "DORAEMON/entropy")
        ax2 = ax.twinx()
        ax2.plot(steps, vals, alpha=0.2, color="#607D8B", linewidth=0.5)
        ax2.plot(steps, smooth(vals), color="#607D8B", label="entropy", linewidth=1.5)
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
        if tag in tags:
            steps, vals = load_scalars(ea, tag)
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
    parser.add_argument("log_dir", help="Path to TensorBoard log directory")
    parser.add_argument("--output", "-o", help="Output image path (default: <log_dir>/encoder_dashboard.png)")
    args = parser.parse_args()
    plot_encoder_dashboard(args.log_dir, args.output)
