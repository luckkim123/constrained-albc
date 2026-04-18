# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate FullDOF-TRPO policy robustness under mid-episode DR changes.

Sends zero commands (hover) while changing domain randomization parameters
every ~5 seconds within a single episode. Tests the encoder's online
adaptation to sudden physics changes.

DR parameters are sampled from the hard DR range (DORAEMON-learned if
available, otherwise HardDomainRandomizationCfg).

Outputs time-series plots of attitude, linear velocity, yaw rate, and
action magnitude across all DR steps.

Usage:
    ./isaaclab.sh -p scripts/analysis/eval_dr_robustness.py \
        --task Isaac-FullDOF-TRPO-v0 --num_envs 1 --headless
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
parser = argparse.ArgumentParser(description="Evaluate DR robustness under mid-episode physics changes.")
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0", help="Task name.")
parser.add_argument("--num_envs", type=int, default=1, help="Number of parallel environments.")
parser.add_argument("--output_dir", type=str, default=None, help="Output directory.")
parser.add_argument("--step_duration", type=float, default=5.0, help="Duration per DR step in seconds.")
parser.add_argument("--num_steps", type=int, default=10, help="Number of DR change steps.")
parser.add_argument("--seed", type=int, default=42, help="Random seed.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="RSL-RL config entry point.")
parser.add_argument(
    "--doraemon-dr",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Use DORAEMON-learned DR as hard level. Default: auto-load from run dir.",
)
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

from isaaclab_tasks.direct.constrained_full_albc.config import (
    DomainRandomizationCfg,
    HardDomainRandomizationCfg,
)
from isaaclab_tasks.direct.constrained_full_albc.encoder import ActorCriticEncoder
from isaaclab_tasks.direct.constrained_full_albc.algorithms import ConstraintTRPO
from isaaclab_tasks.direct.constrained_full_albc.runners import ConstraintEncoderRunner
from isaaclab_tasks.direct.constrained_full_albc.doraemon import build_param_specs
from isaaclab_tasks.direct.constrained_full_albc.mdp import (
    DRSampler,
    randomize_body_mass,
    randomize_hydrodynamics,
    randomize_ocean_current,
    randomize_payload,
)

# Register custom classes in RSL-RL runner module namespace
_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
_runner_module.FullDOFConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.FullDOFConstraintTRPO = ConstraintTRPO

# Module-level: DORAEMON-learned distribution as the hard-DR anchor.
_DORAEMON_FULL_DR: DomainRandomizationCfg | None = None


# ============================================================================
# DORAEMON DR Loading (reuse from eval_dr_fulldof.py)
# ============================================================================

_DORAEMON_TO_DR_FIELD: dict[str, str] = {
    "payload_mass": "payload_mass_range",
    "water_density": "water_density_range",
}


def load_doraemon_dr(run_dir: str) -> DomainRandomizationCfg | None:
    """Build DomainRandomizationCfg from DORAEMON's learned distribution.

    Hard DR range = mean +/- 2*std, clamped to PARAM_SPEC bounds.
    Non-DORAEMON parameters start from HardDomainRandomizationCfg.
    """
    from tensorboard.backend.event_processing import event_accumulator

    if not os.path.isdir(run_dir):
        return None

    try:
        ea = event_accumulator.EventAccumulator(run_dir)
        ea.Reload()
        all_tags = set(ea.Tags().get("scalars", []))
    except Exception as e:
        print(f"[WARN] Could not load TB events from {run_dir}: {e}")
        return None

    if not any(t.startswith("DORAEMON/mean/") for t in all_tags):
        return None

    cfg = HardDomainRandomizationCfg()
    cfg.enable = True
    runtime_specs = build_param_specs(cfg)

    for spec in runtime_specs:
        if spec.name.startswith("cmd_"):
            continue
        mean_tag = f"DORAEMON/mean/{spec.name}"
        std_tag = f"DORAEMON/std/{spec.name}"
        if mean_tag not in all_tags or std_tag not in all_tags:
            continue

        mean_val = ea.Scalars(mean_tag)[-1].value
        std_val = ea.Scalars(std_tag)[-1].value
        lo = max(spec.min_bound, mean_val - 2.0 * std_val)
        hi = min(spec.max_bound, mean_val + 2.0 * std_val)

        mapped = _DORAEMON_TO_DR_FIELD.get(spec.name)
        field_name: str = mapped if mapped is not None else spec.name
        if not hasattr(cfg, field_name):
            continue

        setattr(cfg, field_name, (lo, hi))
        print(f"  DORAEMON DR: {field_name:30s} mean={mean_val:.4f}  std={std_val:.4f}  -> [{lo:.4f}, {hi:.4f}]")

    return cfg


def get_hard_dr_config() -> DomainRandomizationCfg:
    """Get the hard DR config (DORAEMON if loaded, otherwise HardDomainRandomizationCfg)."""
    cfg = _DORAEMON_FULL_DR if _DORAEMON_FULL_DR is not None else HardDomainRandomizationCfg()
    cfg.enable = True
    return cfg


# ============================================================================
# Mid-episode DR application
# ============================================================================


def apply_dr_mid_episode(raw_env, dr_cfg: DomainRandomizationCfg) -> None:
    """Apply new DR parameters mid-episode without resetting robot pose/velocity.

    Creates a DRSampler from the given config and calls randomization functions
    to change physics parameters in-place.
    """
    env_ids = torch.arange(raw_env.num_envs, device=raw_env.device)
    dr = DRSampler(dr_cfg, num_envs=raw_env.num_envs, device=raw_env.device)

    randomize_hydrodynamics(env=raw_env, env_ids=env_ids, dr=dr, sampled=None)
    randomize_body_mass(env=raw_env, env_ids=env_ids, dr=dr, sampled=None)
    randomize_payload(env=raw_env, env_ids=env_ids, dr=dr, sampled=None)

    has_ocean_current = any(v > 0 for v in raw_env.cfg.ocean_current.max_velocity)
    if has_ocean_current:
        randomize_ocean_current(env=raw_env, env_ids=env_ids)


# ============================================================================
# Evaluation loop
# ============================================================================


def run_robustness_eval(
    env,
    policy,
    policy_nn,
    raw_env,
    dr_cfg: DomainRandomizationCfg,
    step_duration: float,
    num_dr_steps: int,
    step_dt: float,
    num_envs: int,
    device,
) -> dict:
    """Run robustness evaluation: zero command + periodic DR changes.

    Args:
        dr_cfg: Hard DR config to sample from at each DR step.
        step_duration: Duration of each DR step in seconds.
        num_dr_steps: Number of DR changes.

    Returns:
        Dict of collected data arrays.
    """
    steps_per_dr = int(step_duration / step_dt)
    total_steps = steps_per_dr * num_dr_steps

    # Data arrays
    actual_roll = np.zeros((total_steps, num_envs))
    actual_pitch = np.zeros((total_steps, num_envs))
    actual_yaw = np.zeros((total_steps, num_envs))
    lin_vel_x = np.zeros((total_steps, num_envs))
    lin_vel_y = np.zeros((total_steps, num_envs))
    lin_vel_z = np.zeros((total_steps, num_envs))
    yaw_rate = np.zeros((total_steps, num_envs))
    action_mag = np.zeros((total_steps, num_envs))
    dr_step_idx = np.zeros(total_steps, dtype=int)
    terminated = np.zeros((total_steps, num_envs), dtype=bool)
    time_to_failure = np.full(num_envs, float("nan"))

    # Force full reset to start fresh
    raw_env.episode_length_buf[:] = raw_env.max_episode_length
    obs = env.get_observations()
    with torch.inference_mode():
        obs, _, _, _ = env.step(policy(obs))
        if hasattr(policy_nn, "reset"):
            policy_nn.reset(torch.ones(num_envs, 1, dtype=torch.bool, device=device))
    raw_env.episode_length_buf[:] = 0

    # Set zero commands
    raw_env._ang_cmd[:] = 0.0
    raw_env._vel_cmd_lin[:] = 0.0

    terminated_ever = np.zeros(num_envs, dtype=bool)
    time_s = np.arange(total_steps) * step_dt

    for dr_i in range(num_dr_steps):
        # Apply new DR at the start of each DR step
        apply_dr_mid_episode(raw_env, dr_cfg)
        print(f"  DR step {dr_i + 1}/{num_dr_steps} (t={dr_i * step_duration:.1f}s)")

        for local_step in range(steps_per_dr):
            global_step = dr_i * steps_per_dr + local_step

            # Ensure zero commands every step (prevent resampling)
            raw_env._ang_cmd[:] = 0.0
            raw_env._vel_cmd_lin[:] = 0.0

            with torch.inference_mode():
                actions = policy(obs)
                obs, _, dones, _ = env.step(actions)
                if hasattr(policy_nn, "reset"):
                    policy_nn.reset(dones)

            # Prevent episode termination from resetting DR
            raw_env.episode_length_buf[:] = min(raw_env.episode_length_buf[0].item(), raw_env.max_episode_length - 10)

            # Collect data
            roll_cur, pitch_cur, yaw_cur = euler_xyz_from_quat(raw_env._robot.data.root_quat_w)
            actual_roll[global_step] = torch.rad2deg(roll_cur).cpu().numpy()
            actual_pitch[global_step] = torch.rad2deg(pitch_cur).cpu().numpy()
            actual_yaw[global_step] = torch.rad2deg(yaw_cur).cpu().numpy()

            lv = raw_env._robot.data.root_lin_vel_b
            lin_vel_x[global_step] = lv[:, 0].cpu().numpy()
            lin_vel_y[global_step] = lv[:, 1].cpu().numpy()
            lin_vel_z[global_step] = lv[:, 2].cpu().numpy()

            yaw_rate[global_step] = raw_env._robot.data.root_ang_vel_b[:, 2].cpu().numpy()
            action_mag[global_step] = torch.norm(actions, dim=-1).cpu().numpy()
            dr_step_idx[global_step] = dr_i

            # Termination tracking (attitude limit violation)
            dones_np = dones.squeeze(-1).bool().cpu().numpy() if dones.dim() > 1 else dones.bool().cpu().numpy()
            newly_terminated = dones_np & ~terminated_ever
            if newly_terminated.any():
                time_to_failure[newly_terminated] = time_s[global_step]
            terminated_ever |= dones_np
            terminated[global_step] = terminated_ever

        # Print status
        alive_mask = ~terminated_ever
        if alive_mask.any():
            t_end = (dr_i + 1) * steps_per_dr - 1
            r_err = np.sqrt(actual_roll[t_end, alive_mask] ** 2 + actual_pitch[t_end, alive_mask] ** 2)
            lv_n = np.sqrt(
                lin_vel_x[t_end, alive_mask] ** 2
                + lin_vel_y[t_end, alive_mask] ** 2
                + lin_vel_z[t_end, alive_mask] ** 2
            )
            yr = np.abs(yaw_rate[t_end, alive_mask])
            print(
                f"    att={np.mean(r_err):.2f}deg  "
                f"lin_vel={np.mean(lv_n):.4f}m/s  "
                f"yaw_rate={np.mean(yr):.4f}rad/s  "
                f"alive={alive_mask.sum()}/{num_envs}"
            )
        else:
            print("    All environments terminated.")
            break

    return {
        "time": time_s,
        "actual_roll_deg": actual_roll,
        "actual_pitch_deg": actual_pitch,
        "actual_yaw_deg": actual_yaw,
        "lin_vel_x": lin_vel_x,
        "lin_vel_y": lin_vel_y,
        "lin_vel_z": lin_vel_z,
        "yaw_rate": yaw_rate,
        "action_magnitude": action_mag,
        "dr_step_idx": dr_step_idx,
        "terminated": terminated,
        "time_to_failure": time_to_failure,
        "steps_per_dr": steps_per_dr,
        "step_duration": step_duration,
        "num_dr_steps": num_dr_steps,
    }


# ============================================================================
# Metrics
# ============================================================================


def _settling_time(signal: np.ndarray, threshold: float, step_dt: float) -> float:
    """Time from start until signal stays within threshold permanently.

    Args:
        signal: 1D array of absolute values (e.g. attitude error norm).
        threshold: Settling band (e.g. 1.0 deg).
        step_dt: Time per step.

    Returns:
        Settling time in seconds. NaN if never settles.
    """
    within = signal <= threshold
    # Find last step where signal exceeds threshold
    exceed_indices = np.where(~within)[0]
    if len(exceed_indices) == 0:
        return 0.0  # Already within threshold from the start
    last_exceed = exceed_indices[-1]
    if last_exceed >= len(signal) - 1:
        return float("nan")  # Never settles
    return (last_exceed + 1) * step_dt


def compute_metrics(data: dict) -> dict:
    """Compute per-DR-step and overall metrics.

    Per DR step:
        - SS error: mean error in last 50% of step (steady state)
        - Peak transient: max error in first 50% of step (overshoot)
        - Settling time: time to stay within threshold permanently
    """
    steps_per_dr = data["steps_per_dr"]
    num_dr_steps = data["num_dr_steps"]
    step_duration = data["step_duration"]
    terminated = data["terminated"]
    step_dt = data["time"][1] - data["time"][0] if len(data["time"]) > 1 else 0.02

    # Use last 50% of each DR step as steady state
    ss_start_frac = 0.5
    ss_start_offset = int(steps_per_dr * ss_start_frac)

    # Settling thresholds
    ATT_SETTLE_THRESH = 1.0   # deg
    LV_SETTLE_THRESH = 0.05   # m/s
    YR_SETTLE_THRESH = 0.02   # rad/s

    per_step_att_err = []
    per_step_lin_vel = []
    per_step_yaw_rate = []
    per_step_att_peak = []
    per_step_lv_peak = []
    per_step_yr_peak = []
    per_step_att_settle = []
    per_step_lv_settle = []
    per_step_yr_settle = []

    for dr_i in range(num_dr_steps):
        seg_s = dr_i * steps_per_dr
        seg_e = (dr_i + 1) * steps_per_dr
        ss_s = seg_s + ss_start_offset
        if ss_s >= len(data["time"]):
            break

        # Full segment signals (for peak / settling)
        roll_full = data["actual_roll_deg"][seg_s:seg_e]
        pitch_full = data["actual_pitch_deg"][seg_s:seg_e]
        att_full = np.sqrt(roll_full ** 2 + pitch_full ** 2)
        lv_full = np.sqrt(
            data["lin_vel_x"][seg_s:seg_e] ** 2
            + data["lin_vel_y"][seg_s:seg_e] ** 2
            + data["lin_vel_z"][seg_s:seg_e] ** 2
        )
        yr_full = np.abs(data["yaw_rate"][seg_s:seg_e])
        alive_full = ~terminated[seg_s:seg_e]

        # SS signals (last 50%)
        alive_ss = alive_full[ss_start_offset:]
        att_ss = att_full[ss_start_offset:]
        lv_ss = lv_full[ss_start_offset:]
        yr_ss = yr_full[ss_start_offset:]

        # -- SS error (mean in last 50%) --
        per_step_att_err.append(np.nanmean(np.where(alive_ss, att_ss, np.nan)))
        per_step_lin_vel.append(np.nanmean(np.where(alive_ss, lv_ss, np.nan)))
        per_step_yaw_rate.append(np.nanmean(np.where(alive_ss, yr_ss, np.nan)))

        # -- Peak transient (max in full segment, per-env mean) --
        att_peak = np.where(alive_full, att_full, np.nan)
        per_step_att_peak.append(np.nanmax(np.nanmean(att_peak, axis=1)))
        lv_peak = np.where(alive_full, lv_full, np.nan)
        per_step_lv_peak.append(np.nanmax(np.nanmean(lv_peak, axis=1)))
        yr_peak = np.where(alive_full, yr_full, np.nan)
        per_step_yr_peak.append(np.nanmax(np.nanmean(yr_peak, axis=1)))

        # -- Settling time (per-env mean signal) --
        att_mean_signal = np.nanmean(np.where(alive_full, att_full, np.nan), axis=1)
        per_step_att_settle.append(_settling_time(att_mean_signal, ATT_SETTLE_THRESH, step_dt))
        lv_mean_signal = np.nanmean(np.where(alive_full, lv_full, np.nan), axis=1)
        per_step_lv_settle.append(_settling_time(lv_mean_signal, LV_SETTLE_THRESH, step_dt))
        yr_mean_signal = np.nanmean(np.where(alive_full, yr_full, np.nan), axis=1)
        per_step_yr_settle.append(_settling_time(yr_mean_signal, YR_SETTLE_THRESH, step_dt))

    return {
        # SS error
        "per_step_att_err": np.array(per_step_att_err),
        "per_step_lin_vel": np.array(per_step_lin_vel),
        "per_step_yaw_rate": np.array(per_step_yaw_rate),
        "mean_att_err": np.nanmean(per_step_att_err),
        "mean_lin_vel": np.nanmean(per_step_lin_vel),
        "mean_yaw_rate": np.nanmean(per_step_yaw_rate),
        # Peak transient
        "per_step_att_peak": np.array(per_step_att_peak),
        "per_step_lv_peak": np.array(per_step_lv_peak),
        "per_step_yr_peak": np.array(per_step_yr_peak),
        "mean_att_peak": np.nanmean(per_step_att_peak),
        "mean_lv_peak": np.nanmean(per_step_lv_peak),
        "mean_yr_peak": np.nanmean(per_step_yr_peak),
        # Settling time
        "per_step_att_settle": np.array(per_step_att_settle),
        "per_step_lv_settle": np.array(per_step_lv_settle),
        "per_step_yr_settle": np.array(per_step_yr_settle),
        "mean_att_settle": np.nanmean(per_step_att_settle),
        "mean_lv_settle": np.nanmean(per_step_lv_settle),
        "mean_yr_settle": np.nanmean(per_step_yr_settle),
        # Thresholds (for reference)
        "att_settle_thresh": ATT_SETTLE_THRESH,
        "lv_settle_thresh": LV_SETTLE_THRESH,
        "yr_settle_thresh": YR_SETTLE_THRESH,
        # Survival
        "survival": (~data["terminated"][-1]).mean() * 100,
        "step_duration": step_duration,
    }


# ============================================================================
# Plotting
# ============================================================================


def generate_plots(data: dict, metrics: dict, output_dir: str) -> None:
    """Generate time-series and summary plots."""
    time_s = data["time"]
    steps_per_dr = data["steps_per_dr"]
    num_dr_steps = data["num_dr_steps"]
    step_dur = data["step_duration"]

    # Use env 0 for single-env plots
    env_idx = 0

    fig, axes = plt.subplots(5, 1, figsize=(14, 16), sharex=True)

    # DR step boundaries
    for ax in axes:
        for dr_i in range(1, num_dr_steps):
            t_boundary = dr_i * step_dur
            ax.axvline(t_boundary, color="gray", linestyle="--", alpha=0.4, linewidth=0.8)

    # 1. Roll & Pitch
    ax = axes[0]
    ax.plot(time_s, data["actual_roll_deg"][:, env_idx], label="Roll", color="#2196F3", linewidth=0.8)
    ax.plot(time_s, data["actual_pitch_deg"][:, env_idx], label="Pitch", color="#F44336", linewidth=0.8)
    ax.axhline(0, color="black", linestyle="-", alpha=0.3, linewidth=0.5)
    ax.set_ylabel("Attitude (deg)")
    ax.set_title("Attitude (Roll/Pitch) - Zero Command + DR Changes")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # 2. Linear velocity
    ax = axes[1]
    ax.plot(time_s, data["lin_vel_x"][:, env_idx], label="vx", color="#2196F3", linewidth=0.8)
    ax.plot(time_s, data["lin_vel_y"][:, env_idx], label="vy", color="#4CAF50", linewidth=0.8)
    ax.plot(time_s, data["lin_vel_z"][:, env_idx], label="vz", color="#F44336", linewidth=0.8)
    ax.axhline(0, color="black", linestyle="-", alpha=0.3, linewidth=0.5)
    ax.set_ylabel("Lin Vel (m/s)")
    ax.set_title("Linear Velocity (Body Frame)")
    ax.legend(loc="upper right", fontsize=8)
    ax.grid(True, alpha=0.3)

    # 3. Yaw rate
    ax = axes[2]
    ax.plot(time_s, data["yaw_rate"][:, env_idx], color="#9C27B0", linewidth=0.8)
    ax.axhline(0, color="black", linestyle="-", alpha=0.3, linewidth=0.5)
    ax.set_ylabel("Yaw Rate (rad/s)")
    ax.set_title("Yaw Rate (Body Frame)")
    ax.grid(True, alpha=0.3)

    # 4. Action magnitude
    ax = axes[3]
    ax.plot(time_s, data["action_magnitude"][:, env_idx], color="#FF9800", linewidth=0.8)
    ax.set_ylabel("Action Magnitude")
    ax.set_title("Action Norm")
    ax.grid(True, alpha=0.3)

    # 5. Attitude error norm
    ax = axes[4]
    att_err = np.sqrt(data["actual_roll_deg"][:, env_idx] ** 2 + data["actual_pitch_deg"][:, env_idx] ** 2)
    ax.plot(time_s, att_err, color="#F44336", linewidth=0.8)
    ax.axhline(0, color="black", linestyle="-", alpha=0.3, linewidth=0.5)
    ax.set_ylabel("Att Error (deg)")
    ax.set_xlabel("Time (s)")
    ax.set_title("Attitude Error Norm")
    ax.grid(True, alpha=0.3)

    # DR step labels
    for dr_i in range(num_dr_steps):
        t_mid = (dr_i + 0.5) * step_dur
        axes[0].text(t_mid, axes[0].get_ylim()[1], f"DR{dr_i}", ha="center", va="bottom", fontsize=7, color="gray")

    plt.tight_layout()
    path = os.path.join(output_dir, "dr_robustness_timeseries.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Saved: {path}")

    # Summary bar chart: 3x3 grid (rows: SS error, Peak transient, Settling time)
    fig, axes = plt.subplots(3, 3, figsize=(16, 12))

    x = np.arange(len(metrics["per_step_att_err"]))

    # Helper to draw a bar chart with mean line
    def _bar(ax, x, vals, mean_val, color, ylabel, title, fmt=".2f"):
        ax.bar(x, vals, color=color, alpha=0.7)
        ax.axhline(mean_val, color="black", linestyle="--", linewidth=1, label=f"Mean={mean_val:{fmt}}")
        ax.set_xlabel("DR Step")
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=7)
        ax.grid(True, alpha=0.3, axis="y")

    # Row 0: SS Error
    _bar(axes[0, 0], x, metrics["per_step_att_err"], metrics["mean_att_err"],
         "#F44336", "SS Att Error (deg)", "SS Attitude Error", ".2f")
    _bar(axes[0, 1], x, metrics["per_step_lin_vel"], metrics["mean_lin_vel"],
         "#2196F3", "SS Lin Vel (m/s)", "SS Linear Velocity", ".4f")
    _bar(axes[0, 2], x, metrics["per_step_yaw_rate"], metrics["mean_yaw_rate"],
         "#9C27B0", "SS Yaw Rate (rad/s)", "SS Yaw Rate", ".4f")

    # Row 1: Peak Transient
    _bar(axes[1, 0], x, metrics["per_step_att_peak"], metrics["mean_att_peak"],
         "#FF5722", "Peak Att (deg)", "Peak Transient (Attitude)", ".2f")
    _bar(axes[1, 1], x, metrics["per_step_lv_peak"], metrics["mean_lv_peak"],
         "#03A9F4", "Peak Lin Vel (m/s)", "Peak Transient (Lin Vel)", ".4f")
    _bar(axes[1, 2], x, metrics["per_step_yr_peak"], metrics["mean_yr_peak"],
         "#AB47BC", "Peak Yaw Rate (rad/s)", "Peak Transient (Yaw Rate)", ".4f")

    # Row 2: Settling Time
    att_thresh = metrics["att_settle_thresh"]
    lv_thresh = metrics["lv_settle_thresh"]
    yr_thresh = metrics["yr_settle_thresh"]
    _bar(axes[2, 0], x, metrics["per_step_att_settle"], metrics["mean_att_settle"],
         "#E57373", f"Settle Time (s) [<{att_thresh}d]", f"Settling Time (Att, <{att_thresh}deg)", ".2f")
    _bar(axes[2, 1], x, metrics["per_step_lv_settle"], metrics["mean_lv_settle"],
         "#64B5F6", f"Settle Time (s) [<{lv_thresh}]", f"Settling Time (Lin Vel, <{lv_thresh}m/s)", ".2f")
    _bar(axes[2, 2], x, metrics["per_step_yr_settle"], metrics["mean_yr_settle"],
         "#CE93D8", f"Settle Time (s) [<{yr_thresh}]", f"Settling Time (Yaw, <{yr_thresh}rad/s)", ".2f")

    plt.tight_layout()
    path = os.path.join(output_dir, "dr_robustness_summary.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Saved: {path}")


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
    env_cfg.play_mode = True
    env_cfg.vel_cmd_resample_steps = 0
    if hasattr(env_cfg, "observation_noise_model"):
        env_cfg.observation_noise_model = None
    env_cfg.max_attitude_angle = 2.5
    env_cfg.debug_vis = False
    env_cfg.seed = args_cli.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    if hasattr(env_cfg, "doraemon"):
        env_cfg.doraemon.enable = False

    # Episode must be long enough for all DR steps
    env_cfg.episode_length_s = args_cli.step_duration * args_cli.num_steps + 10.0

    # Start with hard DR (will be re-randomized each step)
    env_cfg.randomization = HardDomainRandomizationCfg()
    env_cfg.randomization.enable = True

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

    # ---- Load agent params from run directory ----
    run_agent_dict = None
    if resume_path:
        import yaml

        run_params_path = os.path.join(os.path.dirname(resume_path), "params", "agent.yaml")
        if os.path.isfile(run_params_path):
            try:
                with open(run_params_path) as f:
                    run_agent_dict = yaml.full_load(f)
                print(f"[INFO] Loaded agent params from: {run_params_path}")
            except yaml.YAMLError as e:
                print(f"[WARN] Could not load run agent params: {e}")
                run_agent_dict = None

    # ---- Output directory ----
    if args_cli.output_dir:
        output_dir = args_cli.output_dir
    elif resume_path:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr_robustness")
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = task_name.removeprefix("Isaac-").lower().replace("-", "_").removesuffix("_v0")
        output_dir = os.path.join("logs", "eval_dr_robustness", folder_name, ts)
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR override ----
    global _DORAEMON_FULL_DR
    if args_cli.doraemon_dr and resume_path:
        run_dir = os.path.dirname(resume_path)
        print(f"\n[INFO] Attempting to load DORAEMON-learned DR from: {run_dir}")
        cfg = load_doraemon_dr(run_dir)
        if cfg is not None:
            _DORAEMON_FULL_DR = cfg
            print("[INFO] Hard DR = DORAEMON-learned distribution (mean +/- 2*std).\n")
        else:
            print("[INFO] No DORAEMON state found. Falling back to HardDomainRandomizationCfg.\n")
    else:
        print("\n[INFO] DORAEMON-DR disabled. Hard DR = HardDomainRandomizationCfg (static).\n")

    # ---- Create env ----
    env = gym.make(args_cli.task, cfg=env_cfg)
    clip_actions = run_agent_dict.get("clip_actions") if run_agent_dict else agent_cfg.clip_actions
    env = RslRlVecEnvWrapper(env, clip_actions=clip_actions)

    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device

    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")
    print(f"[INFO] DR step duration: {args_cli.step_duration}s, num DR steps: {args_cli.num_steps}")
    print(f"[INFO] Total eval time: {args_cli.step_duration * args_cli.num_steps:.0f}s")

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

    # ---- Run evaluation ----
    dr_cfg = get_hard_dr_config()

    print(f"\n{'=' * 60}")
    print("  DR Robustness Evaluation: Zero Command + Periodic DR Changes")
    print(f"{'=' * 60}")

    data = run_robustness_eval(
        env=env,
        policy=policy,
        policy_nn=policy_nn,
        raw_env=raw_env,
        dr_cfg=dr_cfg,
        step_duration=args_cli.step_duration,
        num_dr_steps=args_cli.num_steps,
        step_dt=step_dt,
        num_envs=num_envs,
        device=device,
    )

    # Save raw data
    np.savez_compressed(
        os.path.join(output_dir, "eval_robustness.npz"),
        **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
    )

    # Compute metrics
    metrics = compute_metrics(data)

    print(f"\n{'=' * 80}")
    print("  RESULTS")
    print(f"{'=' * 80}")
    print(f"  [SS Error]       Att: {metrics['mean_att_err']:.2f} deg   "
          f"Lin Vel: {metrics['mean_lin_vel']:.4f} m/s   "
          f"Yaw Rate: {metrics['mean_yaw_rate']:.4f} rad/s")
    print(f"  [Peak Transient] Att: {metrics['mean_att_peak']:.2f} deg   "
          f"Lin Vel: {metrics['mean_lv_peak']:.4f} m/s   "
          f"Yaw Rate: {metrics['mean_yr_peak']:.4f} rad/s")
    print(f"  [Settling Time]  Att: {metrics['mean_att_settle']:.2f} s     "
          f"Lin Vel: {metrics['mean_lv_settle']:.2f} s       "
          f"Yaw Rate: {metrics['mean_yr_settle']:.2f} s")
    print(f"  [Survival]       {metrics['survival']:.0f}%")
    print()
    hdr = (f"  {'Step':>4}  {'SS Att':>8}  {'Peak Att':>9}  {'Settle':>7}  "
           f"{'SS LV':>8}  {'Peak LV':>8}  {'Settle':>7}  "
           f"{'SS YR':>8}  {'Peak YR':>8}  {'Settle':>7}")
    print(hdr)
    print(f"  {'-' * (len(hdr) - 2)}")
    for i in range(len(metrics["per_step_att_err"])):
        print(
            f"  {i:4d}  "
            f"{metrics['per_step_att_err'][i]:7.2f}d  "
            f"{metrics['per_step_att_peak'][i]:8.2f}d  "
            f"{metrics['per_step_att_settle'][i]:6.2f}s  "
            f"{metrics['per_step_lin_vel'][i]:7.4f}  "
            f"{metrics['per_step_lv_peak'][i]:7.4f}  "
            f"{metrics['per_step_lv_settle'][i]:6.2f}s  "
            f"{metrics['per_step_yaw_rate'][i]:7.4f}  "
            f"{metrics['per_step_yr_peak'][i]:7.4f}  "
            f"{metrics['per_step_yr_settle'][i]:6.2f}s"
        )

    # Generate plots
    print("\n[INFO] Generating plots...")
    generate_plots(data, metrics, output_dir)

    print(f"\nOutput saved to: {output_dir}")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
