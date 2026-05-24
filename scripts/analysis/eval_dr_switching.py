# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluate FullDOF-TRPO policy under mid-episode DR switching with zero command.

Purpose: Test DR-adaptation ability vs. command-tracking robustness (eval_dr_fulldof).
Command is held at zero throughout 50s; physics DR parameters (hydro/mass/payload/
ocean/thruster) are re-sampled every 5s at segment boundaries with a seeded RNG
so that r13_A and r13_B face identical DR draw sequences.

Trajectory: 10 segments x 5s = 50s. DR re-sampled at segs 1..9 (seg 0 uses reset-time DR).
Initial attitude: upright (no play_init_noise).

Outputs per DR level (none/soft/medium/hard):
    eval_<level>.npz: time, errors, lin_vel, yaw_rate, seg_boundaries
    switching_summary.json: per-seg per-env transient metrics
    attitude.png, lin_vel.png, yaw_rate.png: time-series with seg boundaries

Usage:
    ./isaaclab.sh -p scripts/analysis/eval_dr_switching.py \
        --task Isaac-FullDOF-TRPO-v0 --num_envs 64 --headless \
        --checkpoint <run_dir>/model_4999.pt
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))
sys.path.insert(0, os.path.dirname(__file__))

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

parser = argparse.ArgumentParser(description="Evaluate DR-switching adaptation of FullDOF-TRPO policies.")
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0")
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--output_dir", type=str, default=None)
parser.add_argument("--segment_duration", type=float, default=5.0)
parser.add_argument("--num_segments", type=int, default=10)
parser.add_argument("--seed", type=int, default=42, help="Master seed shared across runs for identical DR draws.")
parser.add_argument("--kp_pos", type=float, default=0.5, help="Outer-loop position P-gain (s^-1). vel_cmd = clip(Kp_pos * pos_err, ±vel_sat).")
parser.add_argument("--kp_yaw", type=float, default=0.5, help="Outer-loop yaw P-gain (s^-1). yaw_rate_cmd = clip(Kp_yaw * yaw_err, ±yaw_rate_sat).")
parser.add_argument("--vel_sat", type=float, default=0.25, help="Velocity command saturation (m/s). Matches training range.")
parser.add_argument("--yaw_rate_sat", type=float, default=0.25, help="Yaw rate command saturation (rad/s).")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--doraemon-dr", action=argparse.BooleanOptionalAction, default=True)
# Student-policy mode (optional)
parser.add_argument("--student_ckpt", type=str, default=None,
                    help="If set, run with student encoder + frozen teacher actor instead of teacher runner.")
parser.add_argument("--teacher_ckpt", type=str, default=None,
                    help="Teacher r13_A model_*.pt path (required when --student_ckpt is given).")
parser.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], default=None,
                    help="Student encoder type (required when --student_ckpt is given).")
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

from datetime import datetime
import json

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
from isaaclab.utils.math import euler_xyz_from_quat, quat_rotate_inverse

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

from common import DR_LEVELS, DR_COLORS, DR_SCALE

# ---------------------------------------------------------------------------
# DR config builders (inlined from eval_dr_fulldof to avoid double-AppLauncher)
# ---------------------------------------------------------------------------

_DORAEMON_FULL_DR: DomainRandomizationCfg | None = None
_DORAEMON_RAW: dict[str, tuple[float, float]] = {}

_DORAEMON_TO_DR_FIELD: dict[str, str] = {
    "payload_mass": "payload_mass_range",
    "water_density": "water_density_range",
}

_DR_TUPLE_FIELDS = [
    "added_mass_scale", "linear_damping_scale", "quadratic_damping_scale", "volume_scale",
    "cob_offset_x", "cob_offset_y", "cob_offset_z",
    "cog_offset_x", "cog_offset_y", "cog_offset_z",
    "inertia_scale", "body_mass_scale", "water_density_range",
    "joint_stiffness_range", "joint_damping_range", "yaw_damping_scale",
    "joint_effort_limit_range", "joint_static_friction_range", "joint_viscous_friction_range",
    "payload_mass_range", "payload_cog_offset_z",
    "thrust_coefficient_scale", "time_constant_scale",
    "ocean_current_strength_range",
]
_DR_FLOAT_FIELDS = ["payload_cog_offset_xy_radius", "buoy_moment_arm"]

_TRUE_NOMINAL_PHYSICS: dict[str, float] = {
    "added_mass_scale": 1.0, "linear_damping_scale": 1.0, "quadratic_damping_scale": 1.0,
    "volume_scale": 1.0, "inertia_scale": 1.0, "body_mass_scale": 1.0,
    "yaw_damping_scale": 1.0, "joint_effort_limit_range": 1.0,
    "thrust_coefficient_scale": 1.0, "time_constant_scale": 1.0,
    "cob_offset_x": 0.0, "cob_offset_y": 0.0, "cob_offset_z": 0.0,
    "cog_offset_x": 0.0, "cog_offset_y": 0.0, "cog_offset_z": 0.0,
    "water_density_range": 1000.0,
    "payload_mass_range": 0.0, "payload_cog_offset_z": 0.0,
    "joint_static_friction_range": 0.0, "joint_viscous_friction_range": 0.0,
    "payload_cog_offset_xy_radius": 0.0,
    "ocean_current_strength_range": 0.0,
}


