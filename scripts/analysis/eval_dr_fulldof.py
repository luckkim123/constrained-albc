# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate FullDOF-TRPO policy robustness across Domain Randomization levels.

Roll/pitch: +-15 deg step-change attitude commands. XYZ velocity and yaw rate
are fixed at zero throughout. Collects attitude tracking, linear velocity
disturbance, and yaw rate disturbance across 4 DR scales.

DR parameters are linearly scaled from 0% (none) to 100% (hard = training DR):
    none   -> 0%   of training DR (nominal physics)
    soft   -> 30%  of training DR
    medium -> 60%  of training DR
    hard   -> 100% of training DR (matches DomainRandomizationCfg defaults)

Outputs 3 tracking plots + summary + failure_time.

Usage:
    ./isaaclab.sh -p scripts/analysis/eval_dr_fulldof.py \
        --task Isaac-FullDOF-TRPO-v0 --num_envs 64 --headless
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import os
import sys

# cli_args lives in scripts/reinforcement_learning/rsl_rl/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))
# common.py lives in scripts/analysis/
sys.path.insert(0, os.path.dirname(__file__))

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

# ---- CLI arguments ----
parser = argparse.ArgumentParser(description="Evaluate DR robustness of FullDOF-TRPO policies.")
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0", help="Task name.")
parser.add_argument("--num_envs", type=int, default=64, help="Number of parallel environments.")
parser.add_argument("--output_dir", type=str, default=None, help="Output directory.")
parser.add_argument("--segment_duration", type=float, default=5.0, help="Duration per segment in seconds.")
parser.add_argument("--seed", type=int, default=42, help="Random seed.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="RSL-RL config entry point.")
parser.add_argument("--doraemon-dr", action="store_true", help="Use DORAEMON-learned DR as hard level.")
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

# clear sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

from datetime import datetime

import gymnasium as gym
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator
import numpy as np
import torch
import rsl_rl.runners.on_policy_runner as _runner_module
from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import DirectRLEnvCfg
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.math import euler_xyz_from_quat

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

from isaaclab_tasks.direct.constrained_full_albc.config import DomainRandomizationCfg
from isaaclab_tasks.direct.constrained_full_albc.encoder import ActorCriticEncoder
from isaaclab_tasks.direct.constrained_full_albc.algorithms import ConstraintTRPO
from isaaclab_tasks.direct.constrained_full_albc.runners import ConstraintEncoderRunner
from isaaclab_tasks.direct.constrained_full_albc.doraemon import PARAM_SPECS

from common import DR_LEVELS, DR_COLORS, DR_SCALE

# Module-level: overridden by --doraemon-dr to use DORAEMON-learned ranges as hard DR.
_DORAEMON_FULL_DR: DomainRandomizationCfg | None = None

# Register custom classes in RSL-RL runner module namespace
_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
_runner_module.FullDOFConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.FullDOFConstraintTRPO = ConstraintTRPO

MAX_ANGLE_DEG = 15.0  # kept for backward compat (episode_length_s calc)

# Mapping from DORAEMON param names to DomainRandomizationCfg field names.
# Most share the same name except payload_mass and water_density.
_DORAEMON_TO_DR_FIELD: dict[str, str] = {
    "payload_mass": "payload_mass_range",
    "water_density": "water_density_range",
}


def load_doraemon_dr(run_dir: str) -> DomainRandomizationCfg:
    """Build DomainRandomizationCfg from DORAEMON's learned distribution.

    Reads final mean/std from TensorBoard logs. Hard DR range = mean +/- 2*std,
    clamped to PARAM_SPEC bounds. Parameters not managed by DORAEMON (joint
    actuator, thruster) are kept at their nominal midpoint (no randomization).
    """
    from tensorboard.backend.event_processing import event_accumulator

    ea = event_accumulator.EventAccumulator(run_dir)
    ea.Reload()

    # Read final DORAEMON mean/std for each parameter
    doraemon_ranges: dict[str, tuple[float, float]] = {}
    for spec in PARAM_SPECS:
        if spec.name.startswith("cmd_"):
            continue  # Skip command scales (not physics DR)
        mean_tag = f"DORAEMON/mean/{spec.name}"
        std_tag = f"DORAEMON/std/{spec.name}"
        try:
            mean_val = ea.Scalars(mean_tag)[-1].value
            std_val = ea.Scalars(std_tag)[-1].value
        except KeyError:
            print(f"[WARN] DORAEMON tag not found: {mean_tag}, using PARAM_SPEC bounds")
            doraemon_ranges[spec.name] = (spec.min_bound, spec.max_bound)
            continue

        lo = max(spec.min_bound, mean_val - 2.0 * std_val)
        hi = min(spec.max_bound, mean_val + 2.0 * std_val)
        doraemon_ranges[spec.name] = (lo, hi)
        print(f"  DORAEMON DR: {spec.name:30s} [{lo:.4f}, {hi:.4f}]")

    # Build config: start with nominal (all at midpoint)
    full = DomainRandomizationCfg()
    cfg = _make_nominal_dr()
    cfg.enable = True

    # Apply DORAEMON-learned ranges
    for param_name, (lo, hi) in doraemon_ranges.items():
        field_name = _DORAEMON_TO_DR_FIELD.get(param_name, param_name)
        if hasattr(cfg, field_name):
            setattr(cfg, field_name, (lo, hi))
        else:
            print(f"[WARN] DomainRandomizationCfg has no field '{field_name}'")

    return cfg


# ============================================================================
# DR Configuration (constrained_full_albc-specific fields)
# ============================================================================

# All tuple fields in DomainRandomizationCfg that should be interpolated.
_DR_TUPLE_FIELDS = [
    "added_mass_scale",
    "linear_damping_scale",
    "quadratic_damping_scale",
    "volume_scale",
    "cob_offset_x",
    "cob_offset_y",
    "cob_offset_z",
    "cog_offset_x",
    "cog_offset_y",
    "cog_offset_z",
    "inertia_scale",
    "body_mass_scale",
    "water_density_range",
    "joint_stiffness_range",
    "joint_damping_range",
    "yaw_damping_scale",
    "joint_effort_limit_range",
    "joint_static_friction_range",
    "joint_viscous_friction_range",
    "payload_mass_range",
    "payload_cog_offset_z",
    "thrust_coefficient_scale",
    "time_constant_scale",
]

_DR_FLOAT_FIELDS = [
    "payload_cog_offset_xy_radius",
    "buoy_moment_arm",
]


def _make_nominal_dr() -> DomainRandomizationCfg:
    """Construct nominal DR config with all physics at midpoint values."""
    full = DomainRandomizationCfg()
    nominal = DomainRandomizationCfg()

    for field_name in _DR_TUPLE_FIELDS:
        lo, hi = getattr(full, field_name)
        mid = (lo + hi) / 2.0
        setattr(nominal, field_name, (mid, mid))

    nominal.payload_cog_offset_xy_radius = 0.0
    return nominal


def build_dr_config(scale: float) -> DomainRandomizationCfg:
    """Build DR config by interpolating between nominal and full DR.

    When _DORAEMON_FULL_DR is set (via --doraemon-dr), uses DORAEMON-learned
    ranges as the 100% DR level instead of default DomainRandomizationCfg.
    """
    nominal = _make_nominal_dr()

    if scale <= 0.0:
        nominal.enable = True
        return nominal

    full = _DORAEMON_FULL_DR if _DORAEMON_FULL_DR is not None else DomainRandomizationCfg()
    f = min(scale, 1.0)

    cfg = DomainRandomizationCfg()
    cfg.enable = True

    for field_name in _DR_TUPLE_FIELDS:
        nom_val = getattr(nominal, field_name)
        full_val = getattr(full, field_name)
        lo = nom_val[0] + f * (full_val[0] - nom_val[0])
        hi = nom_val[1] + f * (full_val[1] - nom_val[1])
        setattr(cfg, field_name, (lo, hi))

    for field_name in _DR_FLOAT_FIELDS:
        nom_val = getattr(nominal, field_name)
        full_val = getattr(full, field_name)
        setattr(cfg, field_name, nom_val + f * (full_val - nom_val))

    return cfg


def apply_dr_config(env_cfg, scale: float) -> None:
    """Apply interpolated DR config to the environment config."""
    env_cfg.randomization = build_dr_config(scale)


# ============================================================================
# Trajectory (same +-15 deg step-change as eval_dr.py)
# ============================================================================


ATT_AMP_DEG = 15.0  # Attitude step amplitude (degrees)
LIN_VEL_AMP = 0.25  # Linear velocity step amplitude (m/s)
YAW_RATE_AMP = 0.25  # Yaw rate step amplitude (rad/s)


def build_step_trajectory(
    segment_duration: float,
    step_dt: float,
) -> tuple[np.ndarray, dict[str, np.ndarray], list[str]]:
    """Build 6-DOF step-change target trajectory.

    Tests each command channel with step changes:
    - Roll/Pitch attitude (deg): +-ATT_AMP_DEG
    - Linear velocity x/y/z (m/s): +-LIN_VEL_AMP
    - Yaw rate (rad/s): +-YAW_RATE_AMP

    Returns:
        time_s: 1D time array (seconds).
        targets: dict of 1D target arrays keyed by channel name.
        seg_names: list of segment labels.
    """
    a = ATT_AMP_DEG
    v = LIN_VEL_AMP
    w = YAW_RATE_AMP

    # (roll_deg, pitch_deg, vx, vy, vz, yaw_rate, name)
    waypoints: list[tuple[float, float, float, float, float, float, str]] = [
        (0, 0, 0, 0, 0, 0, "neutral"),
        (a, 0, 0, 0, 0, 0, f"roll +{a:.0f}"),
        (0, a, 0, 0, 0, 0, f"pitch +{a:.0f}"),
        (-a, -a, 0, 0, 0, 0, f"({-a:.0f}, {-a:.0f})"),
        (a, -a, 0, 0, 0, 0, f"({a:.0f}, {-a:.0f})"),
        (0, 0, v, 0, 0, 0, f"vx +{v}"),
        (0, 0, -v, 0, 0, 0, f"vx {-v}"),
        (0, 0, 0, v, 0, 0, f"vy +{v}"),
        (0, 0, 0, -v, 0, 0, f"vy {-v}"),
        (0, 0, 0, 0, v, 0, f"vz +{v}"),
        (0, 0, 0, 0, -v, 0, f"vz {-v}"),
        (0, 0, 0, 0, 0, w, f"yaw +{w}"),
        (0, 0, 0, 0, 0, -w, f"yaw {-w}"),
        (0, 0, 0, 0, 0, 0, "return neutral"),
    ]

    steps_per_seg = int(segment_duration / step_dt)
    n_segs = len(waypoints)
    total_steps = steps_per_seg * n_segs

    time_s = np.arange(total_steps) * step_dt
    keys = ["roll_deg", "pitch_deg", "vx", "vy", "vz", "yaw_rate"]
    targets: dict[str, np.ndarray] = {k: np.zeros(total_steps) for k in keys}
    seg_names: list[str] = []

    for i, wp in enumerate(waypoints):
        s = i * steps_per_seg
        e = (i + 1) * steps_per_seg
        for j, k in enumerate(keys):
            targets[k][s:e] = wp[j]
        seg_names.append(wp[6])

    return time_s, targets, seg_names


# ============================================================================
# Metrics
# ============================================================================


def compute_metrics(data: dict) -> dict:
    """Compute summary metrics from collected data."""
    time_s = data["time"]
    error_roll = data["error_roll"]
    error_pitch = data["error_pitch"]
    terminated = data["terminated"]
    num_envs = error_roll.shape[1]

    error_norm = np.sqrt(error_roll**2 + error_pitch**2)
    alive = ~terminated

    if alive.any():
        total_att_error = float(np.nanmean(np.where(alive, error_norm, np.nan)))
    else:
        total_att_error = float("nan")

    survival_rate = float(alive[-1].sum()) / num_envs * 100.0

    # Attitude: per-segment steady-state error and settling time
    seg_steps = data["steps_per_segment"]
    num_segments = len(data["segment_names"])
    steady_state_errors = []
    settling_times = []

    max_target_amp = max(
        float(np.max(np.abs(data["target_roll_deg"]))),
        float(np.max(np.abs(data["target_pitch_deg"]))),
        1.0,
    )
    settling_threshold = max(2.0, max_target_amp * 0.33)

    for seg_idx in range(num_segments):
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_error = error_norm[s:e]
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]

        ss_start = int(seg_steps * 0.5)
        ss_error = seg_error[ss_start:]
        ss_alive = seg_alive[ss_start:]
        if ss_alive.any():
            steady_state_errors.append(float(np.nanmean(np.where(ss_alive, ss_error, np.nan))))
        else:
            steady_state_errors.append(float("nan"))

        mean_per_step = np.nanmean(np.where(seg_alive, seg_error, np.nan), axis=1)
        settled = mean_per_step < settling_threshold
        if settled.any():
            settling_times.append(float(seg_time[np.argmax(settled)] - seg_time[0]))
        else:
            settling_times.append(float(data["segment_duration"]))

    # Linear velocity: overall mean magnitude (should be near 0)
    lin_vel_norm = data["lin_vel_norm"]
    if alive.any():
        total_lin_vel_error = float(np.nanmean(np.where(alive, lin_vel_norm, np.nan)))
    else:
        total_lin_vel_error = float("nan")

    # Yaw rate: overall mean magnitude (should be near 0)
    yaw_rate_abs = np.abs(data["yaw_rate"])
    if alive.any():
        total_yaw_rate_error = float(np.nanmean(np.where(alive, yaw_rate_abs, np.nan)))
    else:
        total_yaw_rate_error = float("nan")

    per_env_att_errors = np.nanmean(np.where(alive, error_norm, np.nan), axis=0)

    return {
        "total_att_error": total_att_error,
        "total_att_error_std": float(np.nanstd(per_env_att_errors)),
        "total_lin_vel_error": total_lin_vel_error,
        "total_yaw_rate_error": total_yaw_rate_error,
        "survival_rate": survival_rate,
        "steady_state_errors": steady_state_errors,
        "settling_times": settling_times,
    }


