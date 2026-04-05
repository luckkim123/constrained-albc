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
WARMUP_SEGMENTS = 1  # Number of neutral warmup segments (excluded from metrics/plots)


def build_step_trajectory(
    segment_duration: float,
    step_dt: float,
) -> tuple[np.ndarray, dict[str, np.ndarray], list[str], int]:
    """Build 6-DOF step-change target trajectory with warmup.

    Structure: [warmup] + attitude block + lin_vel block + yaw block + [tail neutral]
    Warmup and tail neutral segments are included in the trajectory but excluded
    from metrics and plots by the caller.

    Returns:
        time_s: 1D time array (seconds).
        targets: dict of 1D target arrays keyed by channel name.
        seg_names: list of segment labels.
        warmup_steps: number of warmup steps to skip in metrics/plots.
    """
    a = ATT_AMP_DEG
    v = LIN_VEL_AMP
    w = YAW_RATE_AMP

    # (roll_deg, pitch_deg, vx, vy, vz, yaw_rate, name)
    waypoints: list[tuple[float, float, float, float, float, float, str]] = [
        # Warmup (1 seg, excluded from analysis)
        (0, 0, 0, 0, 0, 0, "warmup"),
        # Attitude block (4 segs, 20s)
        (a, 0, 0, 0, 0, 0, f"roll +{a:.0f}"),
        (0, a, 0, 0, 0, 0, f"pitch +{a:.0f}"),
        (-a, -a, 0, 0, 0, 0, f"({-a:.0f}, {-a:.0f})"),
        (a, -a, 0, 0, 0, 0, f"({a:.0f}, {-a:.0f})"),
        # Linear velocity block (6 segs, 30s)
        (0, 0, v, 0, 0, 0, f"vx +{v}"),
        (0, 0, -v, 0, 0, 0, f"vx {-v}"),
        (0, 0, 0, v, 0, 0, f"vy +{v}"),
        (0, 0, 0, -v, 0, 0, f"vy {-v}"),
        (0, 0, 0, 0, v, 0, f"vz +{v}"),
        (0, 0, 0, 0, -v, 0, f"vz {-v}"),
        # Yaw rate block (2 segs, 10s)
        (0, 0, 0, 0, 0, w, f"yaw +{w}"),
        (0, 0, 0, 0, 0, -w, f"yaw {-w}"),
        # Tail neutral (1 seg, excluded from analysis)
        (0, 0, 0, 0, 0, 0, "tail neutral"),
    ]

    steps_per_seg = int(segment_duration / step_dt)
    n_segs = len(waypoints)
    total_steps = steps_per_seg * n_segs
    warmup_steps = WARMUP_SEGMENTS * steps_per_seg

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

    return time_s, targets, seg_names, warmup_steps


# ============================================================================
# Metrics
# ============================================================================


def _step_response_one_segment(
    actual_roll: np.ndarray,
    actual_pitch: np.ndarray,
    alive: np.ndarray,
    prev_roll: float,
    prev_pitch: float,
    cur_roll: float,
    cur_pitch: float,
    seg_time: np.ndarray,
) -> tuple[float, float, float]:
    """Compute step-response metrics for one attitude segment.

    Returns (rise_time, overshoot_pct, peak_time) averaged across roll/pitch
    axes with meaningful step changes (>1 deg).
    """
    axis_results: list[tuple[float, float, float]] = []

    for actual, prev_val, cur_val in [
        (actual_roll, prev_roll, cur_roll),
        (actual_pitch, prev_pitch, cur_pitch),
    ]:
        step_mag = abs(cur_val - prev_val)
        if step_mag < 1.0:
            continue

        mean_val = np.nanmean(np.where(alive, actual, np.nan), axis=1)
        sign = 1.0 if cur_val > prev_val else -1.0

        # Rise time: 10% -> 90% of step
        thresh_10 = prev_val + sign * 0.1 * step_mag
        thresh_90 = prev_val + sign * 0.9 * step_mag
        t_10 = None
        t_90 = None
        for i, v in enumerate(mean_val):
            if np.isnan(v):
                continue
            if t_10 is None and sign * (v - thresh_10) >= 0:
                t_10 = seg_time[i] - seg_time[0]
            if t_90 is None and sign * (v - thresh_90) >= 0:
                t_90 = seg_time[i] - seg_time[0]
        rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else float("nan")

        # Overshoot: actual exceeding target / step magnitude * 100
        overshoot_val = (np.nanmax(mean_val) - cur_val) if sign > 0 else (cur_val - np.nanmin(mean_val))
        overshoot_pct = max(0.0, overshoot_val) / step_mag * 100.0

        # Peak time
        peak_idx = np.nanargmax(mean_val) if sign > 0 else np.nanargmin(mean_val)
        peak_time = seg_time[peak_idx] - seg_time[0]

        axis_results.append((rise_time, overshoot_pct, peak_time))

    if not axis_results:
        return float("nan"), float("nan"), float("nan")

    rt = float(np.nanmean([r[0] for r in axis_results]))
    os_pct = float(np.nanmean([r[1] for r in axis_results]))
    pt = float(np.nanmean([r[2] for r in axis_results]))
    return rt, os_pct, pt