def _make_nominal_dr() -> DomainRandomizationCfg:
    base = DomainRandomizationCfg()
    nominal = DomainRandomizationCfg()
    for f in _DR_TUPLE_FIELDS:
        if f in _TRUE_NOMINAL_PHYSICS:
            v = _TRUE_NOMINAL_PHYSICS[f]
            setattr(nominal, f, (v, v))
        else:
            lo, hi = getattr(base, f)
            setattr(nominal, f, ((lo + hi) / 2.0, (lo + hi) / 2.0))
    for f in _DR_FLOAT_FIELDS:
        if f in _TRUE_NOMINAL_PHYSICS:
            setattr(nominal, f, _TRUE_NOMINAL_PHYSICS[f])
    return nominal


def build_dr_config(scale: float) -> DomainRandomizationCfg:
    nominal = _make_nominal_dr()
    if scale <= 0.0:
        nominal.enable = True
        return nominal
    full = _DORAEMON_FULL_DR if _DORAEMON_FULL_DR is not None else HardDomainRandomizationCfg()
    f = min(scale, 1.0)
    cfg = DomainRandomizationCfg()
    cfg.enable = True
    for fld in _DR_TUPLE_FIELDS:
        nom = getattr(nominal, fld)
        fu = getattr(full, fld)
        setattr(cfg, fld, (nom[0] + f * (fu[0] - nom[0]), nom[1] + f * (fu[1] - nom[1])))
    for fld in _DR_FLOAT_FIELDS:
        nom = getattr(nominal, fld)
        fu = getattr(full, fld)
        setattr(cfg, fld, nom + f * (fu - nom))
    return cfg


def apply_dr_config(env_cfg, scale: float) -> None:
    env_cfg.randomization = build_dr_config(scale)


def load_doraemon_dr(run_dir: str) -> tuple[DomainRandomizationCfg | None, dict[str, tuple[float, float]]]:
    from tensorboard.backend.event_processing import event_accumulator
    if not os.path.isdir(run_dir):
        return None, {}
    try:
        ea = event_accumulator.EventAccumulator(run_dir)
        ea.Reload()
        all_tags = set(ea.Tags().get("scalars", []))
    except Exception as e:
        print(f"[WARN] Could not load TB events: {e}")
        return None, {}
    if not any(t.startswith("DORAEMON/mean/") for t in all_tags):
        return None, {}
    cfg = HardDomainRandomizationCfg()
    cfg.enable = True
    runtime_specs = build_param_specs(cfg)
    raw: dict[str, tuple[float, float]] = {}
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
        field_name = mapped if mapped is not None else spec.name
        if not hasattr(cfg, field_name):
            continue
        setattr(cfg, field_name, (lo, hi))
        raw[field_name] = (mean_val, std_val)
    return cfg, raw

_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
_runner_module.FullDOFConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.FullDOFConstraintTRPO = ConstraintTRPO


# ---------------------------------------------------------------------------
# Evaluation loop
# ---------------------------------------------------------------------------