# ============================================================================
# Plots
# ============================================================================


def _bar_subplot(ax, x, values, colors, xlabels, ylabel, title, ylim=None, yerr=None):
    """Render a single bar chart subplot with consistent styling."""
    ax.bar(x, values, color=colors, yerr=yerr, capsize=4, error_kw={"linewidth": 1.2})
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ylim:
        ax.set_ylim(*ylim)
    ax.grid(True, alpha=0.3, axis="y")


def generate_plots(
    all_data: dict[str, dict],
    all_metrics: dict[str, dict],
    output_dir: str,
) -> None:
    """Generate all evaluation figures and save as PNG."""
    levels = [lvl for lvl in DR_LEVELS if lvl in all_data]

    _plot_attitude_tracking(all_data, levels, output_dir)
    _plot_lin_vel(all_data, levels, output_dir)
    _plot_yaw_rate(all_data, levels, output_dir)
    _plot_summary(all_data, all_metrics, levels, output_dir)
    _plot_failure_time(all_data, levels, output_dir)


def _plot_attitude_tracking(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Figure 1: Roll/pitch attitude tracking per DR level (Nx2 grid)."""
    fig, axes = plt.subplots(len(levels), 2, figsize=(16, 3 * len(levels)), sharex=True)
    fig.suptitle("Attitude Tracking per DR Level", fontsize=14, y=0.98)

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        time_s = d["time"]
        alive = ~d["terminated"]
        dr_pct = int(DR_SCALE[lvl] * 100)

        for col, (actual_key, target_key, axis_label) in enumerate(
            [
                ("actual_roll_deg", "target_roll_deg", "Roll (deg)"),
                ("actual_pitch_deg", "target_pitch_deg", "Pitch (deg)"),
            ]
        ):
            ax = axes[row, col] if len(levels) > 1 else axes[col]
            ax.plot(time_s, d[target_key], "k--", linewidth=1.2, alpha=0.6, label="target")
            vals = np.where(alive, d[actual_key], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(time_s, mean, color=color, linewidth=1.0, label="actual (mean)")
            ax.fill_between(time_s, mean - std, mean + std, color=color, alpha=0.15)
            ax.set_ylabel(axis_label, fontsize=9)
            ax.yaxis.set_major_locator(MultipleLocator(15))
            ax.grid(True, alpha=0.3)
            if col == 0:
                ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
            if row == 0 and col == 0:
                ax.legend(loc="upper right", fontsize=8)
            if row == len(levels) - 1:
                ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "attitude.png"), dpi=150)
    plt.close(fig)


def _plot_lin_vel(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Figure 2: Linear velocity tracking (XYZ, all DR levels overlaid)."""
    fig, axes = plt.subplots(3, 1, figsize=(14, 10), sharex=True)
    fig.suptitle("Linear Velocity Tracking", fontsize=14)

    axis_labels = ["Vx (m/s)", "Vy (m/s)", "Vz (m/s)"]
    data_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_keys = ["target_vx", "target_vy", "target_vz"]

    # Plot target from first level (same for all)
    ref = all_data[levels[0]]
    for i, tkey in enumerate(target_keys):
        if tkey in ref:
            axes[i].plot(ref["time"], ref[tkey], "k--", linewidth=1.2, alpha=0.6, label="target")

    for lvl in levels:
        d = all_data[lvl]
        time_s = d["time"]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"]
        dr_pct = int(DR_SCALE[lvl] * 100)
        label = f"{lvl} (DR {dr_pct}%)"

        for i, key in enumerate(data_keys):
            vals = np.where(alive, d[key], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            axes[i].plot(time_s, mean, color=color, linewidth=1.0, label=label)
            axes[i].fill_between(time_s, mean - std, mean + std, color=color, alpha=0.12)

    for i, ylabel in enumerate(axis_labels):
        axes[i].set_ylabel(ylabel, fontsize=9)
        axes[i].grid(True, alpha=0.3)
    axes[0].legend(loc="upper right", fontsize=9)
    axes[-1].set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "lin_vel.png"), dpi=150)
    plt.close(fig)