def _classify_segment(name: str) -> str:
    """Classify a segment name into a block type.

    Returns one of: "warmup", "tail", "attitude", "lin_vel", "yaw", "unknown".
    """
    low = name.lower()
    if "warmup" in low:
        return "warmup"
    if "tail" in low:
        return "tail"
    if "roll" in low or "pitch" in low or low.startswith("("):
        return "attitude"
    if "vx" in low or "vy" in low or "vz" in low:
        return "lin_vel"
    if "yaw" in low:
        return "yaw"
    return "unknown"


def _get_block_step_range(
    segment_names: list[str],
    steps_per_segment: int,
    block_type: str,
) -> tuple[int, int]:
    """Return (start_step, end_step) covering all contiguous segments of *block_type*.

    Segments are identified by ``_classify_segment``. The range spans from
    the first segment of matching type to the last (inclusive).
    """
    first = None
    last = None
    for i, name in enumerate(segment_names):
        if _classify_segment(name) == block_type:
            if first is None:
                first = i
            last = i
    if first is None or last is None:
        return 0, 0
    return first * steps_per_segment, (last + 1) * steps_per_segment


def _step_response_scalar_segment(
    actual: np.ndarray,
    alive: np.ndarray,
    prev_target: float,
    cur_target: float,
    seg_time: np.ndarray,
    min_step_mag: float = 0.01,
) -> tuple[float, float]:
    """Compute step-response metrics for a single scalar channel segment.

    Args:
        actual: (T, N) actual values.
        alive: (T, N) bool mask.
        prev_target: target at end of previous segment.
        cur_target: target in this segment.
        seg_time: (T,) time array.
        min_step_mag: minimum step magnitude to consider meaningful.

    Returns:
        (rise_time, overshoot_pct). NaN if step is too small or no data.
    """
    step_mag = abs(cur_target - prev_target)
    if step_mag < min_step_mag:
        return float("nan"), float("nan")

    mean_val = np.nanmean(np.where(alive, actual, np.nan), axis=1)
    sign = 1.0 if cur_target > prev_target else -1.0

    # Rise time: 10% -> 90%
    thresh_10 = prev_target + sign * 0.1 * step_mag
    thresh_90 = prev_target + sign * 0.9 * step_mag
    t_10 = None
    t_90 = None
    for i, v in enumerate(mean_val):
        if np.isnan(v):
            continue
        if t_10 is None and sign * (v - thresh_10) >= 0:
            t_10 = seg_time[i] - seg_time[0]
        if t_90 is None and sign * (v - thresh_90) >= 0:
            t_90 = seg_time[i] - seg_time[0]
    rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else float("nan")

    # Overshoot
    overshoot_val = (np.nanmax(mean_val) - cur_target) if sign > 0 else (cur_target - np.nanmin(mean_val))
    overshoot_pct = max(0.0, overshoot_val) / step_mag * 100.0

    return rise_time, overshoot_pct