def run_switching_eval(
    env, policy, policy_nn, raw_env,
    num_segments: int, segment_duration: float, step_dt: float,
    num_envs: int, device, master_seed: int,
) -> dict:
    """Run one DR-switching evaluation pass with zero command.

    DR draws are deterministic: at each seg boundary i>=1, torch.manual_seed
    is set to ``master_seed + i`` before calling randomize_physics_mid_episode.
    This makes the DR sequence reproducible across runs (r13_A vs r13_B same draw).
    """
    steps_per_seg = int(segment_duration / step_dt)
    total_steps = steps_per_seg * num_segments
    time_s = np.arange(total_steps) * step_dt

    actual_roll = np.zeros((total_steps, num_envs))
    actual_pitch = np.zeros((total_steps, num_envs))
    actual_yaw = np.zeros((total_steps, num_envs))
    error_roll = np.zeros((total_steps, num_envs))
    error_pitch = np.zeros((total_steps, num_envs))
    # World-frame position drift from reset origin (target xyz=0)
    pos_x = np.zeros((total_steps, num_envs))
    pos_y = np.zeros((total_steps, num_envs))
    pos_z = np.zeros((total_steps, num_envs))
    # Body-frame velocity kept for diagnosis but NOT the primary metric
    lin_vel_x = np.zeros((total_steps, num_envs))
    lin_vel_y = np.zeros((total_steps, num_envs))
    lin_vel_z = np.zeros((total_steps, num_envs))
    yaw_rate = np.zeros((total_steps, num_envs))
    action_magnitude = np.zeros((total_steps, num_envs))
    terminated = np.zeros((total_steps, num_envs), dtype=bool)
    time_to_failure = np.full(num_envs, float("nan"))

    # Per-env reset origin (env origin in world frame). Position drift = actual - origin.
    env_origins = raw_env.scene.env_origins.cpu().numpy()  # (num_envs, 3)

    # Force full reset via throwaway step (applies initial DR draw = seg 0 DR)
    torch.manual_seed(master_seed)
    raw_env.episode_length_buf[:] = raw_env.max_episode_length
    obs = env.get_observations()
    with torch.inference_mode():
        obs, _, _, _ = env.step(policy(obs))
        if hasattr(policy_nn, "reset"):
            policy_nn.reset(torch.ones(num_envs, 1, dtype=torch.bool, device=device))
    raw_env.episode_length_buf[:] = 0

    terminated_ever = np.zeros(num_envs, dtype=bool)
    all_env_ids = torch.arange(num_envs, device=device)
    seg_boundaries = []  # step indices where DR switched

    # Cascade PID setup
    origin_t = raw_env.scene.env_origins  # (N, 3)
    kp_pos = float(args_cli.kp_pos)
    kp_yaw = float(args_cli.kp_yaw)
    vel_sat = float(args_cli.vel_sat)
    yaw_rate_sat = float(args_cli.yaw_rate_sat)
    # Logs for commands sent to policy
    vel_cmd_x = np.zeros((total_steps, num_envs))
    vel_cmd_y = np.zeros((total_steps, num_envs))
    vel_cmd_z = np.zeros((total_steps, num_envs))
    yaw_rate_cmd_arr = np.zeros((total_steps, num_envs))

    for step_idx in range(total_steps):
        # Cascade PID outer loop: target xyz=0, yaw=0 (all in world frame rel to env origin)
        pos_w = raw_env._robot.data.root_pos_w
        quat_w = raw_env._robot.data.root_quat_w
        pos_err_w = origin_t - pos_w   # drive robot back toward origin
        pos_err_b = quat_rotate_inverse(quat_w, pos_err_w)  # rotate to body frame
        vel_cmd = torch.clamp(kp_pos * pos_err_b, -vel_sat, vel_sat)
        _, _, yaw_w = euler_xyz_from_quat(quat_w)
        yaw_err = torch.atan2(torch.sin(-yaw_w), torch.cos(-yaw_w))  # wrap (0 - yaw)
        yaw_rate_cmd = torch.clamp(kp_yaw * yaw_err, -yaw_rate_sat, yaw_rate_sat)

        # Roll/pitch target = 0; yaw_rate = outer-loop output; vel_cmd = outer-loop output
        raw_env._ang_cmd[:, 0] = 0.0
        raw_env._ang_cmd[:, 1] = 0.0
        raw_env._ang_cmd[:, 2] = yaw_rate_cmd
        raw_env._vel_cmd_lin[:, 0] = vel_cmd[:, 0]
        raw_env._vel_cmd_lin[:, 1] = vel_cmd[:, 1]
        raw_env._vel_cmd_lin[:, 2] = vel_cmd[:, 2]
        vel_cmd_x[step_idx] = vel_cmd[:, 0].cpu().numpy()
        vel_cmd_y[step_idx] = vel_cmd[:, 1].cpu().numpy()
        vel_cmd_z[step_idx] = vel_cmd[:, 2].cpu().numpy()
        yaw_rate_cmd_arr[step_idx] = yaw_rate_cmd.cpu().numpy()

        # DR switch at every segment boundary (except step 0 = reset-time DR)
        if step_idx > 0 and step_idx % steps_per_seg == 0:
            seg_idx = step_idx // steps_per_seg
            torch.manual_seed(master_seed + seg_idx)
            raw_env.randomize_physics_mid_episode(env_ids=all_env_ids)
            seg_boundaries.append(step_idx)

        with torch.inference_mode():
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            if hasattr(policy_nn, "reset"):
                policy_nn.reset(dones)

        action_magnitude[step_idx] = torch.norm(actions, dim=-1).cpu().numpy()
        roll_cur, pitch_cur, yaw_cur = euler_xyz_from_quat(raw_env._robot.data.root_quat_w)
        actual_roll[step_idx] = torch.rad2deg(roll_cur).cpu().numpy()
        actual_pitch[step_idx] = torch.rad2deg(pitch_cur).cpu().numpy()
        # Wrap yaw to [-180, 180]
        yaw_deg = torch.rad2deg(yaw_cur).cpu().numpy()
        actual_yaw[step_idx] = (yaw_deg + 180) % 360 - 180

        # World-frame position drift from env origin
        pos_w = raw_env._robot.data.root_pos_w.cpu().numpy()
        pos_x[step_idx] = pos_w[:, 0] - env_origins[:, 0]
        pos_y[step_idx] = pos_w[:, 1] - env_origins[:, 1]
        pos_z[step_idx] = pos_w[:, 2] - env_origins[:, 2]

        att_err = raw_env._att_rp_err
        error_roll[step_idx] = torch.rad2deg(att_err[:, 0]).cpu().numpy()
        error_pitch[step_idx] = torch.rad2deg(att_err[:, 1]).cpu().numpy()

        lv = raw_env._robot.data.root_lin_vel_b
        lin_vel_x[step_idx] = lv[:, 0].cpu().numpy()
        lin_vel_y[step_idx] = lv[:, 1].cpu().numpy()
        lin_vel_z[step_idx] = lv[:, 2].cpu().numpy()
        yaw_rate[step_idx] = raw_env._robot.data.root_ang_vel_b[:, 2].cpu().numpy()

        dones_np = dones.squeeze(-1).bool().cpu().numpy() if dones.dim() > 1 else dones.bool().cpu().numpy()
        newly_terminated = dones_np & ~terminated_ever
        if newly_terminated.any():
            time_to_failure[newly_terminated] = time_s[step_idx]
        terminated_ever |= dones_np
        terminated[step_idx] = terminated_ever

        if (step_idx + 1) % steps_per_seg == 0:
            seg_idx = step_idx // steps_per_seg
            err_norm = np.sqrt(error_roll[step_idx] ** 2 + error_pitch[step_idx] ** 2)
            mean_err = np.mean(err_norm[~terminated_ever]) if (~terminated_ever).any() else float("nan")
            print(f"  seg {seg_idx + 1:2d}/{num_segments} done @ t={time_s[step_idx]:.1f}s: att_err={mean_err:.2f}° alive={num_envs - terminated_ever.sum()}/{num_envs}")

    return {
        "time": time_s,
        "actual_roll_deg": actual_roll,
        "actual_pitch_deg": actual_pitch,
        "actual_yaw_deg": actual_yaw,
        "error_roll": error_roll,
        "error_pitch": error_pitch,
        "pos_x": pos_x,
        "pos_y": pos_y,
        "pos_z": pos_z,
        "lin_vel_x": lin_vel_x,
        "lin_vel_y": lin_vel_y,
        "lin_vel_z": lin_vel_z,
        "yaw_rate": yaw_rate,
        "vel_cmd_x": vel_cmd_x,
        "vel_cmd_y": vel_cmd_y,
        "vel_cmd_z": vel_cmd_z,
        "yaw_rate_cmd": yaw_rate_cmd_arr,
        "action_magnitude": action_magnitude,
        "terminated": terminated,
        "time_to_failure": time_to_failure,
        "steps_per_segment": steps_per_seg,
        "segment_duration": segment_duration,
        "num_segments": num_segments,
        "seg_boundaries": np.array(seg_boundaries, dtype=np.int64),
    }