def _plot_yaw_rate(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Figure 3: Yaw rate tracking (all DR levels overlaid)."""
    fig, ax = plt.subplots(1, 1, figsize=(14, 4))
    fig.suptitle("Yaw Rate Tracking", fontsize=14)

    # Plot target from first level
    ref = all_data[levels[0]]
    if "target_yaw_rate" in ref:
        ax.plot(ref["time"], ref["target_yaw_rate"], "k--", linewidth=1.2, alpha=0.6, label="target")

    for lvl in levels:
        d = all_data[lvl]
        time_s = d["time"]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"]
        dr_pct = int(DR_SCALE[lvl] * 100)
        label = f"{lvl} (DR {dr_pct}%)"

        vals = np.where(alive, d["yaw_rate"], np.nan)
        mean = np.nanmean(vals, axis=1)
        std = np.nanstd(vals, axis=1)
        ax.plot(time_s, mean, color=color, linewidth=1.0, label=label)
        ax.fill_between(time_s, mean - std, mean + std, color=color, alpha=0.12)

    ax.set_ylabel("Yaw Rate (rad/s)", fontsize=10)
    ax.set_xlabel("Time (s)")
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "yaw_rate.png"), dpi=150)
    plt.close(fig)


def _plot_summary(all_data: dict, all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Figure 4: Summary bar charts (2x2)."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("DR Robustness Summary", fontsize=14)
    x = np.arange(len(levels))
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): Total attitude error
    att_errors = [all_metrics[lvl]["total_att_error"] for lvl in levels]
    att_stds = [all_metrics[lvl]["total_att_error_std"] for lvl in levels]
    _bar_subplot(axes[0, 0], x, att_errors, bar_colors, xlabels, "Error (deg)", "Attitude Error (mean)", yerr=att_stds)

    # (0,1): Survival rate
    survivals = [all_metrics[lvl]["survival_rate"] for lvl in levels]
    _bar_subplot(axes[0, 1], x, survivals, bar_colors, xlabels, "Survival (%)", "Survival Rate", ylim=(0, 105))

    # (1,0): Linear velocity error
    lin_errs = [all_metrics[lvl]["total_lin_vel_error"] for lvl in levels]
    _bar_subplot(axes[1, 0], x, lin_errs, bar_colors, xlabels, "Velocity (m/s)", "Linear Velocity Error (mean)")

    # (1,1): Yaw rate error
    yaw_errs = [all_metrics[lvl]["total_yaw_rate_error"] for lvl in levels]
    _bar_subplot(axes[1, 1], x, yaw_errs, bar_colors, xlabels, "Rate (rad/s)", "Yaw Rate Error (mean)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary.png"), dpi=150)
    plt.close(fig)


def _plot_failure_time(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Figure 5: Failure time distribution."""
    if "time_to_failure" not in all_data[levels[0]]:
        return

    fig, axes = plt.subplots(1, len(levels), figsize=(4 * len(levels), 4), sharey=True)
    fig.suptitle("Failure Time Distribution", fontsize=14)
    if len(levels) == 1:
        axes = [axes]
    for i, lvl in enumerate(levels):
        ttf = all_data[lvl]["time_to_failure"]
        valid = ttf[~np.isnan(ttf)]
        ax = axes[i]
        dr_pct = int(DR_SCALE[lvl] * 100)
        if len(valid) > 0:
            ax.hist(valid, bins=20, color=DR_COLORS[lvl], alpha=0.7, edgecolor="black")
            ax.axvline(
                np.median(valid), color="black", linestyle="--", linewidth=1.0,
                label=f"median={np.median(valid):.1f}s",
            )
            ax.legend(fontsize=8)
        ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10)
        ax.set_xlabel("Time to Failure (s)")
        if i == 0:
            ax.set_ylabel("Count")
        ax.grid(True, alpha=0.3)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "failure_time.png"), dpi=150)
    plt.close(fig)