def compute_metrics(data: dict) -> dict:
    """Compute per-channel summary metrics from collected data.

    Skips warmup and tail segments. Computes separate metrics for:
    - Attitude (roll/pitch): SS error, settling time, rise time, overshoot
    - Linear velocity (per-axis vx, vy, vz): SS error, rise time, overshoot
    - Yaw rate: SS error, rise time, overshoot
    """
    time_s = data["time"]
    error_roll = data["error_roll"]
    error_pitch = data["error_pitch"]
    terminated = data["terminated"]
    num_envs = error_roll.shape[1]
    seg_steps = data["steps_per_segment"]
    seg_names = data["segment_names"]
    seg_duration = data["segment_duration"]

    error_norm = np.sqrt(error_roll**2 + error_pitch**2)
    alive = ~terminated
    survival_rate = float(alive[-1].sum()) / num_envs * 100.0

    target_roll = data["target_roll_deg"]
    target_pitch = data["target_pitch_deg"]

    max_target_amp = max(
        float(np.max(np.abs(target_roll))),
        float(np.max(np.abs(target_pitch))),
        1.0,
    )
    settling_threshold = max(2.0, max_target_amp * 0.33)

    # ---- Attitude metrics (only attitude segments) ----
    att_ss_errors: list[float] = []
    att_settling_times: list[float] = []
    att_rise_times: list[float] = []
    att_overshoot_pcts: list[float] = []

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "attitude":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_error = error_norm[s:e]
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]

        # Steady-state error (last 50% of segment)
        ss_start = int(seg_steps * 0.5)
        ss_error = seg_error[ss_start:]
        ss_alive = seg_alive[ss_start:]
        if ss_alive.any():
            att_ss_errors.append(float(np.nanmean(np.where(ss_alive, ss_error, np.nan))))
        else:
            att_ss_errors.append(float("nan"))

        # Settling time
        mean_per_step = np.nanmean(np.where(seg_alive, seg_error, np.nan), axis=1)
        settled = mean_per_step < settling_threshold
        if settled.any():
            att_settling_times.append(float(seg_time[np.argmax(settled)] - seg_time[0]))
        else:
            att_settling_times.append(float(seg_duration))

        # Step-response (rise time, overshoot) via existing dual-axis helper
        cur_roll_target = float(target_roll[s])
        cur_pitch_target = float(target_pitch[s])
        prev_roll_target = float(target_roll[s - 1]) if s > 0 else 0.0
        prev_pitch_target = float(target_pitch[s - 1]) if s > 0 else 0.0

        seg_rt, seg_os, _ = _step_response_one_segment(
            data["actual_roll_deg"][s:e],
            data["actual_pitch_deg"][s:e],
            seg_alive,
            prev_roll_target,
            prev_pitch_target,
            cur_roll_target,
            cur_pitch_target,
            seg_time,
        )
        att_rise_times.append(seg_rt)
        att_overshoot_pcts.append(seg_os)

    # Aggregate attitude error over attitude block only
    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    att_alive = alive[att_start:att_end]
    att_err = error_norm[att_start:att_end]
    if att_alive.any():
        total_att_error = float(np.nanmean(np.where(att_alive, att_err, np.nan)))
        per_env_att = np.nanmean(np.where(att_alive, att_err, np.nan), axis=0)
        total_att_error_std = float(np.nanstd(per_env_att))
    else:
        total_att_error = float("nan")
        total_att_error_std = float("nan")

    # ---- Linear velocity metrics (per-axis, only lin_vel segments) ----
    lin_vel_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_vel_keys = ["target_vx", "target_vy", "target_vz"]
    axis_labels = ["vx", "vy", "vz"]

    lin_vel_ss_errors: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_rise_times: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_overshoot_pcts: dict[str, list[float]] = {a: [] for a in axis_labels}

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "lin_vel":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]

        for ax_i, (dkey, tkey, ax_name) in enumerate(zip(lin_vel_keys, target_vel_keys, axis_labels)):
            seg_actual = data[dkey][s:e]
            cur_target = float(data[tkey][s])
            prev_target = float(data[tkey][s - 1]) if s > 0 else 0.0

            # SS error: mean |actual - target| in last 50%
            ss_start = int(seg_steps * 0.5)
            ss_actual = seg_actual[ss_start:]
            ss_alive = seg_alive[ss_start:]
            ss_err = np.abs(ss_actual - cur_target)
            if ss_alive.any():
                lin_vel_ss_errors[ax_name].append(float(np.nanmean(np.where(ss_alive, ss_err, np.nan))))
            else:
                lin_vel_ss_errors[ax_name].append(float("nan"))

            # Step-response only if this axis has a step change in this segment
            rt, os_pct = _step_response_scalar_segment(
                seg_actual, seg_alive, prev_target, cur_target, seg_time, min_step_mag=0.01,
            )
            lin_vel_rise_times[ax_name].append(rt)
            lin_vel_overshoot_pcts[ax_name].append(os_pct)

    # Overall lin_vel SS error (per-axis mean then averaged)
    lin_vel_block_start, lin_vel_block_end = _get_block_step_range(seg_names, seg_steps, "lin_vel")
    lin_vel_block_alive = alive[lin_vel_block_start:lin_vel_block_end]
    lin_vel_block_norm = data["lin_vel_norm"][lin_vel_block_start:lin_vel_block_end]
    if lin_vel_block_alive.any():
        total_lin_vel_error = float(np.nanmean(np.where(lin_vel_block_alive, lin_vel_block_norm, np.nan)))
    else:
        total_lin_vel_error = float("nan")

    lin_vel_survival = float(alive[lin_vel_block_end - 1].sum()) / num_envs * 100.0 if lin_vel_block_end > 0 else 0.0

    # ---- Yaw rate metrics (only yaw segments) ----
    yaw_ss_errors: list[float] = []
    yaw_rise_times: list[float] = []
    yaw_overshoot_pcts: list[float] = []

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "yaw":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]
        seg_actual = data["yaw_rate"][s:e]
        cur_target = float(data["target_yaw_rate"][s])
        prev_target = float(data["target_yaw_rate"][s - 1]) if s > 0 else 0.0

        # SS error
        ss_start = int(seg_steps * 0.5)
        ss_actual = seg_actual[ss_start:]
        ss_alive = seg_alive[ss_start:]
        ss_err = np.abs(ss_actual - cur_target)
        if ss_alive.any():
            yaw_ss_errors.append(float(np.nanmean(np.where(ss_alive, ss_err, np.nan))))
        else:
            yaw_ss_errors.append(float("nan"))

        # Step-response
        rt, os_pct = _step_response_scalar_segment(
            seg_actual, seg_alive, prev_target, cur_target, seg_time, min_step_mag=0.01,
        )
        yaw_rise_times.append(rt)
        yaw_overshoot_pcts.append(os_pct)

    yaw_block_start, yaw_block_end = _get_block_step_range(seg_names, seg_steps, "yaw")
    yaw_block_alive = alive[yaw_block_start:yaw_block_end]
    yaw_block_abs = np.abs(data["yaw_rate"][yaw_block_start:yaw_block_end])
    if yaw_block_alive.any():
        total_yaw_rate_error = float(np.nanmean(np.where(yaw_block_alive, yaw_block_abs, np.nan)))
    else:
        total_yaw_rate_error = float("nan")

    yaw_survival = float(alive[yaw_block_end - 1].sum()) / num_envs * 100.0 if yaw_block_end > 0 else 0.0

    return {
        # Attitude
        "total_att_error": total_att_error,
        "total_att_error_std": total_att_error_std,
        "att_ss_errors": att_ss_errors,
        "att_settling_times": att_settling_times,
        "att_rise_times": att_rise_times,
        "att_overshoot_pcts": att_overshoot_pcts,
        # Linear velocity (per-axis)
        "total_lin_vel_error": total_lin_vel_error,
        "lin_vel_ss_errors": lin_vel_ss_errors,  # dict[axis_name, list[float]]
        "lin_vel_rise_times": lin_vel_rise_times,
        "lin_vel_overshoot_pcts": lin_vel_overshoot_pcts,
        "lin_vel_survival": lin_vel_survival,
        # Yaw
        "total_yaw_rate_error": total_yaw_rate_error,
        "yaw_ss_errors": yaw_ss_errors,
        "yaw_rise_times": yaw_rise_times,
        "yaw_overshoot_pcts": yaw_overshoot_pcts,
        "yaw_survival": yaw_survival,
        # Global
        "survival_rate": survival_rate,
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
    _plot_error(all_data, levels, output_dir)
    _plot_summary_attitude(all_metrics, levels, output_dir)
    _plot_summary_lin_vel(all_metrics, levels, output_dir)
    _plot_summary_yaw(all_metrics, levels, output_dir)
    _plot_failure_time(all_data, levels, output_dir)


# ---------------------------------------------------------------------------
# Attitude tracking (cropped to attitude block, per-DR-row)
# ---------------------------------------------------------------------------

def _plot_attitude_tracking(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Roll/pitch attitude tracking per DR level (Nx2 grid), cropped to attitude block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    fig, axes = plt.subplots(len(levels), 2, figsize=(16, 3 * len(levels)), sharex=True)
    fig.suptitle("Attitude Tracking per DR Level (attitude block)", fontsize=14, y=0.98)

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][att_start:att_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(att_end - att_start) * step_dt

        for col, (actual_key, target_key, axis_label) in enumerate(
            [
                ("actual_roll_deg", "target_roll_deg", "Roll (deg)"),
                ("actual_pitch_deg", "target_pitch_deg", "Pitch (deg)"),
            ]
        ):
            ax = axes[row, col] if len(levels) > 1 else axes[col]
            target = d[target_key][att_start:att_end]
            ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
            vals = np.where(alive, d[actual_key][att_start:att_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
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


# ---------------------------------------------------------------------------
# Linear velocity tracking (per-DR-row, 3 columns = vx/vy/vz)
# ---------------------------------------------------------------------------

def _plot_lin_vel(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Linear velocity tracking per DR level (Nx3 grid), cropped to lin_vel block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    lv_start, lv_end = _get_block_step_range(seg_names, seg_steps, "lin_vel")
    if lv_start >= lv_end:
        return

    data_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_keys = ["target_vx", "target_vy", "target_vz"]
    axis_labels = ["Vx (m/s)", "Vy (m/s)", "Vz (m/s)"]

    fig, axes = plt.subplots(len(levels), 3, figsize=(18, 3 * len(levels)), sharex=True)
    fig.suptitle("Linear Velocity Tracking per DR Level (lin_vel block)", fontsize=14, y=0.98)

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][lv_start:lv_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(lv_end - lv_start) * step_dt

        for col, (dkey, tkey, ylabel) in enumerate(zip(data_keys, target_keys, axis_labels)):
            ax = axes[row, col] if len(levels) > 1 else axes[col]
            target = d[tkey][lv_start:lv_end]
            ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
            vals = np.where(alive, d[dkey][lv_start:lv_end], np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
            ax.set_ylabel(ylabel, fontsize=9)
            ax.grid(True, alpha=0.3)
            if col == 0:
                ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
            if row == 0 and col == 1:
                ax.legend(loc="upper right", fontsize=8)
            if row == len(levels) - 1:
                ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "lin_vel.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Yaw rate tracking (per-DR-row, 1 column)
# ---------------------------------------------------------------------------

def _plot_yaw_rate(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Yaw rate tracking per DR level (Nx1 grid), cropped to yaw block."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    yaw_start, yaw_end = _get_block_step_range(seg_names, seg_steps, "yaw")
    if yaw_start >= yaw_end:
        return

    fig, axes = plt.subplots(len(levels), 1, figsize=(14, 3 * len(levels)), sharex=True)
    fig.suptitle("Yaw Rate Tracking per DR Level (yaw block)", fontsize=14, y=0.98)
    if len(levels) == 1:
        axes = [axes]

    for row, lvl in enumerate(levels):
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][yaw_start:yaw_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        block_time = np.arange(yaw_end - yaw_start) * step_dt

        ax = axes[row]
        target = d["target_yaw_rate"][yaw_start:yaw_end]
        ax.plot(block_time, target, "k--", linewidth=1.2, alpha=0.6, label="target")
        vals = np.where(alive, d["yaw_rate"][yaw_start:yaw_end], np.nan)
        mean = np.nanmean(vals, axis=1)
        std = np.nanstd(vals, axis=1)
        ax.plot(block_time, mean, color=color, linewidth=1.0, label="actual (mean)")
        ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.15)
        ax.set_ylabel("Yaw Rate (rad/s)", fontsize=9)
        ax.set_title(f"{lvl} (DR {dr_pct}%)", fontsize=10, fontweight="bold", color=color)
        ax.grid(True, alpha=0.3)
        if row == 0:
            ax.legend(loc="upper right", fontsize=8)
        if row == len(levels) - 1:
            ax.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "yaw_rate.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Error plot (|roll error|, |pitch error|, action magnitude -- all DR overlaid)
# ---------------------------------------------------------------------------

def _plot_error(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Tracking error and action magnitude, cropped to attitude block, all DR overlaid."""
    ref = all_data[levels[0]]
    seg_names = ref["segment_names"]
    seg_steps = ref["steps_per_segment"]
    step_dt = ref["time"][1] - ref["time"][0] if len(ref["time"]) > 1 else 0.02

    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    if att_start >= att_end:
        return

    has_actions = "action_magnitude" in ref
    n_rows = 3 if has_actions else 2
    fig, axes = plt.subplots(n_rows, 1, figsize=(14, 4 * n_rows), sharex=True)
    fig.suptitle("Tracking Error vs DR Level (attitude block)", fontsize=14)
    ax_re, ax_pe = axes[0], axes[1]

    block_time = np.arange(att_end - att_start) * step_dt

    for lvl in levels:
        d = all_data[lvl]
        color = DR_COLORS[lvl]
        alive = ~d["terminated"][att_start:att_end]
        dr_pct = int(DR_SCALE[lvl] * 100)
        label = f"{lvl} (DR {dr_pct}%)"

        for ax, key in [(ax_re, "error_roll"), (ax_pe, "error_pitch")]:
            vals = np.where(alive, np.abs(d[key][att_start:att_end]), np.nan)
            mean = np.nanmean(vals, axis=1)
            std = np.nanstd(vals, axis=1)
            ax.plot(block_time, mean, color=color, linewidth=1.2, label=label)
            ax.fill_between(block_time, mean - std, mean + std, color=color, alpha=0.12)

        if has_actions:
            ax_act = axes[2]
            act_vals = np.where(alive, d["action_magnitude"][att_start:att_end], np.nan)
            act_mean = np.nanmean(act_vals, axis=1)
            act_std = np.nanstd(act_vals, axis=1)
            ax_act.plot(block_time, act_mean, color=color, linewidth=1.2, label=label)
            ax_act.fill_between(block_time, act_mean - act_std, act_mean + act_std, color=color, alpha=0.12)

    ax_re.set_ylabel("|Roll Error| (deg)")
    ax_pe.set_ylabel("|Pitch Error| (deg)")
    ax_re.legend(loc="upper right", fontsize=9)
    for _ax in [ax_re, ax_pe]:
        _ax.yaxis.set_major_locator(MultipleLocator(15))
        _ax.grid(True, alpha=0.3)
    if has_actions:
        axes[2].set_ylabel("Action Magnitude")
        axes[2].set_xlabel("Time (s)")
        axes[2].grid(True, alpha=0.3)
    else:
        ax_pe.set_xlabel("Time (s)")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "error.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: attitude (2x2 bar chart)
# ---------------------------------------------------------------------------

def _plot_summary_attitude(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for attitude: SS error, settling time, rise time, overshoot."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Attitude Summary", fontsize=14)
    x = np.arange(len(levels))
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): SS error
    ss_means = [float(np.nanmean(all_metrics[lvl]["att_ss_errors"])) for lvl in levels]
    ss_stds = [float(np.nanstd(all_metrics[lvl]["att_ss_errors"])) for lvl in levels]
    _bar_subplot(axes[0, 0], x, ss_means, bar_colors, xlabels, "Error (deg)", "Attitude SS Error", yerr=ss_stds)

    # (0,1): Settling time
    st_means = [float(np.nanmean(all_metrics[lvl]["att_settling_times"])) for lvl in levels]
    st_stds = [float(np.nanstd(all_metrics[lvl]["att_settling_times"])) for lvl in levels]
    _bar_subplot(axes[0, 1], x, st_means, bar_colors, xlabels, "Time (s)", "Settling Time", yerr=st_stds)

    # (1,0): Rise time
    rt_means = [float(np.nanmean(all_metrics[lvl]["att_rise_times"])) for lvl in levels]
    rt_stds = [float(np.nanstd(all_metrics[lvl]["att_rise_times"])) for lvl in levels]
    _bar_subplot(axes[1, 0], x, rt_means, bar_colors, xlabels, "Time (s)", "Rise Time (10%->90%)", yerr=rt_stds)

    # (1,1): Overshoot
    os_means = [float(np.nanmean(all_metrics[lvl]["att_overshoot_pcts"])) for lvl in levels]
    os_stds = [float(np.nanstd(all_metrics[lvl]["att_overshoot_pcts"])) for lvl in levels]
    _bar_subplot(axes[1, 1], x, os_means, bar_colors, xlabels, "Overshoot (%)", "Step-Response Overshoot", yerr=os_stds)

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_att.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: linear velocity (2x2 bar chart, per-axis SS + step-response)
# ---------------------------------------------------------------------------

def _plot_summary_lin_vel(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for lin vel: per-axis SS error, rise time, overshoot, survival."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Linear Velocity Summary", fontsize=14)
    axis_names = ["vx", "vy", "vz"]
    n_ax = len(axis_names)
    n_lvl = len(levels)
    bar_width = 0.8 / n_ax
    x_base = np.arange(n_lvl)
    ax_colors = ["#1f77b4", "#ff7f0e", "#2ca02c"]  # per-axis colors
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): Per-axis SS error (grouped bar)
    ax = axes[0, 0]
    for ai, aname in enumerate(axis_names):
        vals = [float(np.nanmean(all_metrics[lvl]["lin_vel_ss_errors"][aname])) for lvl in levels]
        offset = (ai - (n_ax - 1) / 2) * bar_width
        ax.bar(x_base + offset, vals, width=bar_width, color=ax_colors[ai], label=aname)
    ax.set_xticks(x_base)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel("SS Error (m/s)")
    ax.set_title("Per-Axis SS Error")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # (0,1): Per-axis rise time (grouped bar)
    ax = axes[0, 1]
    for ai, aname in enumerate(axis_names):
        vals = [float(np.nanmean(all_metrics[lvl]["lin_vel_rise_times"][aname])) for lvl in levels]
        offset = (ai - (n_ax - 1) / 2) * bar_width
        ax.bar(x_base + offset, vals, width=bar_width, color=ax_colors[ai], label=aname)
    ax.set_xticks(x_base)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel("Time (s)")
    ax.set_title("Rise Time (10%->90%)")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # (1,0): Per-axis overshoot (grouped bar)
    ax = axes[1, 0]
    for ai, aname in enumerate(axis_names):
        vals = [float(np.nanmean(all_metrics[lvl]["lin_vel_overshoot_pcts"][aname])) for lvl in levels]
        offset = (ai - (n_ax - 1) / 2) * bar_width
        ax.bar(x_base + offset, vals, width=bar_width, color=ax_colors[ai], label=aname)
    ax.set_xticks(x_base)
    ax.set_xticklabels(xlabels, fontsize=9)
    ax.set_ylabel("Overshoot (%)")
    ax.set_title("Step-Response Overshoot")
    ax.legend(fontsize=8)
    ax.grid(True, alpha=0.3, axis="y")

    # (1,1): Survival at end of lin_vel block
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    survivals = [all_metrics[lvl]["lin_vel_survival"] for lvl in levels]
    _bar_subplot(
        axes[1, 1], x_base, survivals, bar_colors, xlabels,
        "Survival (%)", "Survival (end of lin_vel)", ylim=(0, 105),
    )

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_lin_vel.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Summary: yaw (2x2 bar chart)
# ---------------------------------------------------------------------------

def _plot_summary_yaw(all_metrics: dict, levels: list[str], output_dir: str) -> None:
    """Summary bar chart for yaw: SS error, rise time, overshoot, survival."""
    fig, axes = plt.subplots(2, 2, figsize=(12, 8))
    fig.suptitle("Yaw Rate Summary", fontsize=14)
    x = np.arange(len(levels))
    bar_colors = [DR_COLORS[lvl] for lvl in levels]
    xlabels = [f"{lvl}\n(DR {int(DR_SCALE[lvl] * 100)}%)" for lvl in levels]

    # (0,0): SS error
    ss_means = [float(np.nanmean(all_metrics[lvl]["yaw_ss_errors"])) for lvl in levels]
    ss_stds = [float(np.nanstd(all_metrics[lvl]["yaw_ss_errors"])) for lvl in levels]
    _bar_subplot(axes[0, 0], x, ss_means, bar_colors, xlabels, "Error (rad/s)", "Yaw SS Error", yerr=ss_stds)

    # (0,1): Rise time
    rt_means = [float(np.nanmean(all_metrics[lvl]["yaw_rise_times"])) for lvl in levels]
    rt_stds = [float(np.nanstd(all_metrics[lvl]["yaw_rise_times"])) for lvl in levels]
    _bar_subplot(axes[0, 1], x, rt_means, bar_colors, xlabels, "Time (s)", "Rise Time (10%->90%)", yerr=rt_stds)

    # (1,0): Overshoot
    os_means = [float(np.nanmean(all_metrics[lvl]["yaw_overshoot_pcts"])) for lvl in levels]
    os_stds = [float(np.nanstd(all_metrics[lvl]["yaw_overshoot_pcts"])) for lvl in levels]
    _bar_subplot(axes[1, 0], x, os_means, bar_colors, xlabels, "Overshoot (%)", "Step-Response Overshoot", yerr=os_stds)

    # (1,1): Survival at end of yaw block
    survivals = [all_metrics[lvl]["yaw_survival"] for lvl in levels]
    _bar_subplot(axes[1, 1], x, survivals, bar_colors, xlabels, "Survival (%)", "Survival (end of yaw)", ylim=(0, 105))

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_yaw.png"), dpi=150)
    plt.close(fig)


# ---------------------------------------------------------------------------
# Failure time distribution (unchanged layout)
# ---------------------------------------------------------------------------

def _plot_failure_time(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Failure time distribution histogram per DR level."""
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
        "warmup_steps": WARMUP_SEGMENTS * steps_per_seg,
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
    time_s, targets, segment_names, warmup_steps = build_step_trajectory(
        segment_duration=args_cli.segment_duration,
        step_dt=step_dt,
    )
    print(
        f"[INFO] Trajectory: {len(segment_names)} segs x {args_cli.segment_duration}s"
        f" = {len(time_s)} steps ({time_s[-1]:.0f}s)"
        f", warmup={WARMUP_SEGMENTS} segs ({warmup_steps} steps)"
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
        print("    [Attitude]")
        print(f"      Error:     {metrics['total_att_error']:.1f} +/- {metrics['total_att_error_std']:.1f} deg")
        print(f"      SS error:  {np.nanmean(metrics['att_ss_errors']):.1f} deg")
        print(f"      Settling:  {np.nanmean(metrics['att_settling_times']):.2f} s")
        print(f"      Rise time: {np.nanmean(metrics['att_rise_times']):.3f} s")
        print(f"      Overshoot: {np.nanmean(metrics['att_overshoot_pcts']):.1f}%")
        print("    [Lin Vel]")
        print(f"      Error:     {metrics['total_lin_vel_error']:.3f} m/s")
        for ax_name in ["vx", "vy", "vz"]:
            ss = np.nanmean(metrics['lin_vel_ss_errors'][ax_name])
            rt = np.nanmean(metrics['lin_vel_rise_times'][ax_name])
            os_p = np.nanmean(metrics['lin_vel_overshoot_pcts'][ax_name])
            print(f"      {ax_name}: SS={ss:.3f} Rise={rt:.3f}s OS={os_p:.1f}%")
        print(f"      Survival:  {metrics['lin_vel_survival']:.0f}%")
        print("    [Yaw]")
        print(f"      Error:     {metrics['total_yaw_rate_error']:.4f} rad/s")
        print(f"      SS error:  {np.nanmean(metrics['yaw_ss_errors']):.4f} rad/s")
        print(f"      Rise time: {np.nanmean(metrics['yaw_rise_times']):.3f} s")
        print(f"      Overshoot: {np.nanmean(metrics['yaw_overshoot_pcts']):.1f}%")
        print(f"      Survival:  {metrics['yaw_survival']:.0f}%")
        print(f"    [Global] Survival: {metrics['survival_rate']:.0f}%")

    # ---- Generate plots ----
    print("\n[INFO] Generating plots...")
    generate_plots(all_data, all_metrics, output_dir)

    # ---- Print final comparison ----
    print(f"\n{'=' * 100}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 100}")
    print(
        f"{'Level':<10} {'DR%':>5} {'AttErr':>10} {'AttSS':>8} {'AttRise':>8} "
        f"{'LinVel':>8} {'YawErr':>8} {'YawSS':>8} {'Surv':>6}"
    )
    print(f"{'-' * 10} {'-' * 5} {'-' * 10} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 8} {'-' * 6}")
    for lvl in DR_LEVELS:
        m = all_metrics[lvl]
        print(
            f"{lvl:<10} "
            f"{int(DR_SCALE[lvl] * 100):4d}% "
            f"{m['total_att_error']:5.1f}+/-{m['total_att_error_std']:.1f} "
            f"{np.nanmean(m['att_ss_errors']):7.1f}d "
            f"{np.nanmean(m['att_rise_times']):7.3f}s "
            f"{m['total_lin_vel_error']:7.3f} "
            f"{m['total_yaw_rate_error']:7.4f} "
            f"{np.nanmean(m['yaw_ss_errors']):7.4f} "
            f"{m['survival_rate']:5.0f}%"
        )
    print(f"{'=' * 100}")

    print(f"\nOutput saved to: {output_dir}")
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