# ---------------------------------------------------------------------------
# Metrics (per-seg transient)
# ---------------------------------------------------------------------------

def compute_seg_metrics(data: dict) -> dict:
    """Per-seg per-env transient metrics after DR switch.

    Each seg (except seg 0) represents "DR just changed, policy must adapt".
    Seg 0 is a baseline: initial DR, no switch yet.

    Primary metrics (target = xyz=0, rpy=0):
        pos_drift_norm_peak: max sqrt(x^2+y^2+z^2) within seg (transient)
        pos_drift_norm_ss:   mean of last 50% (DC offset after transient)
        yaw_drift_deg_peak / ss: |yaw| (already wrapped to [-180,180])
        peak_roll_deg / ss_roll_deg: |roll| peak/ss (attitude is a directly-logged view)
        peak_pitch_deg / ss_pitch_deg: |pitch|
    """
    steps_per_seg = data["steps_per_segment"]
    num_segs = data["num_segments"]
    seg_duration = data["segment_duration"]
    num_envs = data["actual_roll_deg"].shape[1]

    per_seg = []
    for seg in range(num_segs):
        s = seg * steps_per_seg
        e = (seg + 1) * steps_per_seg
        roll_abs = np.abs(data["actual_roll_deg"][s:e])
        pitch_abs = np.abs(data["actual_pitch_deg"][s:e])
        yaw_abs = np.abs(data["actual_yaw_deg"][s:e])
        pos_norm = np.sqrt(
            data["pos_x"][s:e] ** 2 + data["pos_y"][s:e] ** 2 + data["pos_z"][s:e] ** 2
        )
        half = steps_per_seg // 2

        per_seg.append({
            "seg_idx": seg,
            # Attitude |err| from 0
            "peak_roll_deg": roll_abs.max(axis=0).tolist(),
            "peak_pitch_deg": pitch_abs.max(axis=0).tolist(),
            "peak_yaw_deg": yaw_abs.max(axis=0).tolist(),
            "ss_roll_deg": roll_abs[half:].mean(axis=0).tolist(),
            "ss_pitch_deg": pitch_abs[half:].mean(axis=0).tolist(),
            "ss_yaw_deg": yaw_abs[half:].mean(axis=0).tolist(),
            # Position drift from xyz=0
            "pos_drift_peak": pos_norm.max(axis=0).tolist(),
            "pos_drift_ss": pos_norm[half:].mean(axis=0).tolist(),
            "pos_x_ss": data["pos_x"][s:e][half:].mean(axis=0).tolist(),
            "pos_y_ss": data["pos_y"][s:e][half:].mean(axis=0).tolist(),
            "pos_z_ss": data["pos_z"][s:e][half:].mean(axis=0).tolist(),
        })

    return {"per_seg": per_seg, "num_envs": num_envs, "num_segments": num_segs}


# ---------------------------------------------------------------------------
# Plots
# ---------------------------------------------------------------------------

def _plot_trajectory(all_data: dict, levels: list[str], channel: str, ylabel: str, title: str, output_dir: str, filename: str) -> None:
    """Per-DR-level time-series with seg boundaries as vertical dashed lines."""
    fig, axes = plt.subplots(len(levels), 1, figsize=(12, 2.4 * len(levels)), sharex=True)
    if len(levels) == 1:
        axes = [axes]
    fig.suptitle(title, fontsize=13)

    for i, lvl in enumerate(levels):
        ax = axes[i]
        d = all_data[lvl]
        t = d["time"]
        if channel == "att":
            # Plot roll and pitch err per-env mean +/- std
            err_r = d["error_roll"]
            err_p = d["error_pitch"]
            mean_r = err_r.mean(axis=1)
            std_r = err_r.std(axis=1)
            mean_p = err_p.mean(axis=1)
            std_p = err_p.std(axis=1)
            ax.plot(t, mean_r, color="C0", label="roll err", linewidth=1.2)
            ax.fill_between(t, mean_r - std_r, mean_r + std_r, color="C0", alpha=0.2)
            ax.plot(t, mean_p, color="C1", label="pitch err", linewidth=1.2)
            ax.fill_between(t, mean_p - std_p, mean_p + std_p, color="C1", alpha=0.2)
        elif channel == "lv":
            for j, (key, name, col) in enumerate([("lin_vel_x", "vx", "C0"), ("lin_vel_y", "vy", "C1"), ("lin_vel_z", "vz", "C2")]):
                arr = d[key]
                m, s = arr.mean(axis=1), arr.std(axis=1)
                ax.plot(t, m, color=col, label=name, linewidth=1.0)
                ax.fill_between(t, m - s, m + s, color=col, alpha=0.15)
        elif channel == "yaw":
            arr = d["yaw_rate"]
            m, s = arr.mean(axis=1), arr.std(axis=1)
            ax.plot(t, m, color="C0", label="yaw_rate", linewidth=1.2)
            ax.fill_between(t, m - s, m + s, color="C0", alpha=0.2)
        # Seg boundaries
        for b_step in d["seg_boundaries"]:
            ax.axvline(t[b_step], color="red", linestyle="--", alpha=0.4, linewidth=0.7)
        ax.axhline(0.0, color="black", linewidth=0.5, alpha=0.3)
        ax.set_ylabel(ylabel, fontsize=9)
        ax.set_title(f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%)", color=DR_COLORS[lvl], fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, filename), dpi=150)
    plt.close(fig)