# ============================================================================
# Evaluation Loop
# ============================================================================


def run_evaluation(
    env,
    policy,
    policy_nn,
    raw_env,
    time_s,
    targets: dict[str, np.ndarray],
    segment_names,
    segment_duration,
    step_dt,
    num_envs,
    device,
) -> dict:
    """Run one evaluation pass and collect per-step data.

    Injects 6-DOF commands from targets dict:
    - roll_deg, pitch_deg: attitude commands (deg -> rad)
    - vx, vy, vz: linear velocity commands (m/s, body frame)
    - yaw_rate: yaw rate command (rad/s)
    """
    total_steps = len(time_s)
    steps_per_seg = int(segment_duration / step_dt)
    target_roll_deg = targets["roll_deg"]
    target_pitch_deg = targets["pitch_deg"]

    # Attitude
    actual_roll = np.zeros((total_steps, num_envs))
    actual_pitch = np.zeros((total_steps, num_envs))
    error_roll = np.zeros((total_steps, num_envs))
    error_pitch = np.zeros((total_steps, num_envs))
    # Linear velocity (body frame)
    lin_vel_x = np.zeros((total_steps, num_envs))
    lin_vel_y = np.zeros((total_steps, num_envs))
    lin_vel_z = np.zeros((total_steps, num_envs))
    lin_vel_norm = np.zeros((total_steps, num_envs))
    # Yaw rate (body frame)
    yaw_rate = np.zeros((total_steps, num_envs))
    # Action magnitude
    action_magnitude = np.zeros((total_steps, num_envs))
    # Termination
    terminated = np.zeros((total_steps, num_envs), dtype=bool)
    time_to_failure = np.full(num_envs, float("nan"))

    # Force full reset via throwaway step
    raw_env.episode_length_buf[:] = raw_env.max_episode_length
    obs = env.get_observations()
    with torch.inference_mode():
        obs, _, _, _ = env.step(policy(obs))
        if hasattr(policy_nn, "reset"):
            policy_nn.reset(torch.ones(num_envs, 1, dtype=torch.bool, device=device))
    raw_env.episode_length_buf[:] = 0

    target_roll_rad = np.deg2rad(target_roll_deg)
    target_pitch_rad = np.deg2rad(target_pitch_deg)
    terminated_ever = np.zeros(num_envs, dtype=bool)

    for step_idx in range(total_steps):
        # Inject 6-DOF commands from trajectory
        raw_env._ang_cmd[:, 0] = target_roll_rad[step_idx]
        raw_env._ang_cmd[:, 1] = target_pitch_rad[step_idx]
        raw_env._ang_cmd[:, 2] = targets["yaw_rate"][step_idx]
        raw_env._vel_cmd_lin[:, 0] = targets["vx"][step_idx]
        raw_env._vel_cmd_lin[:, 1] = targets["vy"][step_idx]
        raw_env._vel_cmd_lin[:, 2] = targets["vz"][step_idx]

        with torch.inference_mode():
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            if hasattr(policy_nn, "reset"):
                policy_nn.reset(dones)

        # Collect action magnitude
        action_magnitude[step_idx] = torch.norm(actions, dim=-1).cpu().numpy()

        # Attitude: actual + error
        roll_cur, pitch_cur, _ = euler_xyz_from_quat(raw_env._robot.data.root_quat_w)
        actual_roll[step_idx] = torch.rad2deg(roll_cur).cpu().numpy()
        actual_pitch[step_idx] = torch.rad2deg(pitch_cur).cpu().numpy()

        att_err = raw_env._att_rp_err
        error_roll[step_idx] = torch.rad2deg(att_err[:, 0]).cpu().numpy()
        error_pitch[step_idx] = torch.rad2deg(att_err[:, 1]).cpu().numpy()

        # Linear velocity (body frame)
        lv = raw_env._robot.data.root_lin_vel_b
        lin_vel_x[step_idx] = lv[:, 0].cpu().numpy()
        lin_vel_y[step_idx] = lv[:, 1].cpu().numpy()
        lin_vel_z[step_idx] = lv[:, 2].cpu().numpy()
        lin_vel_norm[step_idx] = torch.norm(lv, dim=-1).cpu().numpy()

        # Yaw rate (body frame)
        yaw_rate[step_idx] = raw_env._robot.data.root_ang_vel_b[:, 2].cpu().numpy()

        # Termination tracking
        dones_np = dones.squeeze(-1).bool().cpu().numpy() if dones.dim() > 1 else dones.bool().cpu().numpy()
        newly_terminated = dones_np & ~terminated_ever
        if newly_terminated.any():
            time_to_failure[newly_terminated] = time_s[step_idx]
        terminated_ever |= dones_np
        terminated[step_idx] = terminated_ever

        if (step_idx + 1) % 1000 == 0 or step_idx == total_steps - 1:
            alive_count = num_envs - terminated_ever.sum()
            err_norm = np.sqrt(error_roll[step_idx] ** 2 + error_pitch[step_idx] ** 2)
            alive_mask = ~terminated_ever
            mean_err = np.mean(err_norm[alive_mask]) if alive_mask.any() else float("nan")
            lv_mean = np.mean(lin_vel_norm[step_idx][alive_mask]) if alive_mask.any() else float("nan")
            seg_idx = min(step_idx // steps_per_seg, len(segment_names) - 1)
            print(
                f"  [{step_idx + 1:6d}/{total_steps}] "
                f"seg={segment_names[seg_idx]:30s} "
                f"att_err={mean_err:5.1f}deg "
                f"lin_vel={lv_mean:.3f}m/s "
                f"alive={alive_count}/{num_envs}"
            )

    return {
        "time": time_s,
        "target_roll_deg": target_roll_deg,
        "target_pitch_deg": target_pitch_deg,
        "target_vx": targets["vx"],
        "target_vy": targets["vy"],
        "target_vz": targets["vz"],
        "target_yaw_rate": targets["yaw_rate"],
        "actual_roll_deg": actual_roll,
        "actual_pitch_deg": actual_pitch,
        "error_roll": error_roll,
        "error_pitch": error_pitch,
        "lin_vel_x": lin_vel_x,
        "lin_vel_y": lin_vel_y,
        "lin_vel_z": lin_vel_z,
        "lin_vel_norm": lin_vel_norm,
        "yaw_rate": yaw_rate,
        "action_magnitude": action_magnitude,
        "terminated": terminated,
        "time_to_failure": time_to_failure,
        "steps_per_segment": steps_per_seg,
        "segment_duration": segment_duration,
        "segment_names": segment_names,
    }


# ============================================================================
# Main
# ============================================================================


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    """Main evaluation function."""
    task_name = args_cli.task.split(":")[-1]
    use_checkpoint = args_cli.checkpoint != "none" if args_cli.checkpoint else True

    # ---- Env config overrides (evaluation mode) ----
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.play_mode = True  # Fixed zero commands (overridden by run_evaluation anyway)
    env_cfg.vel_cmd_resample_steps = 0  # Disable mid-episode resampling; eval injects commands directly
    if hasattr(env_cfg, "observation_noise_model"):
        env_cfg.observation_noise_model = None
    env_cfg.max_attitude_angle = 2.5
    env_cfg.debug_vis = False
    env_cfg.seed = args_cli.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    if hasattr(env_cfg, "doraemon"):
        env_cfg.doraemon.enable = False

    # Compute episode_length_s from trajectory (14 segments)
    _n_segs = 14  # 5 att + 6 lin_vel + 2 yaw + 1 neutral
    env_cfg.episode_length_s = _n_segs * args_cli.segment_duration + 10.0

    # ---- Load checkpoint ----
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)

    resume_path = None
    if use_checkpoint:
        log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
        if args_cli.checkpoint and args_cli.checkpoint != "none":
            resume_path = retrieve_file_path(args_cli.checkpoint)
        else:
            resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
            best_model_path = os.path.join(os.path.dirname(resume_path), "best_model.pt")
            if os.path.isfile(best_model_path):
                resume_path = best_model_path
        print(f"[INFO] Checkpoint: {resume_path}")

    # ---- Load agent params from run directory if available ----
    run_agent_dict = None
    if resume_path:
        import yaml

        run_params_path = os.path.join(os.path.dirname(resume_path), "params", "agent.yaml")
        if os.path.isfile(run_params_path):
            try:
                with open(run_params_path) as f:
                    run_agent_dict = yaml.full_load(f)
                print(f"[INFO] Loaded agent params from run directory: {run_params_path}")
            except yaml.YAMLError as e:
                print(f"[WARN] Could not load run agent params, using task registry: {e}")
                run_agent_dict = None

    # ---- Output directory ----
    if args_cli.output_dir:
        output_dir = args_cli.output_dir
    elif resume_path:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr")
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = task_name.removeprefix("Isaac-").lower().replace("-", "_").removesuffix("_v0")
        output_dir = os.path.join("logs", "eval_dr", folder_name, ts)
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR override ----
    global _DORAEMON_FULL_DR
    if args_cli.doraemon_dr and resume_path:
        run_dir = os.path.dirname(resume_path)
        print(f"\n[INFO] Loading DORAEMON-learned DR from: {run_dir}")
        _DORAEMON_FULL_DR = load_doraemon_dr(run_dir)
        print("[INFO] Hard DR = DORAEMON-learned ranges (joint/thruster at nominal)\n")

    # ---- Create env (initial DR = none) ----
    apply_dr_config(env_cfg, DR_SCALE["none"])
    env = gym.make(args_cli.task, cfg=env_cfg)
    clip_actions = run_agent_dict.get("clip_actions") if run_agent_dict else agent_cfg.clip_actions
    env = RslRlVecEnvWrapper(env, clip_actions=clip_actions)

    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device

    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")
    print(f"[INFO] Segment duration: {args_cli.segment_duration}s")

    # ---- Create runner + load policy ----
    agent_dict = run_agent_dict if run_agent_dict else agent_cfg.to_dict()
    runner_cls_name = agent_dict.get("class_name", getattr(agent_cfg, "class_name", "OnPolicyRunner"))
    runner_device = agent_dict.get("device", agent_cfg.device)

    if use_checkpoint and resume_path:
        runner_cls_map = {
            "FullDOFConstraintEncoderRunner": ConstraintEncoderRunner,
        }
        runner_cls = runner_cls_map.get(runner_cls_name)

        if runner_cls:
            runner = runner_cls(env, agent_dict, log_dir=None, device=runner_device)
            runner.load(resume_path, load_optimizer=False)
            policy = runner.get_inference_policy(device=device)
            policy_nn = runner.alg.policy
        else:
            runner = OnPolicyRunner(env, agent_dict, log_dir=None, device=runner_device)
            runner.load(resume_path, load_optimizer=False)
            policy = runner.get_inference_policy(device=device)
            try:
                policy_nn = runner.alg.policy
            except AttributeError:
                policy_nn = runner.alg.actor_critic

        print(f"[INFO] Loaded {runner_cls_name} from {resume_path}")
    else:
        action_dim = env_cfg.action_space
        policy = lambda obs: torch.zeros(num_envs, action_dim, device=device)  # noqa: E731
        policy_nn = type("FakePolicy", (), {"reset": lambda _s, _d: None})()
        print("[INFO] No checkpoint mode (zero-action policy).")

    # ---- Build trajectory (same for all DR levels) ----
    time_s, targets, segment_names = build_step_trajectory(
        segment_duration=args_cli.segment_duration,
        step_dt=step_dt,
    )
    print(
        f"[INFO] Trajectory: {len(segment_names)} segs x {args_cli.segment_duration}s"
        f" = {len(time_s)} steps ({time_s[-1]:.0f}s)"
    )
    print(f"[INFO] Targets: att +-{ATT_AMP_DEG}deg, lin +-{LIN_VEL_AMP}m/s, yaw +-{YAW_RATE_AMP}rad/s")

    # ---- Run evaluation for each DR level ----
    all_data = {}
    all_metrics = {}

    for level in DR_LEVELS:
        dr_pct = int(DR_SCALE[level] * 100)
        print(f"\n{'=' * 60}")
        print(f"  DR Level: {level.upper()} | DR Scale: {dr_pct}%")
        print(f"{'=' * 60}")

        apply_dr_config(raw_env.cfg, DR_SCALE[level])

        data = run_evaluation(
            env=env,
            policy=policy,
            policy_nn=policy_nn,
            raw_env=raw_env,
            time_s=time_s,
            targets=targets,
            segment_names=segment_names,
            segment_duration=args_cli.segment_duration,
            step_dt=step_dt,
            num_envs=num_envs,
            device=device,
        )
        all_data[level] = data

        np.savez_compressed(
            os.path.join(output_dir, f"eval_{level}.npz"),
            **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
        )

        metrics = compute_metrics(data)
        all_metrics[level] = metrics

        print(f"\n  Results ({level}, DR {dr_pct}%):")
        print(f"    Attitude error:  {metrics['total_att_error']:.1f} +/- {metrics['total_att_error_std']:.1f} deg")
        print(f"    Lin vel error:   {metrics['total_lin_vel_error']:.3f} m/s")
        print(f"    Yaw rate error:  {metrics['total_yaw_rate_error']:.4f} rad/s")
        print(f"    Survival rate:   {metrics['survival_rate']:.0f}%")
        print(f"    SS error (avg):  {np.nanmean(metrics['steady_state_errors']):.1f} deg")
        print(f"    Settling (avg):  {np.nanmean(metrics['settling_times']):.2f} s")

    # ---- Generate plots ----
    print("\n[INFO] Generating plots...")
    generate_plots(all_data, all_metrics, output_dir)

    # ---- Print final comparison ----
    print(f"\n{'=' * 90}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 90}")
    print(
        f"{'Level':<10} {'DR%':>5} {'AttErr':>10} {'LinVel':>8} "
        f"{'YawRate':>8} {'SS Err':>8} {'Settle':>8} {'Survival':>10}"
    )
    print(f"{'-' * 10} {'-' * 5} {'-' * 10} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 10}")
    for lvl in DR_LEVELS:
        m = all_metrics[lvl]
        print(
            f"{lvl:<10} "
            f"{int(DR_SCALE[lvl] * 100):4d}% "
            f"{m['total_att_error']:5.1f}+/-{m['total_att_error_std']:.1f} "
            f"{m['total_lin_vel_error']:7.3f} "
            f"{m['total_yaw_rate_error']:7.4f} "
            f"{np.nanmean(m['steady_state_errors']):7.1f}d "
            f"{np.nanmean(m['settling_times']):7.2f}s "
            f"{m['survival_rate']:9.0f}%"
        )
    print(f"{'=' * 90}")

    print(f"\nOutput saved to: {output_dir}")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