def _plot_position_drift(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Per-DR-level time-series of xyz drift from target=0, with seg boundaries."""
    fig, axes = plt.subplots(len(levels), 1, figsize=(12, 2.2 * len(levels)), sharex=True)
    if len(levels) == 1:
        axes = [axes]
    fig.suptitle("Position Drift from Target xyz=0 (cascade PID, DR switching)", fontsize=13)
    for i, lvl in enumerate(levels):
        ax = axes[i]
        d = all_data[lvl]
        t = d["time"]
        for key, name, col in [("pos_x", "x", "C0"), ("pos_y", "y", "C1"), ("pos_z", "z", "C2")]:
            arr = d[key]
            m, s = arr.mean(axis=1), arr.std(axis=1)
            ax.plot(t, m, color=col, label=name, linewidth=1.1)
            ax.fill_between(t, m - s, m + s, color=col, alpha=0.15)
        for b in d["seg_boundaries"]:
            ax.axvline(t[b], color="red", linestyle="--", alpha=0.4, linewidth=0.7)
        ax.axhline(0.0, color="black", linewidth=0.5, alpha=0.3)
        ax.set_ylabel("drift (m)")
        ax.set_title(f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%)", color=DR_COLORS[lvl], fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "pos_drift.png"), dpi=150)
    plt.close(fig)


def _plot_attitude_drift(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Per-DR-level roll/pitch/yaw drift from target rpy=0, env mean ± std, seg boundaries.

    Analogous to pos_drift.png but for attitude. Single plot with all three angles.
    """
    fig, axes = plt.subplots(len(levels), 1, figsize=(12, 2.4 * len(levels)), sharex=True)
    if len(levels) == 1:
        axes = [axes]
    fig.suptitle("Attitude Drift from Target rpy=0 (cascade PID, DR switching)", fontsize=13)
    for i, lvl in enumerate(levels):
        ax = axes[i]
        d = all_data[lvl]
        t = d["time"]
        for key, name, col in [("actual_roll_deg", "roll", "C0"),
                                ("actual_pitch_deg", "pitch", "C1"),
                                ("actual_yaw_deg", "yaw", "C2")]:
            arr = d[key]
            m, s = arr.mean(axis=1), arr.std(axis=1)
            ax.plot(t, m, color=col, label=name, linewidth=1.1)
            ax.fill_between(t, m - s, m + s, color=col, alpha=0.15)
        for b in d["seg_boundaries"]:
            ax.axvline(t[b], color="red", linestyle="--", alpha=0.4, linewidth=0.7)
        ax.axhline(0.0, color="black", linewidth=0.5, alpha=0.3)
        ax.set_ylabel("angle (deg)")
        ax.set_title(f"{lvl} (DR {int(DR_SCALE[lvl] * 100)}%)", color=DR_COLORS[lvl], fontsize=10)
        ax.legend(fontsize=8, loc="upper right")
        ax.grid(True, alpha=0.3)
    axes[-1].set_xlabel("Time (s)")
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "att_drift.png"), dpi=150)
    plt.close(fig)


def _collect_metric_across_levels(all_metrics: dict, levels: list[str], key: str, stat: str = "mean") -> tuple[list, list]:
    """Aggregate a per-seg per-env metric across DR levels, ignoring seg 0 (initial transient).

    Returns (means, stds) per DR level, where the statistic is computed over the
    union of all post-switch envs (segs 1..N, all envs).
    """
    means, stds = [], []
    for lvl in levels:
        m = all_metrics[lvl]
        num_segs = m["num_segments"]
        # Concatenate across all post-switch envs (segs 1..N)
        vals = np.concatenate([np.array(m["per_seg"][s][key]) for s in range(1, num_segs)])
        if stat == "mean":
            means.append(float(np.nanmean(vals)))
            stds.append(float(np.nanstd(vals)))
        elif stat == "max":
            means.append(float(np.nanmax(vals)))
            stds.append(0.0)
    return means, stds


def _bar_subplot(ax, x, heights, colors, xlabels, ylabel, title, yerr=None, ylim=None):
    ax.bar(x, heights, color=colors, yerr=yerr, capsize=4, edgecolor="black", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if ylim:
        ax.set_ylim(ylim)
    ax.grid(True, alpha=0.3, axis="y")


def _plot_summary_pos(all_metrics: dict, all_data: dict, levels: list[str], output_dir: str) -> None:
    """Position summary (eval_dr style): bar chart across DR levels."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.suptitle("Position Summary (target xyz=0, DR switching)", fontsize=14)
    x = np.arange(len(levels))
    colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0) Peak drift norm per seg (env mean ± std)
    m, s = _collect_metric_across_levels(all_metrics, levels, "pos_drift_peak")
    _bar_subplot(axes[0, 0], x, m, colors, xlabels, "Drift (m)", "Peak Pos Drift per Seg", yerr=s)
    # (0,1) SS drift norm per seg
    m, s = _collect_metric_across_levels(all_metrics, levels, "pos_drift_ss")
    _bar_subplot(axes[0, 1], x, m, colors, xlabels, "Drift (m)", "SS Pos Drift (last 50% of seg)", yerr=s)

    # (1,0..2) SS DC offset per axis (signed mean to reveal systematic bias)
    for ci, (key, ax_name) in enumerate([("pos_x_ss", "X"), ("pos_y_ss", "Y"), ("pos_z_ss", "Z")]):
        row, col = divmod(1 + ci, 2)
        if row >= axes.shape[0]:
            break
        m, s = _collect_metric_across_levels(all_metrics, levels, key)
        _bar_subplot(axes[row, col], x, m, colors, xlabels, f"{ax_name} drift (m, signed)",
                     f"{ax_name}-axis SS Bias (env mean)", yerr=s)

    # (2,1) Heavy-tail: % envs with peak drift > 0.1 m per seg
    pct = []
    for lvl in levels:
        mm = all_metrics[lvl]
        vals = np.concatenate([np.array(mm["per_seg"][s]["pos_drift_peak"]) for s in range(1, mm["num_segments"])])
        pct.append(100.0 * (vals > 0.1).mean())
    _bar_subplot(axes[2, 1], x, pct, colors, xlabels, "% env×seg", "Heavy-tail: %env peak>0.1m")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_pos.png"), dpi=150)
    plt.close(fig)


def _plot_summary_attitude(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Attitude summary (eval_dr style): bar chart across DR levels, per-axis grouping."""
    fig, axes = plt.subplots(3, 2, figsize=(12, 12))
    fig.suptitle("Attitude Summary (target rpy=0, DR switching)", fontsize=14)
    x = np.arange(len(levels))
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]
    ax_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # roll / pitch / yaw

    def _grouped_bar(ax, key, ylabel, title):
        axis_names = ["peak_roll_deg", "peak_pitch_deg", "peak_yaw_deg"] if "peak" in key else \
                     ["ss_roll_deg", "ss_pitch_deg", "ss_yaw_deg"]
        bw = 0.25
        for ai, metric_key in enumerate(axis_names):
            vals, _ = _collect_metric_across_levels(all_metrics, levels, metric_key)
            offs = (ai - 1) * bw
            ax.bar(x + offs, vals, bw, color=ax_colors[ai], label=metric_key.replace("peak_", "").replace("ss_", "").replace("_deg", ""))
        ax.set_xticks(x)
        ax.set_xticklabels(xlabels, fontsize=9)
        ax.set_ylabel(ylabel)
        ax.set_title(title)
        ax.legend(fontsize=8)
        ax.grid(True, alpha=0.3, axis="y")

    _grouped_bar(axes[0, 0], "peak", "Peak (deg)", "Peak |angle| per Seg (transient)")
    _grouped_bar(axes[0, 1], "ss", "SS |angle| (deg)", "SS |angle| (last 50% of seg)")

    # Heavy-tail: % envs with peak roll > 5° (attitude blow-up)
    colors_single = [DR_COLORS[lvl] for lvl in levels]
    pct_r = [100.0 * (np.concatenate([np.array(all_metrics[lvl]["per_seg"][s]["peak_roll_deg"])
                                       for s in range(1, all_metrics[lvl]["num_segments"])]) > 5.0).mean()
             for lvl in levels]
    pct_p = [100.0 * (np.concatenate([np.array(all_metrics[lvl]["per_seg"][s]["peak_pitch_deg"])
                                       for s in range(1, all_metrics[lvl]["num_segments"])]) > 5.0).mean()
             for lvl in levels]
    pct_y = [100.0 * (np.concatenate([np.array(all_metrics[lvl]["per_seg"][s]["peak_yaw_deg"])
                                       for s in range(1, all_metrics[lvl]["num_segments"])]) > 5.0).mean()
             for lvl in levels]
    _bar_subplot(axes[1, 0], x, pct_r, colors_single, xlabels, "% env×seg", "Heavy-tail: %env roll peak>5°")
    _bar_subplot(axes[1, 1], x, pct_p, colors_single, xlabels, "% env×seg", "Heavy-tail: %env pitch peak>5°")
    _bar_subplot(axes[2, 0], x, pct_y, colors_single, xlabels, "% env×seg", "Heavy-tail: %env yaw peak>5°")

    # Worst-seg peak (max across all segs, all envs)
    worst_r, _ = _collect_metric_across_levels(all_metrics, levels, "peak_roll_deg", stat="max")
    worst_p, _ = _collect_metric_across_levels(all_metrics, levels, "peak_pitch_deg", stat="max")
    worst_y, _ = _collect_metric_across_levels(all_metrics, levels, "peak_yaw_deg", stat="max")
    bw = 0.25
    axes[2, 1].bar(x - bw, worst_r, bw, color=ax_colors[0], label="roll")
    axes[2, 1].bar(x,       worst_p, bw, color=ax_colors[1], label="pitch")
    axes[2, 1].bar(x + bw, worst_y, bw, color=ax_colors[2], label="yaw")
    axes[2, 1].set_xticks(x)
    axes[2, 1].set_xticklabels(xlabels, fontsize=9)
    axes[2, 1].set_ylabel("Worst peak (deg)")
    axes[2, 1].set_title("Worst-case env×seg Peak")
    axes[2, 1].legend(fontsize=8)
    axes[2, 1].grid(True, alpha=0.3, axis="y")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_att.png"), dpi=150)
    plt.close(fig)


def _plot_transient_overlay(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Overlaid post-switch transient profiles across all DR levels.

    For each DR level, align seg boundaries (t=0 = switch moment) and overlay
    all post-switch windows. Shows how fast and how far the policy drifts after
    each DR change, averaged across segs 1..N.
    """
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Post-Switch Transient (aligned at DR change, segs 1..N mean ± std)", fontsize=13)

    for lvl in levels:
        d = all_data[lvl]
        steps_per_seg = d["steps_per_segment"]
        num_segs = d["num_segments"]
        seg_dur = d["segment_duration"]
        step_dt = seg_dur / steps_per_seg
        t_seg = np.arange(steps_per_seg) * step_dt

        pos_norm_full = np.sqrt(d["pos_x"] ** 2 + d["pos_y"] ** 2 + d["pos_z"] ** 2)
        roll_abs = np.abs(d["actual_roll_deg"])
        pitch_abs = np.abs(d["actual_pitch_deg"])
        yaw_abs = np.abs(d["actual_yaw_deg"])

        pos_curves, roll_curves, pitch_curves, yaw_curves = [], [], [], []
        for s in range(1, num_segs):
            a, b = s * steps_per_seg, (s + 1) * steps_per_seg
            pos_curves.append(pos_norm_full[a:b].mean(axis=1))
            roll_curves.append(roll_abs[a:b].mean(axis=1))
            pitch_curves.append(pitch_abs[a:b].mean(axis=1))
            yaw_curves.append(yaw_abs[a:b].mean(axis=1))

        def _draw(ax, curves, ylabel):
            curves_arr = np.array(curves)
            m_ = curves_arr.mean(axis=0)
            s_ = curves_arr.std(axis=0)
            ax.plot(t_seg, m_, color=DR_COLORS[lvl], label=lvl, linewidth=1.8)
            ax.fill_between(t_seg, m_ - s_, m_ + s_, color=DR_COLORS[lvl], alpha=0.15)
            ax.set_xlabel("t since DR switch (s)")
            ax.set_ylabel(ylabel)
            ax.grid(True, alpha=0.3)

        _draw(axes[0, 0], pos_curves, "pos drift (m)")
        _draw(axes[0, 1], roll_curves, "|roll| (deg)")
        _draw(axes[1, 0], pitch_curves, "|pitch| (deg)")
        _draw(axes[1, 1], yaw_curves, "|yaw| (deg)")

    axes[0, 0].set_title("Position drift from 0")
    axes[0, 1].set_title("Roll |angle|")
    axes[1, 0].set_title("Pitch |angle|")
    axes[1, 1].set_title("Yaw |angle|")
    for ax in axes.flat:
        ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "transient_overlay.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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
    # Upright init (no attitude noise)
    if hasattr(env_cfg, "play_init_attitude_noise_deg"):
        env_cfg.play_init_attitude_noise_deg = 0.0
        env_cfg.play_init_yaw_noise_deg = 0.0

    total_s = args_cli.num_segments * args_cli.segment_duration
    env_cfg.episode_length_s = total_s + 10.0

    # Checkpoint -- student mode short-circuits teacher-runner checkpoint search
    is_student_mode = args_cli.student_ckpt is not None
    if is_student_mode:
        if args_cli.teacher_ckpt is None or args_cli.encoder_type is None:
            raise ValueError("--student_ckpt requires both --teacher_ckpt and --encoder_type.")
        resume_path = args_cli.student_ckpt
        print(f"[INFO] Student mode: student_ckpt={resume_path}  teacher_ckpt={args_cli.teacher_ckpt}  encoder={args_cli.encoder_type}")
    else:
        agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
        resume_path = None
        if args_cli.checkpoint and args_cli.checkpoint != "none":
            resume_path = retrieve_file_path(args_cli.checkpoint)
        else:
            log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
            resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
        print(f"[INFO] Checkpoint: {resume_path}")

    # Load agent params from run dir -- student mode reuses teacher's params.yaml
    run_agent_dict = None
    import yaml
    params_search_path = args_cli.teacher_ckpt if is_student_mode else resume_path
    run_params_path = os.path.join(os.path.dirname(params_search_path), "params", "agent.yaml")
    if os.path.isfile(run_params_path):
        try:
            with open(run_params_path) as f:
                run_agent_dict = yaml.full_load(f)
            print(f"[INFO] Loaded agent params from: {run_params_path}")
        except yaml.YAMLError as e:
            print(f"[WARN] Could not load run agent params: {e}")

    # Output dir -- student: put under <student_ckpt_dir>/../eval_dr_switching
    if args_cli.output_dir:
        output_dir = args_cli.output_dir
    elif is_student_mode:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(resume_path)), "eval_dr_switching")
    else:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr_switching")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output: {output_dir}")

    # DORAEMON DR -- use teacher run for loading (student doesn't produce DORAEMON state)
    global _DORAEMON_FULL_DR, _DORAEMON_RAW
    if args_cli.doraemon_dr:
        run_dir = os.path.dirname(args_cli.teacher_ckpt) if is_student_mode else os.path.dirname(resume_path)
        print(f"[INFO] Loading DORAEMON DR from: {run_dir}")
        cfg, raw = load_doraemon_dr(run_dir)
        if cfg is not None:
            _DORAEMON_FULL_DR = cfg
            _DORAEMON_RAW = raw
            print("[INFO] Hard DR = DORAEMON-learned distribution")
        else:
            print("[INFO] No DORAEMON state; using static HardDomainRandomizationCfg")

    # Create env (initial DR scale set per-level below)
    apply_dr_config(env_cfg, DR_SCALE["none"])
    env = gym.make(args_cli.task, cfg=env_cfg)
    clip_actions = run_agent_dict.get("clip_actions") if run_agent_dict else agent_cfg.clip_actions
    env = RslRlVecEnvWrapper(env, clip_actions=clip_actions)
    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device
    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")

    # Policy: student mode uses StudentInLoopPolicy (student encoder + frozen teacher actor)
    if is_student_mode:
        from isaaclab_tasks.direct.constrained_full_albc.student.eval import build_student_policy_fn

        student_policy = build_student_policy_fn(
            teacher_ckpt=args_cli.teacher_ckpt,
            student_ckpt=args_cli.student_ckpt,
            encoder_type=args_cli.encoder_type,
            num_envs=num_envs,
            device=str(device),
        )
        policy = student_policy  # __call__(obs) already matches expected signature

        class _StudentPolicyNN:
            def __init__(self, p): self._p = p
            def reset(self, env_ids):
                if env_ids is None:
                    self._p.reset(None); return
                if isinstance(env_ids, torch.Tensor):
                    self._p.reset(env_ids)
                else:
                    self._p.reset(torch.as_tensor(env_ids, dtype=torch.long))

        policy_nn = _StudentPolicyNN(student_policy)
        print(f"[INFO] Loaded student ({args_cli.encoder_type}) + frozen teacher actor")
    else:
        agent_dict = run_agent_dict if run_agent_dict else agent_cfg.to_dict()
        runner_cls_name = agent_dict.get("class_name", getattr(agent_cfg, "class_name", "OnPolicyRunner"))
        runner_device = agent_dict.get("device", agent_cfg.device)
        runner_cls_map = {"FullDOFConstraintEncoderRunner": ConstraintEncoderRunner}
        runner_cls = runner_cls_map.get(runner_cls_name, OnPolicyRunner)
        runner = runner_cls(env, agent_dict, log_dir=None, device=runner_device)
        runner.load(resume_path, load_optimizer=False)
        policy = runner.get_inference_policy(device=device)
        policy_nn = runner.alg.policy if hasattr(runner.alg, "policy") else runner.alg.actor_critic
        print(f"[INFO] Loaded {runner_cls_name}")

    all_data = {}
    all_metrics = {}

    for level in DR_LEVELS:
        dr_pct = int(DR_SCALE[level] * 100)
        print(f"\n{'=' * 60}\n  DR Level: {level.upper()} | Scale: {dr_pct}% | seed: {args_cli.seed}\n{'=' * 60}")
        apply_dr_config(raw_env.cfg, DR_SCALE[level])

        data = run_switching_eval(
            env=env, policy=policy, policy_nn=policy_nn, raw_env=raw_env,
            num_segments=args_cli.num_segments, segment_duration=args_cli.segment_duration,
            step_dt=step_dt, num_envs=num_envs, device=device, master_seed=args_cli.seed,
        )
        all_data[level] = data
        np.savez_compressed(
            os.path.join(output_dir, f"eval_{level}.npz"),
            **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
        )
        all_metrics[level] = compute_seg_metrics(data)

    # Plots
    print("\n[INFO] Generating plots...")
    _plot_position_drift(all_data, DR_LEVELS, output_dir)
    _plot_attitude_drift(all_data, DR_LEVELS, output_dir)
    _plot_summary_pos(all_metrics, all_data, DR_LEVELS, output_dir)
    _plot_summary_attitude(all_metrics, DR_LEVELS, output_dir)
    _plot_transient_overlay(all_data, DR_LEVELS, output_dir)

    # Save summary JSON
    with open(os.path.join(output_dir, "switching_summary.json"), "w") as f:
        json.dump({"metrics": all_metrics, "config": {
            "num_segments": args_cli.num_segments,
            "segment_duration": args_cli.segment_duration,
            "seed": args_cli.seed,
            "num_envs": num_envs,
        }}, f, indent=2, default=float)

    # Print comparison
    print(f"\n{'=' * 90}\nSWITCHING SUMMARY (target xyz=0 rpy=0, cascade PID, env×seg mean over segs 1..N)\n{'=' * 90}")
    print(f"{'Level':<10} {'DR%':>5} {'pos_peak':>9} {'pos_ss':>8} {'roll_pk':>8} {'pitch_pk':>9} {'yaw_pk':>8} {'yaw_ss':>8}")
    for lvl in DR_LEVELS:
        m = all_metrics[lvl]
        segs_post = list(range(1, m["num_segments"]))
        def agg(key):
            return np.mean(np.concatenate([np.array(m["per_seg"][s][key]) for s in segs_post]))
        print(f"{lvl:<10} {int(DR_SCALE[lvl]*100):4d}% "
              f"{agg('pos_drift_peak'):8.4f}m {agg('pos_drift_ss'):7.4f}m "
              f"{agg('peak_roll_deg'):7.3f}° {agg('peak_pitch_deg'):8.3f}° "
              f"{agg('peak_yaw_deg'):7.3f}° {agg('ss_yaw_deg'):7.3f}°")

    print(f"\nOutput saved to: {output_dir}")
    env.close()


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]  -- hydra_task_config injects env_cfg, agent_cfg
    simulation_app.close()
