# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""DR-robustness evaluation for ALBC / Isaac-ConstrainedALBC-TRPO-v0 (Isaac Sim required).

Subcommands:
    static     evaluate policy across fixed DR levels (none/soft/medium/hard) + OOD  [main eval]
    periodic   mid-episode periodic DR change, hover robustness
    segmented  per-segment DR switch + student/teacher/cascade-PID compare

OOD (out-of-distribution) generalization is evaluated within `static` via
--extreme-ood / --ood-preset / --ood-scale / --ood-range-scale (no separate mode).

Usage:
    ./isaaclab.sh -p scripts/analysis/eval.py static --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless
    ./isaaclab.sh -p scripts/analysis/eval.py static --extreme-ood --ood-preset v2 --headless
    ./isaaclab.sh -p scripts/analysis/eval.py periodic --num_steps 4 --headless
    ./isaaclab.sh -p scripts/analysis/eval.py segmented --segment_duration 5 --headless
"""

import argparse
import os
import sys

# cli_args is vendored locally (was scripts/reinforcement_learning/rsl_rl/ in isaaclab, not migrated)
# common.py and cli_args.py both live alongside this file
sys.path.insert(0, os.path.dirname(__file__))

# Pure (Isaac-Sim-free) trajectory + metric helpers, extracted to _eval_dr/.
# Safe to import before the AppLauncher boot below (numpy only).
from _eval_dr.metrics import (  # type: ignore[import-not-found]  # noqa: E402
    _get_block_step_range,
    _periodic_compute_metrics,
    _pick_sample_env,
    compute_metrics,
    compute_seg_metrics,
)
from _eval_dr.trajectory import (  # type: ignore[import-not-found]  # noqa: E402
    ATT_AMP_DEG,
    LIN_VEL_AMP,
    WARMUP_SEGMENTS,
    YAW_RATE_AMP,
    build_step_trajectory,
)

from isaaclab.app import AppLauncher

import cli_args  # isort: skip


def _add_common(sp: argparse.ArgumentParser) -> None:
    """Add args shared by all subcommands (incl. app-launcher + rsl_rl args)."""
    # Register app-launcher flags on the subparser so they parse when placed after
    # the subcommand token (subparsers own args that follow the subcommand). This must
    # run before the required args below: add_app_launcher_args() does an internal
    # parse_known_args() for collision checks, which would abort on the subcommand token
    # or not-yet-added args, so we neutralize sys.argv around the call.
    _saved_argv = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        AppLauncher.add_app_launcher_args(sp)
    finally:
        sys.argv = _saved_argv
    sp.add_argument("--task", type=str, default="Isaac-ConstrainedALBC-TRPO-v0", help="Task name.")
    sp.add_argument("--num_envs", type=int, default=64, help="Number of parallel environments.")
    sp.add_argument("--output_dir", type=str, default=None, help="Output directory.")
    sp.add_argument("--seed", type=int, default=42, help="Random seed.")
    sp.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="RSL-RL config entry point.")
    cli_args.add_rsl_rl_args(sp)


parser = argparse.ArgumentParser(description="DR-robustness evaluation for ALBC.")
subparsers = parser.add_subparsers(dest="mode", required=True)

# ----------------------------------------------------------------------------
# static: evaluate policy across fixed DR levels (none/soft/medium/hard) [main eval]
# ----------------------------------------------------------------------------
sp_static = subparsers.add_parser("static", description="Evaluate DR robustness across fixed DR levels.")
_add_common(sp_static)
sp_static.add_argument("--segment_duration", type=float, default=5.0, help="Duration per segment in seconds.")
sp_static.add_argument(
    "--doraemon-dr",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Use DORAEMON-learned DR (mean +/- 2*std) as hard level. Default: auto-load from run dir. "
         "Use --no-doraemon-dr to fall back to HardDomainRandomizationCfg.",
)
sp_static.add_argument(
    "--doraemon-dr-from",
    type=str,
    default=None,
    help="Load DORAEMON DR from this run dir instead of the evaluated run's own dir. "
         "Used to evaluate all ablation variants on the r13_A baseline's learned DR "
         "distribution (common test distribution). Overrides --doraemon-dr auto-load.",
)
sp_static.add_argument(
    "--ood-scale",
    type=float,
    default=None,
    help="Run OOD eval at this scale factor (e.g. 2.0 = 2x hard DR). Skips the "
         "usual none/soft/medium/hard loop and runs ONLY one level at this scale. "
         "Extrapolates DR bounds beyond training distribution.",
)
sp_static.add_argument(
    "--deterministic-dr",
    action="store_true",
    default=False,
    help="Force deterministic physics: collapse every DR range to its midpoint "
         "AND disable DORAEMON Beta sampling. Guarantees identical physics "
         "across independent runs -- required for 1-env policy comparison "
         "where seed alone doesn't ensure identical DR draws between different "
         "policy networks (different RNG consumption order).",
)
sp_static.add_argument(
    "--extreme-ood",
    action="store_true",
    default=False,
    help="Apply an explicit extreme-OOD physics preset (every DR param pushed "
         "~30%% beyond r13_A's learned training bounds, fixed value). Disables "
         "DORAEMON and overrides DR config. See _EXTREME_OOD_PHYSICS below.",
)
sp_static.add_argument(
    "--ood-preset",
    choices=["v1", "v2"],
    default="v2",
    help="Extreme-OOD preset: v1 = training hard DR upper bound, v2 = +20-30%% beyond (default).",
)
sp_static.add_argument(
    "--ood-range-scale",
    type=float,
    default=None,
    help="v3 mode: widen each training DR tuple range by this factor about its midpoint "
         "(e.g. 1.2 = +20%% wider). Random sample per env, combining Hard-DR randomness with "
         "OOD extrapolation. Disables DORAEMON.",
)
# Student-policy mode (optional) -- mirrors segmented so a distilled student is evaluated
# through the same static path as the teacher (4 DR levels + .mat + full PNG set), giving a
# 1:1 teacher/student comparison. When --student_ckpt is set, the student encoder + frozen
# teacher actor replace the teacher runner; the rest of the static pipeline is unchanged.
sp_static.add_argument("--student_ckpt", type=str, default=None,
                       help="If set, evaluate the student encoder + frozen teacher actor instead of the teacher runner.")
sp_static.add_argument("--teacher_ckpt", type=str, default=None,
                       help="Teacher model_*.pt path (required when --student_ckpt is given).")
sp_static.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], default=None,
                       help="Student encoder type (required when --student_ckpt is given).")
sp_static.add_argument(
    "--z_ablation",
    type=str,
    default=None,
    choices=["zero", "mean"],
    help="Inference-time encoder z-ablation (gap-#1 diagnostic): zero=z->0, "
    "mean=z->encode(nominal). Unset=normal eval (default).",
)

# ----------------------------------------------------------------------------
# periodic: mid-episode periodic DR change, hover robustness
# ----------------------------------------------------------------------------
sp_periodic = subparsers.add_parser("periodic", description="Evaluate DR robustness under mid-episode physics changes.")
_add_common(sp_periodic)
sp_periodic.add_argument("--step_duration", type=float, default=5.0, help="Duration per DR step in seconds.")
sp_periodic.add_argument("--num_steps", type=int, default=10, help="Number of DR change steps.")
sp_periodic.add_argument(
    "--doraemon-dr",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Use DORAEMON-learned DR as hard level. Default: auto-load from run dir.",
)

# ----------------------------------------------------------------------------
# segmented: per-segment DR switch + student/teacher/cascade-PID compare
# ----------------------------------------------------------------------------
sp_segmented = subparsers.add_parser("segmented", description="Evaluate DR-switching adaptation of ALBC-TRPO policies.")  # noqa: E501
_add_common(sp_segmented)
sp_segmented.add_argument("--segment_duration", type=float, default=5.0)
sp_segmented.add_argument("--num_segments", type=int, default=10)
sp_segmented.add_argument("--kp_pos", type=float, default=0.5, help="Outer-loop position P-gain (s^-1). vel_cmd = clip(Kp_pos * pos_err, ±vel_sat).")
sp_segmented.add_argument("--kp_yaw", type=float, default=0.5, help="Outer-loop yaw P-gain (s^-1). yaw_rate_cmd = clip(Kp_yaw * yaw_err, ±yaw_rate_sat).")
sp_segmented.add_argument("--vel_sat", type=float, default=0.25, help="Velocity command saturation (m/s). Matches training range.")
sp_segmented.add_argument("--yaw_rate_sat", type=float, default=0.25, help="Yaw rate command saturation (rad/s).")
sp_segmented.add_argument("--doraemon-dr", action=argparse.BooleanOptionalAction, default=True)
# Student-policy mode (optional)
sp_segmented.add_argument("--student_ckpt", type=str, default=None,
                          help="If set, run with student encoder + frozen teacher actor instead of teacher runner.")
sp_segmented.add_argument("--teacher_ckpt", type=str, default=None,
                          help="Teacher model_*.pt path (required when --student_ckpt is given).")
sp_segmented.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], default=None,
                          help="Student encoder type (required when --student_ckpt is given).")

# Parse + launch ONLY when executed directly. When this module is imported by
# another script that owns argv, that script is responsible for calling AppLauncher
# exactly once. Re-launching AppLauncher in imported mode corrupts Kit state. The
# required subparser would also SystemExit on the importer's argv (no subcommand token),
# so the whole parse/launch block is guarded.
if __name__ == "__main__":
    args_cli, hydra_args = parser.parse_known_args()

    # clear sys.argv for Hydra
    sys.argv = [sys.argv[0]] + hydra_args

    # launch omniverse app
    app_launcher = AppLauncher(args_cli)
    simulation_app = app_launcher.app
else:
    # Imported mode: provide a minimal args_cli so the @hydra_task_config decorator
    # on main() can resolve args_cli.task/.agent at import time. The importer never
    # calls eval_dr.main(); it only uses the module-top helper functions.
    args_cli = argparse.Namespace(task="Isaac-ConstrainedALBC-TRPO-v0", agent="rsl_rl_cfg_entry_point", mode=None)
    hydra_args = []
    app_launcher = None  # type: ignore[assignment]
    simulation_app = None  # type: ignore[assignment]

"""Rest everything follows."""

import json
from datetime import datetime

import gymnasium as gym
import matplotlib

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import rsl_rl.runners.on_policy_runner as _runner_module
import torch
from common import DR_COLORS
from common import DR_LEVELS as _DEFAULT_DR_LEVELS
from common import DR_SCALE as _DEFAULT_DR_SCALE
from eval_plots import (  # type: ignore[import-not-found]  # noqa: E402
    _bar_subplot,
    generate_plots,
)
from matplotlib.ticker import MultipleLocator
from paths import eval_dir_for_checkpoint  # type: ignore[import-not-found]  # noqa: E402  run_id-tree eval output (#2)
from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import DirectRLEnvCfg
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.math import euler_xyz_from_quat, quat_rotate_inverse

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from constrained_albc.envs.main.algorithms import ConstraintTRPO
from constrained_albc.envs.main.config import (
    DomainRandomizationCfg,
    HardDomainRandomizationCfg,
)
from constrained_albc.envs.main.doraemon import _NOMINAL_OVERRIDES, _PARAM_DEFS, build_param_specs
from constrained_albc.envs.main.encoder import ActorCriticEncoder
from constrained_albc.envs.main.mdp import (
    DRSampler,
    randomize_body_mass,
    randomize_hydrodynamics,
    randomize_ocean_current,
    randomize_payload,
)
from constrained_albc.envs.main.runners import ConstraintEncoderRunner
from constrained_albc.envs.main.utils import update_latest_symlink
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# Runtime-mutable copies (overridden by --ood-scale in static mode)
DR_LEVELS: list[str] = list(_DEFAULT_DR_LEVELS)
DR_SCALE: dict[str, float] = dict(_DEFAULT_DR_SCALE)

# Module-level: DORAEMON-learned distribution as the hard-DR anchor.
# `_DORAEMON_FULL_DR` is the DR config (mean +/- 2*std clamped to PARAM_SPEC bounds).
# `_DORAEMON_RAW` is the underlying mean/std per parameter, used by visualization.
_DORAEMON_FULL_DR: DomainRandomizationCfg | None = None
_DORAEMON_RAW: dict[str, tuple[float, float]] = {}

# Register custom classes in RSL-RL runner module namespace
_runner_module.ALBCActorCriticEncoder = ActorCriticEncoder
_runner_module.ALBCConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.ALBCConstraintTRPO = ConstraintTRPO

MAX_ANGLE_DEG = 15.0  # kept for backward compat (episode_length_s calc)

# Total number of waypoints in build_step_trajectory():
#   1 init warmup
#   + 1 att zero (post-warmup, logged)
#   + 10 att (last is "att return (0, 0) 1")
#   + 1 "att return (0, 0) 2" (doubled)
#   + 1 pre-lin_vel warmup
#   + 1 vxyz zero (post-warmup, logged)
#   + 10 lin_vel (last two are "vxyz return (0, 0, 0) 1/2")
#   + 1 pre-yaw warmup
#   + 1 yaw zero (post-warmup, logged)
#   + 4 yaw (last two are "yaw return 0 (1)/(2)")
#   = 31 segments.
# Used by run_static() to set env_cfg.episode_length_s. Keep in sync with waypoints
# list inside build_step_trajectory().
TRAJECTORY_N_SEGMENTS = 31

# Mapping from DORAEMON param names to DomainRandomizationCfg field names.
# Most share the same name except payload_mass and water_density.
_DORAEMON_TO_DR_FIELD: dict[str, str] = {
    "payload_mass": "payload_mass_range",
    "water_density": "water_density_range",
}


def load_doraemon_dr(run_dir: str) -> tuple[DomainRandomizationCfg | None, dict[str, tuple[float, float]]]:
    """Build DomainRandomizationCfg from DORAEMON's learned distribution.

    Reads final mean/std from TensorBoard logs. Hard DR range = mean +/- 2*std,
    clamped to PARAM_SPEC bounds. Non-DORAEMON parameters (joint actuator,
    thruster) start from HardDomainRandomizationCfg so the eval matches the
    physics ranges actually seen during training.

    Returns:
        (cfg, raw): DR config with DORAEMON-learned ranges applied, and a dict
        mapping DR field name -> (mean, std) for visualization. Returns
        (None, {}) if no DORAEMON tags are found in the TB log.
    """
    from tensorboard.backend.event_processing import event_accumulator

    if not os.path.isdir(run_dir):
        return None, {}

    try:
        ea = event_accumulator.EventAccumulator(run_dir)
        ea.Reload()
        all_tags = set(ea.Tags().get("scalars", []))
    except Exception as e:
        print(f"[WARN] Could not load TB events from {run_dir}: {e}")
        return None, {}

    if not any(t.startswith("DORAEMON/mean/") for t in all_tags):
        return None, {}

    # Hard DR is the runtime physics range used during training; use it as the
    # base config so non-DORAEMON fields (joint, thruster) match training.
    cfg = HardDomainRandomizationCfg()
    cfg.enable = True

    # CRITICAL: imported PARAM_SPECS uses base DomainRandomizationCfg bounds, but
    # the runtime DORAEMON scheduler builds its specs from HardDomainRandomizationCfg
    # via build_param_specs(). Using the hardcoded PARAM_SPECS would clamp the
    # learned mean +/- 2*std into the much narrower base DR range, falsely shrinking
    # the hard-DR anchor. Use HardDR-derived specs to match the actual training bounds.
    runtime_specs = build_param_specs(cfg, _PARAM_DEFS, _NOMINAL_OVERRIDES)

    raw: dict[str, tuple[float, float]] = {}
    for spec in runtime_specs:
        if spec.name.startswith("cmd_"):
            continue
        mean_tag = f"DORAEMON/mean/{spec.name}"
        std_tag = f"DORAEMON/std/{spec.name}"
        if mean_tag not in all_tags or std_tag not in all_tags:
            print(f"[WARN] DORAEMON tag not found: {mean_tag}")
            continue

        mean_val = ea.Scalars(mean_tag)[-1].value
        std_val = ea.Scalars(std_tag)[-1].value
        lo = max(spec.min_bound, mean_val - 2.0 * std_val)
        hi = min(spec.max_bound, mean_val + 2.0 * std_val)

        mapped = _DORAEMON_TO_DR_FIELD.get(spec.name)
        field_name: str = mapped if mapped is not None else spec.name
        if not hasattr(cfg, field_name):
            print(f"[WARN] DomainRandomizationCfg has no field '{field_name}'")
            continue

        setattr(cfg, field_name, (lo, hi))
        raw[field_name] = (mean_val, std_val)
        print(f"  DORAEMON DR: {field_name:30s} mean={mean_val:.4f}  std={std_val:.4f}  -> [{lo:.4f}, {hi:.4f}]")

    return cfg, raw


def get_hard_dr_config() -> DomainRandomizationCfg:
    """Get the hard DR config (DORAEMON if loaded, otherwise HardDomainRandomizationCfg)."""
    cfg = _DORAEMON_FULL_DR if _DORAEMON_FULL_DR is not None else HardDomainRandomizationCfg()
    cfg.enable = True
    return cfg


# ============================================================================
# DR Configuration (main-specific fields)
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
    # r13: ocean current strength is DORAEMON-managed during training. Eval must
    # also scale this range with DR level so none/soft/medium/hard match training
    # curriculum stages. Nominal=(0,0) (no current), hard=(0,1) (full range).
    "ocean_current_strength_range",
]

_DR_FLOAT_FIELDS = [
    "payload_cog_offset_xy_radius",
    "buoy_moment_arm",
]


# True physics-nominal values for the scale=0 ("none") DR anchor.
# Scale fields -> 1.0 (no modification), offset fields -> 0.0 (centered),
# payload -> 0.0 (no payload), water -> 1000.0 (pure water).
# Joint actuator and buoy_moment_arm are asset-specific: omitted here so they
# fall back to the base cfg midpoint (preserves prior behavior).
_TRUE_NOMINAL_PHYSICS: dict[str, float] = {
    # Scale fields
    "added_mass_scale": 1.0,
    "linear_damping_scale": 1.0,
    "quadratic_damping_scale": 1.0,
    "volume_scale": 1.0,
    "inertia_scale": 1.0,
    "body_mass_scale": 1.0,
    "yaw_damping_scale": 1.0,
    "joint_effort_limit_range": 1.0,
    "thrust_coefficient_scale": 1.0,
    "time_constant_scale": 1.0,
    # Offset fields (centered)
    "cob_offset_x": 0.0,
    "cob_offset_y": 0.0,
    "cob_offset_z": 0.0,
    "cog_offset_x": 0.0,
    "cog_offset_y": 0.0,
    "cog_offset_z": 0.0,
    # Absolute physical defaults
    "water_density_range": 1000.0,
    "payload_mass_range": 0.0,
    "payload_cog_offset_z": 0.0,
    "joint_static_friction_range": 0.0,
    "joint_viscous_friction_range": 0.0,
    # Float fields
    "payload_cog_offset_xy_radius": 0.0,
    # r13: ocean current strength tuple collapses to (0, 0) at nominal -> no current.
    # HardDR full range = (0, 1). Linear interpolation yields per-level strength range.
    "ocean_current_strength_range": 0.0,
}


def _make_nominal_dr() -> DomainRandomizationCfg:
    """Construct true nominal DR config (single-point distribution at physics defaults).

    Fields listed in _TRUE_NOMINAL_PHYSICS use the explicit nominal value.
    Fields not listed (joint_stiffness/damping, buoy_moment_arm) fall back to
    the base DomainRandomizationCfg midpoint, since these are asset-specific
    and have no obvious physics-true value.
    """
    base = DomainRandomizationCfg()
    nominal = DomainRandomizationCfg()

    for field_name in _DR_TUPLE_FIELDS:
        if field_name in _TRUE_NOMINAL_PHYSICS:
            val = _TRUE_NOMINAL_PHYSICS[field_name]
            setattr(nominal, field_name, (val, val))
        else:
            lo, hi = getattr(base, field_name)
            mid = (lo + hi) / 2.0
            setattr(nominal, field_name, (mid, mid))

    for field_name in _DR_FLOAT_FIELDS:
        if field_name in _TRUE_NOMINAL_PHYSICS:
            setattr(nominal, field_name, _TRUE_NOMINAL_PHYSICS[field_name])
        # Otherwise leave at base default (e.g. buoy_moment_arm).

    return nominal


def build_dr_config(scale: float) -> DomainRandomizationCfg:
    """Build DR config by interpolating between true nominal and the hard anchor.

    Hard anchor priority:
        1. _DORAEMON_FULL_DR (DORAEMON-learned distribution, if loaded)
        2. HardDomainRandomizationCfg (matches training-time physics ranges)

    Note: previously the fallback was the base DomainRandomizationCfg, which
    is far narrower than the actual training DR. That caused all four levels
    to evaluate near-nominal physics regardless of the requested scale.
    """
    nominal = _make_nominal_dr()

    if scale <= 0.0:
        nominal.enable = True
        return nominal

    full: DomainRandomizationCfg = _DORAEMON_FULL_DR if _DORAEMON_FULL_DR is not None else HardDomainRandomizationCfg()
    # Allow scale > 1.0 for OOD eval (extrapolate bounds beyond training distribution).
    f = scale

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


def _collapse_dr_to_midpoint(cfg: DomainRandomizationCfg) -> None:
    """Collapse each tuple DR range to its midpoint (lo=hi=mid).

    Uniform sampling over (mid, mid) returns mid deterministically, giving
    reproducible physics for 1-env comparisons across independent runs.
    """
    for field_name in _DR_TUPLE_FIELDS:
        lo, hi = getattr(cfg, field_name)
        mid = (lo + hi) / 2.0
        setattr(cfg, field_name, (mid, mid))


# Set True by --deterministic-dr (static mode) to collapse DR bounds inside apply_dr_config.
_DETERMINISTIC_DR: bool = False
# Set True by --extreme-ood (static mode) to overwrite DR with fixed OOD preset values.
_APPLY_EXTREME_OOD: bool = False


# Extreme-OOD physics presets. Selectable via --ood-preset {v1,v2} (static mode).
# v1 = r13_A training hard DR upper bound ("at edge"). v2 = +20-30% beyond (true OOD).
_EXTREME_OOD_PHYSICS_V1: dict[str, float] = {
    "payload_mass_range":       3.00,
    "added_mass_scale":         1.50,
    "linear_damping_scale":     1.70,
    "quadratic_damping_scale":  1.70,
    "water_density_range":      1025.0,
    "volume_scale":             1.25,
    "inertia_scale":            2.00,
    "body_mass_scale":          1.25,
    "cog_offset_x": 0.020, "cog_offset_y": 0.020, "cog_offset_z": 0.040,
    "cob_offset_x": 0.020, "cob_offset_y": 0.020, "cob_offset_z": 0.040,
    "payload_cog_offset_z":    -0.050,
}
_EXTREME_OOD_PHYSICS_V1_FLOATS: dict[str, float] = {
    "payload_cog_offset_xy_radius": 0.08,
}

_EXTREME_OOD_PHYSICS_V2: dict[str, float] = {
    "payload_mass_range":       3.50,
    "added_mass_scale":         1.80,
    "linear_damping_scale":     2.05,
    "quadratic_damping_scale":  2.05,
    "water_density_range":      1045.0,
    "volume_scale":             1.45,
    "inertia_scale":            2.50,
    "body_mass_scale":          1.50,
    "cog_offset_x": 0.028, "cog_offset_y": 0.028, "cog_offset_z": 0.055,
    "cob_offset_x": 0.028, "cob_offset_y": 0.028, "cob_offset_z": 0.055,
    "payload_cog_offset_z":    -0.075,
}
_EXTREME_OOD_PHYSICS_V2_FLOATS: dict[str, float] = {
    "payload_cog_offset_xy_radius": 0.10,
}

# Default preset (v2); overridden at CLI parse time by --ood-preset.
_EXTREME_OOD_PHYSICS: dict[str, float] = _EXTREME_OOD_PHYSICS_V2
_EXTREME_OOD_PHYSICS_FLOATS: dict[str, float] = _EXTREME_OOD_PHYSICS_V2_FLOATS


# ---- .mat metadata: variable descriptors (unit + meaning) ----
# Maps each raw array key written into data_{level}.mat to its physical unit and a
# one-line description, so a MATLAB session can interpret the file without reading
# this Python source. Keys must match the array names produced by run_evaluation().
_MAT_VAR_DESC: dict[str, tuple[str, str]] = {
    "time":             ("s",        "rollout time vector, shape (1, T)"),
    "actual_roll_deg":  ("deg",      "measured roll angle, shape (T, num_envs)"),
    "actual_pitch_deg": ("deg",      "measured pitch angle, shape (T, num_envs)"),
    "error_roll":       ("deg",      "roll tracking error (target - actual), (T, num_envs)"),
    "error_pitch":      ("deg",      "pitch tracking error (target - actual), (T, num_envs)"),
    "yaw_rate":         ("rad/s",    "measured yaw rate, shape (T, num_envs)"),
    "lin_vel_x":        ("m/s",      "body-frame surge velocity, shape (T, num_envs)"),
    "lin_vel_y":        ("m/s",      "body-frame sway velocity, shape (T, num_envs)"),
    "lin_vel_z":        ("m/s",      "body-frame heave velocity, shape (T, num_envs)"),
    "lin_vel_norm":     ("m/s",      "linear velocity magnitude, shape (T, num_envs)"),
    "action_magnitude": ("unitless",     "L2 norm of the 8-D action, shape (T, num_envs)"),
    "delta_action":     ("action-norm", "||a(z) - a(z_ablated)|| per env-step; z-ablation diagnostic (#1-A); (T, num_envs); zeros when ablation off"),
    "terminated":       ("bool",        "per-step termination flag, shape (T, num_envs)"),
    "time_to_failure":  ("s",        "time of first termination per env, shape (1, num_envs)"),
    "target_roll_deg":  ("deg",      "commanded roll setpoint, shape (1, T)"),
    "target_pitch_deg": ("deg",      "commanded pitch setpoint, shape (1, T)"),
    "target_yaw_rate":  ("rad/s",    "commanded yaw-rate setpoint, shape (1, T)"),
    "target_vx":        ("m/s",      "commanded surge setpoint, shape (1, T)"),
    "target_vy":        ("m/s",      "commanded sway setpoint, shape (1, T)"),
    "target_vz":        ("m/s",      "commanded heave setpoint, shape (1, T)"),
}


def _build_mat_meta(array_data: dict, level: str, dr_scale: float,
                    checkpoint: str, task: str, num_envs: int, mode: str) -> dict:
    """Build a self-describing metadata struct for a data_{level}.mat file.

    scipy.io.savemat nests a dict as a MATLAB struct, so the returned dict becomes
    `data.meta.<field>` in MATLAB. `eval_axis` is assigned per-FILE (per DR level),
    not per-variable: the same signal (e.g. error_roll) reads as a robustness signal
    at nominal DR levels and an OOD-generalization signal at an OOD level.
    """
    # eval_axis is a coarse classification of what THIS file (DR level) measures,
    # mapping to the three model-selection axes in the eval-mode-restructure spec.
    if level.startswith("ood") or level == "extreme_ood":
        eval_axis = "ood_generalization"
    else:
        # none/soft/medium/hard sweep -> broad robustness; across-env spread within a
        # level also feeds policy_consistency (computed MATLAB-side from the env axis).
        eval_axis = "robustness;policy_consistency"

    variables = {}
    for key in array_data:
        unit, desc = _MAT_VAR_DESC.get(key, ("unknown", "undocumented array"))
        variables[key] = {"unit": unit, "description": desc}

    return {
        "dr_level": level,
        "dr_scale": float(dr_scale),
        "eval_axis": eval_axis,
        "mode": mode,
        "task": task,
        "checkpoint": checkpoint if checkpoint else "",
        "num_envs": int(num_envs),
        "dims_note": "per-env signals are (T_steps, num_envs); targets/time are (1, T_steps)",
        "variables": variables,
    }


def _apply_extreme_ood_physics(env_cfg) -> None:
    """Overwrite env_cfg.randomization: tuples -> (v,v); floats -> v (scalar)."""
    dr = env_cfg.randomization
    applied = 0
    for field_name, value in _EXTREME_OOD_PHYSICS.items():
        if not hasattr(dr, field_name):
            print(f"[WARN] extreme-ood: DR has no field '{field_name}', skipping.")
            continue
        setattr(dr, field_name, (value, value))  # collapse to fixed value
        applied += 1
    for field_name, value in _EXTREME_OOD_PHYSICS_FLOATS.items():
        if not hasattr(dr, field_name):
            print(f"[WARN] extreme-ood: DR has no float field '{field_name}', skipping.")
            continue
        setattr(dr, field_name, value)
        applied += 1
    print(f"[INFO] extreme-ood: applied {applied} fixed OOD physics values")


def apply_dr_config(env_cfg, scale: float) -> None:
    """Apply interpolated DR config to the environment config."""
    env_cfg.randomization = build_dr_config(scale)
    if _DETERMINISTIC_DR:
        _collapse_dr_to_midpoint(env_cfg.randomization)
    if _APPLY_EXTREME_OOD:
        _apply_extreme_ood_physics(env_cfg)


def apply_dr_mid_episode(raw_env, dr_cfg: DomainRandomizationCfg) -> None:
    """Apply new DR parameters mid-episode without resetting robot pose/velocity.

    Creates a DRSampler from the given config and calls randomization functions
    to change physics parameters in-place. Used by the periodic mode.
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
# static mode: trajectory, metrics, plots, evaluation loop
# (moved verbatim from eval_dr.py static.py)
# ============================================================================

# ============================================================================
# Trajectory + metrics (static mode)
# Moved to _eval_dr/{trajectory,metrics}.py (pure numpy, Isaac-Sim-free):
#   build_step_trajectory + ATT_AMP_DEG/LIN_VEL_AMP/YAW_RATE_AMP/WARMUP_SEGMENTS
#   _step_response_one_segment, _classify_segment, _get_block_step_range,
#   _pick_sample_env, _step_response_scalar_segment, compute_metrics
# imported at module top.
# ============================================================================


# ============================================================================
# Plots
# ============================================================================


def _plot_dr_distributions(
    dr_configs: dict[str, DomainRandomizationCfg],
    doraemon_raw: dict[str, tuple[float, float]],
    output_dir: str,
) -> None:
    """Visualize DR ranges per level, normalized to HardDomainRandomizationCfg.

    Each row is one DR parameter; each row contains 4 horizontal bars (one per
    DR level) showing the [lo, hi] range. The HardDomainRandomizationCfg range
    is the gray background and is normalized to [0, 1]. When DORAEMON state was
    loaded, the learned mean +/- 2*std is overlaid as a black star with caps.
    """
    fields = list(_DR_TUPLE_FIELDS)
    n_params = len(fields)
    levels = [lvl for lvl in DR_LEVELS if lvl in dr_configs]
    n_levels = len(levels)
    if n_params == 0 or n_levels == 0:
        return

    hard = HardDomainRandomizationCfg()
    fig, ax = plt.subplots(figsize=(11, max(8.0, n_params * 0.45)))

    y_pos = np.arange(n_params, dtype=float)
    bar_h = 0.8 / n_levels

    for i, level in enumerate(levels):
        cfg = dr_configs[level]
        offsets = (i - (n_levels - 1) / 2.0) * bar_h

        lows: list[float] = []
        widths: list[float] = []
        for field in fields:
            hard_lo, hard_hi = getattr(hard, field)
            hard_range = hard_hi - hard_lo
            cfg_lo, cfg_hi = getattr(cfg, field)
            if hard_range > 0:
                n_lo = (cfg_lo - hard_lo) / hard_range
                n_hi = (cfg_hi - hard_lo) / hard_range
            else:
                n_lo = n_hi = 0.5
            lows.append(n_lo)
            widths.append(max(n_hi - n_lo, 1e-3))  # tiny min width so single-point shows

        ax.barh(
            y_pos + offsets,
            widths,
            left=lows,
            height=bar_h * 0.92,
            color=DR_COLORS[level],
            label=f"{level} ({int(DR_SCALE[level] * 100)}%)",
            edgecolor="black",
            linewidth=0.4,
            alpha=0.85,
        )

    # HardDR reference band
    ax.axvspan(0.0, 1.0, alpha=0.08, color="gray", zorder=-2)
    ax.axvline(0.0, color="gray", linewidth=0.8, linestyle="--", zorder=-1)
    ax.axvline(1.0, color="gray", linewidth=0.8, linestyle="--", zorder=-1)

    # DORAEMON mean +/- 2*std markers (if available)
    if doraemon_raw:
        for j, field in enumerate(fields):
            if field not in doraemon_raw:
                continue
            mean, std = doraemon_raw[field]
            hard_lo, hard_hi = getattr(hard, field)
            hard_range = hard_hi - hard_lo
            if hard_range <= 0:
                continue
            m_norm = (mean - hard_lo) / hard_range
            s_norm = std / hard_range
            ax.errorbar(
                [m_norm],
                [y_pos[j]],
                xerr=[[2 * s_norm], [2 * s_norm]],
                fmt="*",
                color="black",
                markersize=11,
                ecolor="black",
                elinewidth=1.2,
                capsize=4,
                zorder=10,
            )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(fields, fontsize=8)
    ax.set_xlabel(
        "Normalized to HardDomainRandomizationCfg range  [0 = HardDR low, 1 = HardDR high]",
        fontsize=10,
    )
    title = "DR Distribution per Level (normalized to HardDR range)"
    if doraemon_raw:
        title += "\nblack star = DORAEMON learned mean +/- 2*std"
    ax.set_title(title, fontsize=11)
    ax.legend(loc="lower right", fontsize=9, framealpha=0.92)
    ax.set_xlim(-0.35, 1.35)
    ax.invert_yaxis()
    ax.grid(True, alpha=0.3, axis="x")

    plt.tight_layout()
    out = os.path.join(output_dir, "summary_drdist.png")
    plt.savefig(out, dpi=120, bbox_inches="tight")
    plt.close()
    print(f"  Saved: {out}")


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
    # z-ablation diagnostic (#1-A): ||action(z) - action(z_ablated)|| per env-step.
    # Only populated when the policy has an active z-ablation; stays zeros otherwise.
    delta_action = np.zeros((total_steps, num_envs))
    _ablation_active = getattr(policy_nn, "_z_ablation", None) is not None
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
            actions = policy(obs)  # ablated action (z_ablation active) -> stepped into env
            if _ablation_active:
                _prev = policy_nn._z_ablation
                policy_nn._z_ablation = None  # restore TRUE z for one diagnostic forward
                actions_normal = policy(obs)
                policy_nn._z_ablation = _prev  # re-ablate (cache for "mean" untouched)
                delta_action[step_idx] = (
                    (actions_normal - actions).norm(dim=-1).detach().cpu().numpy()
                )
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
        "delta_action": delta_action,
        "terminated": terminated,
        "time_to_failure": time_to_failure,
        "steps_per_segment": steps_per_seg,
        "segment_duration": segment_duration,
        "segment_names": segment_names,
        "warmup_steps": WARMUP_SEGMENTS * steps_per_seg,
    }


# ============================================================================
# Student latent diagnostic (integrated into static student mode, 2026-05-26)
# ============================================================================
# A distilled student can track well yet have a collapsed encoder (the frozen teacher
# actor carries it). `static` performance alone cannot tell -- so when a student is
# evaluated, we also log (l_hat = student-predicted latent, l_true = teacher's
# privileged latent) per step and summarize their agreement. Moved here from
# eval_student.py `latent` so a single static pass yields both performance and the
# encoder-fidelity diagnostic. See rule 03 ("encoder verification requires more than
# aggregate z_std").


class _InstrumentedStudentPolicy:
    """Wrap a StudentInLoopPolicy; log (l_hat, l_true) at every __call__.

    Replicates StudentInLoopPolicy.__call__'s forward so the intermediate latents can be
    captured WITHOUT calling the underlying __call__ (which would double-advance the TCN
    ring buffer / GRU hidden state). The returned action is identical to the wrapped
    policy's, so swapping it in is behavior-neutral for the rollout.
    """

    def __init__(self, student) -> None:
        self._s = student
        self.l_hat_log: list[np.ndarray] = []
        self.l_true_log: list[np.ndarray] = []

    def reset_logs(self) -> None:
        self.l_hat_log = []
        self.l_true_log = []

    def reset(self, env_ids=None) -> None:
        if env_ids is None or isinstance(env_ids, torch.Tensor):
            self._s.reset(env_ids)
        else:
            self._s.reset(torch.as_tensor(env_ids, dtype=torch.long))

    @torch.no_grad()
    def __call__(self, obs_td) -> torch.Tensor:
        s = self._s
        obs = obs_td["policy"]
        priv = obs_td["privileged"]
        l_true = s.teacher.encode_privileged(priv)  # (B, 9)

        if s.cfg.encoder_type == "tcn":
            assert s.ring is not None
            s.ring = torch.roll(s.ring, shifts=-1, dims=1)
            s.ring[:, -1] = obs
            l_hat = s.student(s.ring)
        else:
            obs_for_student = s.obs_normalizer(obs)
            l_hat_seq, s.hidden = s.student(obs_for_student.unsqueeze(1), hidden=s.hidden)
            l_hat = l_hat_seq[:, -1]

        obs_normed = s.teacher.normalize_obs(obs)
        action = s.teacher.actor_forward(obs_normed, l_hat)

        self.l_hat_log.append(l_hat.detach().cpu().numpy())
        self.l_true_log.append(l_true.detach().cpu().numpy())
        return action


def _summarize_latent(l_hat: np.ndarray, l_true: np.ndarray) -> dict:
    """Agreement metrics between student-predicted (l_hat) and teacher (l_true) latents.

    Shapes (T, E, D). overall/per-dim MSE = tracking of the latent; envvar = does the
    student latent distinguish envs as the teacher's does (collapse check across envs);
    tvar = does it vary over time (collapse check over the episode).
    """
    err = l_hat - l_true
    per_env_rmse = np.sqrt((err ** 2).mean(axis=(0, 2)))
    return {
        "overall_mse": float((err ** 2).mean()),
        "per_dim_mse": (err ** 2).mean(axis=(0, 1)).tolist(),
        "l_true_envvar_mean": float(l_true.var(axis=1).mean()),
        "l_hat_envvar_mean": float(l_hat.var(axis=1).mean()),
        "l_true_tvar_mean": float(l_true.var(axis=0).mean()),
        "l_hat_tvar_mean": float(l_hat.var(axis=0).mean()),
        "per_env_rmse_mean": float(per_env_rmse.mean()),
        "per_env_rmse_std": float(per_env_rmse.std()),
    }


# ============================================================================
# static mode: run function (was eval_dr.py static main)
# ============================================================================

def run_static(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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

    # Compute episode_length_s from trajectory (see TRAJECTORY_N_SEGMENTS).
    env_cfg.episode_length_s = TRAJECTORY_N_SEGMENTS * args_cli.segment_duration + 10.0

    # ---- Load checkpoint ----
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)

    # Student mode short-circuits the teacher-runner checkpoint search (mirrors segmented):
    # resume_path = student_ckpt so eval output lands under the STUDENT's run_id tree, while
    # params / DORAEMON DR resolve from the teacher's run dir.
    is_student_mode = getattr(args_cli, "student_ckpt", None) is not None
    if is_student_mode:
        if args_cli.teacher_ckpt is None or args_cli.encoder_type is None:
            raise ValueError("--student_ckpt requires both --teacher_ckpt and --encoder_type.")

    resume_path = None
    if is_student_mode:
        resume_path = args_cli.student_ckpt
        print(f"[INFO] Student mode: student_ckpt={resume_path}  teacher_ckpt={args_cli.teacher_ckpt}  encoder={args_cli.encoder_type}")
    elif use_checkpoint:
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
    # Student mode reads the teacher's params (the student reuses the teacher's env/agent cfg);
    # the DORAEMON DR auto-load below also keys off the teacher dir in student mode.
    run_agent_dict = None
    params_search_ckpt = args_cli.teacher_ckpt if is_student_mode else resume_path
    if params_search_ckpt:
        import yaml

        run_params_path = os.path.join(os.path.dirname(params_search_ckpt), "params", "agent.yaml")
        if os.path.isfile(run_params_path):
            try:
                with open(run_params_path) as f:
                    run_agent_dict = yaml.full_load(f)
                print(f"[INFO] Loaded agent params from run directory: {run_params_path}")
            except yaml.YAMLError as e:
                print(f"[WARN] Could not load run agent params, using task registry: {e}")
                run_agent_dict = None

    # ---- OOD scale override: replace 4-level loop with single OOD level ----
    # NOTE: preserve "none" key in DR_SCALE -- apply_dr_config(env_cfg, DR_SCALE["none"])
    # is used below as the initial (nominal) DR before rollout starts.
    if args_cli.ood_scale is not None:
        global DR_LEVELS, DR_SCALE
        ood_name = f"ood_{args_cli.ood_scale:.1f}x"
        if args_cli.deterministic_dr:
            ood_name += "_det"
        DR_LEVELS = [ood_name]
        DR_SCALE = {"none": 0.0, ood_name: args_cli.ood_scale}
        DR_COLORS[ood_name] = "#FF00FF"  # magenta for OOD
        print(f"\n[INFO] OOD eval mode: single level '{ood_name}' at scale={args_cli.ood_scale:.2f}\n")

    # ---- Deterministic DR: disable DORAEMON + collapse tuple DR ranges to midpoint ----
    # Applied AFTER env_cfg is built but BEFORE gym.make(...) so env init uses fixed values.
    if args_cli.deterministic_dr or args_cli.extreme_ood:
        if hasattr(env_cfg, "doraemon"):
            env_cfg.doraemon.enable = False
            print("[INFO] DORAEMON disabled")
    if args_cli.deterministic_dr:
        global _DETERMINISTIC_DR
        _DETERMINISTIC_DR = True  # apply_dr_config will now collapse tuples to midpoint
        print("[INFO] deterministic-dr: DR tuple ranges collapsed to midpoint -> fixed physics")

    # ---- Extreme OOD preset: overwrite DR with explicit out-of-training values ----
    if args_cli.extreme_ood:
        global _APPLY_EXTREME_OOD, _EXTREME_OOD_PHYSICS, _EXTREME_OOD_PHYSICS_FLOATS
        _APPLY_EXTREME_OOD = True
        if args_cli.ood_preset == "v1":
            _EXTREME_OOD_PHYSICS = _EXTREME_OOD_PHYSICS_V1
            _EXTREME_OOD_PHYSICS_FLOATS = _EXTREME_OOD_PHYSICS_V1_FLOATS
        else:
            _EXTREME_OOD_PHYSICS = _EXTREME_OOD_PHYSICS_V2
            _EXTREME_OOD_PHYSICS_FLOATS = _EXTREME_OOD_PHYSICS_V2_FLOATS
        print(f"[INFO] extreme-ood preset={args_cli.ood_preset}: will apply {len(_EXTREME_OOD_PHYSICS)} fixed OOD physics values\n")

    # ---- v3: widen training DR ranges by `ood_range_scale` factor (random sample per env) ----
    if args_cli.ood_range_scale is not None:
        if hasattr(env_cfg, "doraemon"):
            env_cfg.doraemon.enable = False
            print("[INFO] DORAEMON disabled (v3 mode)")
        scale = args_cli.ood_range_scale
        dr = env_cfg.randomization
        widened = 0
        for field_name in list(vars(dr).keys()):
            val = getattr(dr, field_name)
            if isinstance(val, tuple) and len(val) == 2 and all(isinstance(v, (int, float)) for v in val):
                lo, hi = val
                mid = (lo + hi) / 2.0
                half = (hi - lo) / 2.0 * scale
                setattr(dr, field_name, (mid - half, mid + half))
                widened += 1
        print(f"[INFO] v3 ood-range-scale {scale:.2f}: widened {widened} DR ranges by {(scale-1)*100:+.0f}%\n")

    # ---- Output directory ----
    if args_cli.output_dir:
        output_dir = args_cli.output_dir
    elif resume_path and (_run_eval_dir := eval_dir_for_checkpoint(resume_path, "static")) is not None:
        # Checkpoint lives in a run_id tree -> write eval under experiments/<run_id>/eval/ (#2).
        output_dir = str(_run_eval_dir)
    elif resume_path:
        suffix = f"eval_dr_ood_{args_cli.ood_scale:.1f}x" if args_cli.ood_scale else "eval_dr"
        output_dir = os.path.join(os.path.dirname(resume_path), suffix)
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = task_name.removeprefix("Isaac-").lower().replace("-", "_").removesuffix("_v0")
        output_dir = os.path.join("logs", "eval_dr", folder_name, ts)
        os.makedirs(output_dir, exist_ok=True)
        update_latest_symlink(output_dir)  # logs/eval_dr/<folder>/latest -> newest eval
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR override ----
    # Default behavior: auto-load DORAEMON-learned distribution from the run dir
    # and use it as the hard-DR anchor. Use --no-doraemon-dr to fall back to
    # HardDomainRandomizationCfg (the static training-time physics ranges).
    #
    # --doraemon-dr-from=<path> overrides the auto-load path with an explicit
    # run dir. This is used to evaluate every ablation variant on a common test
    # distribution (typically the r13_A baseline's final DR), so cross-variant
    # comparisons are not confounded by per-variant curriculum drift.
    global _DORAEMON_FULL_DR, _DORAEMON_RAW
    if args_cli.doraemon_dr_from:
        dr_source = args_cli.doraemon_dr_from
        if not os.path.isdir(dr_source):
            raise FileNotFoundError(f"--doraemon-dr-from path does not exist: {dr_source}")
        print(f"\n[INFO] Loading DORAEMON-learned DR from override path: {dr_source}")
        cfg, raw = load_doraemon_dr(dr_source)
        if cfg is None:
            raise RuntimeError(
                f"--doraemon-dr-from requested but no DORAEMON tags found in {dr_source}. "
                "Check that the run dir contains a TB event file with DORAEMON/mean/* scalars."
            )
        _DORAEMON_FULL_DR = cfg
        _DORAEMON_RAW = raw
        print("[INFO] Hard DR = DORAEMON-learned distribution from override (mean +/- 2*std).\n")
    elif args_cli.doraemon_dr and (params_search_ckpt or resume_path):
        # Student mode: DORAEMON tags live in the teacher's TB events, not the student dir.
        run_dir = os.path.dirname(params_search_ckpt if is_student_mode else resume_path)
        print(f"\n[INFO] Attempting to load DORAEMON-learned DR from: {run_dir}")
        cfg, raw = load_doraemon_dr(run_dir)
        if cfg is not None:
            _DORAEMON_FULL_DR = cfg
            _DORAEMON_RAW = raw
            print("[INFO] Hard DR = DORAEMON-learned distribution (mean +/- 2*std).\n")
        else:
            print("[INFO] No DORAEMON state found in run dir. Falling back to HardDomainRandomizationCfg.\n")
    else:
        print("\n[INFO] DORAEMON-DR disabled. Hard DR = HardDomainRandomizationCfg (static).\n")

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

    if is_student_mode:
        # Student encoder + frozen teacher actor, same loader segmented uses. The resulting
        # callable matches the policy(obs) signature run_evaluation expects, so the static
        # pipeline (4 DR levels + .mat + PNG set) is identical to the teacher's.
        from constrained_albc.analysis.student_policy import build_student_policy_fn

        student_policy = build_student_policy_fn(
            teacher_ckpt=args_cli.teacher_ckpt,
            student_ckpt=args_cli.student_ckpt,
            encoder_type=args_cli.encoder_type,
            num_envs=num_envs,
            device=str(device),
        )
        # Wrap so the rollout also records (l_hat, l_true) for the encoder-fidelity
        # diagnostic. The wrapper's action == the wrapped policy's, so performance metrics
        # are unaffected; it doubles as policy_nn so run_evaluation's reset hook works.
        policy = _InstrumentedStudentPolicy(student_policy)
        policy_nn = policy
        print(f"[INFO] Loaded student ({args_cli.encoder_type}) + frozen teacher actor (latent diagnostic on)")
    elif use_checkpoint and resume_path:
        runner_cls_map = {
            "ALBCConstraintEncoderRunner": ConstraintEncoderRunner,
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

        # z-ablation diagnostic (encoder gap #1): enable on the loaded policy network.
        if getattr(args_cli, "z_ablation", None) is not None:
            if not hasattr(policy_nn, "set_z_ablation"):
                raise AttributeError(
                    f"--z_ablation set but policy {type(policy_nn).__name__} has no "
                    "set_z_ablation (not an ActorCriticEncoder)"
                )
            nominal_obs = None
            if args_cli.z_ablation == "mean":
                nominal_obs = env.get_observations()
            policy_nn.set_z_ablation(args_cli.z_ablation, nominal_obs=nominal_obs)
            print(f"[INFO] z-ablation ENABLED: mode={args_cli.z_ablation}")
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

    # Student mode also collects the encoder-fidelity diagnostic (l_hat vs l_true) per level.
    latent_summary = {"encoder_type": args_cli.encoder_type, "levels": {}} if is_student_mode else None

    for level in DR_LEVELS:
        dr_pct = int(DR_SCALE[level] * 100)
        print(f"\n{'=' * 60}")
        print(f"  DR Level: {level.upper()} | DR Scale: {dr_pct}%")
        print(f"{'=' * 60}")

        apply_dr_config(raw_env.cfg, DR_SCALE[level])

        if is_student_mode:
            policy.reset_logs()  # per-level latent logs (don't carry across DR levels)

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

        array_data = {k: v for k, v in data.items() if isinstance(v, np.ndarray)}
        np.savez_compressed(os.path.join(output_dir, f"data_{level}.npz"), **array_data)
        # Also write a MATLAB .mat alongside the .npz for MATLAB-side visualization
        # (.npz is a Python-only pickle container that MATLAB cannot load directly).
        # A `meta` struct rides along so MATLAB can interpret each array (unit,
        # description, eval axis, DR level) without reading this source.
        from scipy.io import savemat

        mat_payload = dict(array_data)
        mat_payload["meta"] = _build_mat_meta(
            array_data, level=level, dr_scale=DR_SCALE[level],
            checkpoint=resume_path or "", task=task_name,
            num_envs=num_envs, mode="static",
        )
        savemat(os.path.join(output_dir, f"data_{level}.mat"), mat_payload, do_compression=True)

        if is_student_mode:
            l_hat = np.stack(policy.l_hat_log, axis=0)    # (T, E, 9)
            l_true = np.stack(policy.l_true_log, axis=0)  # (T, E, 9)
            np.savez_compressed(os.path.join(output_dir, f"latent_{level}.npz"), l_hat=l_hat, l_true=l_true)
            ls = _summarize_latent(l_hat, l_true)
            latent_summary["levels"][level] = ls
            print(f"  [latent] overall_mse={ls['overall_mse']:.5f}  "
                  f"per_env_rmse={ls['per_env_rmse_mean']:.4f}+/-{ls['per_env_rmse_std']:.4f}  "
                  f"l_hat/l_true envvar={ls['l_hat_envvar_mean']:.4f}/{ls['l_true_envvar_mean']:.4f}")

        metrics = compute_metrics(data)
        all_metrics[level] = metrics

        print(f"\n  Results ({level}, DR {dr_pct}%):")
        print("    [Attitude]")
        print(f"      Error:     {metrics['total_att_error']:.1f} +/- {metrics['total_att_error_std']:.1f} deg")
        print(f"      SS error:  {np.nanmean(metrics['att_ss_errors']):.1f} deg")
        print(f"      SS jitter: {np.nanmean(metrics['att_ss_jitters']):.2f} deg")
        print(f"      Settling:  {np.nanmean(metrics['att_settling_times']):.2f} s")
        print(f"      Rise time: {np.nanmean(metrics['att_rise_times']):.3f} s")
        print(f"      Overshoot: {np.nanmean(metrics['att_overshoot_pcts']):.1f}%")
        print(f"      Zero-X:   {np.nanmean(metrics['att_zero_crossings']):.1f}")
        print("    [Lin Vel]")
        print(f"      Error:     {metrics['total_lin_vel_error']:.3f} m/s")
        for ax_name in ["vx", "vy", "vz"]:
            ss = np.nanmean(metrics['lin_vel_ss_errors'][ax_name])
            jt = np.nanmean(metrics['lin_vel_ss_jitters'][ax_name])
            rt = np.nanmean(metrics['lin_vel_rise_times'][ax_name])
            os_p = np.nanmean(metrics['lin_vel_overshoot_pcts'][ax_name])
            zx = np.nanmean(metrics['lin_vel_zero_crossings'][ax_name])
            print(f"      {ax_name}: SS={ss:.3f} Jit={jt:.3f} Rise={rt:.3f}s OS={os_p:.1f}% ZX={zx:.1f}")
        print(f"      Survival:  {metrics['lin_vel_survival']:.0f}%")
        print("    [Yaw]")
        print(f"      Error:     {metrics['total_yaw_rate_error']:.4f} rad/s")
        print(f"      SS error:  {np.nanmean(metrics['yaw_ss_errors']):.4f} rad/s")
        print(f"      SS jitter: {np.nanmean(metrics['yaw_ss_jitters']):.4f} rad/s")
        print(f"      Rise time: {np.nanmean(metrics['yaw_rise_times']):.3f} s")
        print(f"      Overshoot: {np.nanmean(metrics['yaw_overshoot_pcts']):.1f}%")
        print(f"      Zero-X:   {np.nanmean(metrics['yaw_zero_crossings']):.1f}")
        print(f"      Survival:  {metrics['yaw_survival']:.0f}%")
        print(f"    [Global] Survival: {metrics['survival_rate']:.0f}%")

    # ---- Generate plots ----
    print("\n[INFO] Generating plots...")
    generate_plots(all_data, all_metrics, output_dir)

    # DR distribution plot: rebuild the per-level configs and visualize.
    dr_configs_used = {lvl: build_dr_config(DR_SCALE[lvl]) for lvl in DR_LEVELS}
    _plot_dr_distributions(dr_configs_used, _DORAEMON_RAW, output_dir)

    # ---- Print final comparison ----
    print(f"\n{'=' * 100}")
    print("COMPARISON SUMMARY")
    print(f"{'=' * 100}")
    print(
        f"{'Level':<10} {'DR%':>5} {'AttErr':>10} {'AttSS':>8} {'Jitter':>7} {'Settle':>7} {'AttOS':>6} {'ZeroX':>6} "
        f"{'LinVel':>8} {'YawErr':>8} {'YawSS':>8} {'Surv':>6}"
    )
    print("-" * 110)
    for lvl in DR_LEVELS:
        m = all_metrics[lvl]
        print(
            f"{lvl:<10} "
            f"{int(DR_SCALE[lvl] * 100):4d}% "
            f"{m['total_att_error']:5.1f}+/-{m['total_att_error_std']:.1f} "
            f"{np.nanmean(m['att_ss_errors']):7.1f}d "
            f"{np.nanmean(m['att_ss_jitters']):6.2f}d "
            f"{np.nanmean(m['att_settling_times']):6.2f}s "
            f"{np.nanmean(m['att_overshoot_pcts']):5.1f}% "
            f"{np.nanmean(m['att_zero_crossings']):5.1f} "
            f"{m['total_lin_vel_error']:7.3f} "
            f"{m['total_yaw_rate_error']:7.4f} "
            f"{np.nanmean(m['yaw_ss_errors']):7.4f} "
            f"{m['survival_rate']:5.0f}%"
        )
    print("=" * 110)

    # ---- Student latent diagnostic summary ----
    if latent_summary is not None:
        with open(os.path.join(output_dir, "summary_latent.json"), "w") as f:
            json.dump(latent_summary, f, indent=2)
        print(f"\n{'=' * 70}\nLATENT DIAGNOSTIC (l_hat vs l_true) -- {args_cli.encoder_type}\n{'=' * 70}")
        print(f"{'Level':<10} {'mse':>9} {'per_env_rmse':>16} {'envvar h/t':>14} {'tvar h/t':>14}")
        for lvl in DR_LEVELS:
            s = latent_summary["levels"][lvl]
            print(f"{lvl:<10} {s['overall_mse']:9.5f} "
                  f"{s['per_env_rmse_mean']:7.4f}+/-{s['per_env_rmse_std']:.4f} "
                  f"{s['l_hat_envvar_mean']:6.4f}/{s['l_true_envvar_mean']:.4f} "
                  f"{s['l_hat_tvar_mean']:6.4f}/{s['l_true_tvar_mean']:.4f}")
        print("=" * 70)

    print(f"\nOutput saved to: {output_dir}")
    env.close()

    # Post-process: regenerate summary_*.png using per-env enhanced metrics
    # (overwrites the ensemble-mean-trajectory versions written above).
    try:
        from _analyze.recompute import _process_and_write as process_and_write
        # output_dir holds the data_*.npz; recompute reads <run_dir>/<data_subdir>/.
        # Split output_dir into parent + leaf so enhanced summaries land beside the
        # data, regardless of whether the leaf is the legacy "eval_dr" or a run-id-tree
        # timestamped folder (e.g. "static_<ts>").
        clean = output_dir.rstrip("/")
        run_dir = os.path.dirname(clean)
        data_subdir = os.path.basename(clean)
        print("\n[INFO] Regenerating summary_*.png with per-env metrics...")
        process_and_write(run_dir, data_subdir=data_subdir)
    except Exception as e:
        print(f"[WARN] Enhanced summary generation failed: {e}")


# ============================================================================
# periodic mode: evaluation loop, metrics, plots
# (moved from eval_dr_robustness.py; compute_metrics/generate_plots renamed to
#  _periodic_* to avoid clashing with the static-mode functions above)
# ============================================================================

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


# _settling_time + _periodic_compute_metrics moved to _eval_dr/metrics.py
# (pure numpy, imported at module top).


# ============================================================================
# Plotting
# ============================================================================


def _periodic_generate_plots(data: dict, metrics: dict, output_dir: str) -> None:
    """Generate time-series and summary plots."""
    time_s = data["time"]
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
    path = os.path.join(output_dir, "traj_periodic.png")
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
    path = os.path.join(output_dir, "summary_periodic.png")
    plt.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"[INFO] Saved: {path}")


# ============================================================================
# periodic mode: run function (was eval_dr_robustness main)
# ============================================================================

def run_periodic(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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
    elif resume_path and (_run_eval_dir := eval_dir_for_checkpoint(resume_path, "periodic")) is not None:
        # Checkpoint lives in a run_id tree -> write eval under experiments/<run_id>/eval/ (#2).
        output_dir = str(_run_eval_dir)
    elif resume_path:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr_robustness")
    else:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = task_name.removeprefix("Isaac-").lower().replace("-", "_").removesuffix("_v0")
        output_dir = os.path.join("logs", "eval_dr_robustness", folder_name, ts)
        os.makedirs(output_dir, exist_ok=True)
        update_latest_symlink(output_dir)  # logs/eval_dr_robustness/<folder>/latest -> newest eval
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR override ----
    global _DORAEMON_FULL_DR
    if args_cli.doraemon_dr and resume_path:
        run_dir = os.path.dirname(resume_path)
        print(f"\n[INFO] Attempting to load DORAEMON-learned DR from: {run_dir}")
        cfg, _ = load_doraemon_dr(run_dir)
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
            "ALBCConstraintEncoderRunner": ConstraintEncoderRunner,
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
        os.path.join(output_dir, "data_periodic.npz"),
        **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
    )

    # Compute metrics
    metrics = _periodic_compute_metrics(data)

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
    _periodic_generate_plots(data, metrics, output_dir)

    print(f"\nOutput saved to: {output_dir}")
    env.close()


# ============================================================================
# segmented mode: evaluation loop, per-seg metrics, plots
# (moved from eval_dr_switching.py; _bar_subplot -> _seg_bar_subplot and
#  _plot_summary_attitude -> _plot_seg_summary_attitude to avoid static-mode clash)
# ============================================================================

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

# compute_seg_metrics moved to _eval_dr/metrics.py (pure numpy, imported at module top).


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
    fig.savefig(os.path.join(output_dir, "traj_position.png"), dpi=150)
    plt.close(fig)


def _plot_attitude_drift(all_data: dict, levels: list[str], output_dir: str) -> None:
    """Per-DR-level roll/pitch/yaw drift from target rpy=0, env mean ± std, seg boundaries.

    Analogous to traj_position.png but for attitude. Single plot with all three angles.
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
    fig.savefig(os.path.join(output_dir, "traj_attitude.png"), dpi=150)
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


def _seg_bar_subplot(ax, x, heights, colors, xlabels, ylabel, title, yerr=None, ylim=None):
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
    _seg_bar_subplot(axes[0, 0], x, m, colors, xlabels, "Drift (m)", "Peak Pos Drift per Seg", yerr=s)
    # (0,1) SS drift norm per seg
    m, s = _collect_metric_across_levels(all_metrics, levels, "pos_drift_ss")
    _seg_bar_subplot(axes[0, 1], x, m, colors, xlabels, "Drift (m)", "SS Pos Drift (last 50% of seg)", yerr=s)

    # (1,0..2) SS DC offset per axis (signed mean to reveal systematic bias)
    for ci, (key, ax_name) in enumerate([("pos_x_ss", "X"), ("pos_y_ss", "Y"), ("pos_z_ss", "Z")]):
        row, col = divmod(1 + ci, 2)
        if row >= axes.shape[0]:
            break
        m, s = _collect_metric_across_levels(all_metrics, levels, key)
        _seg_bar_subplot(axes[row, col], x, m, colors, xlabels, f"{ax_name} drift (m, signed)",
                     f"{ax_name}-axis SS Bias (env mean)", yerr=s)

    # (2,1) Heavy-tail: % envs with peak drift > 0.1 m per seg
    pct = []
    for lvl in levels:
        mm = all_metrics[lvl]
        vals = np.concatenate([np.array(mm["per_seg"][s]["pos_drift_peak"]) for s in range(1, mm["num_segments"])])
        pct.append(100.0 * (vals > 0.1).mean())
    _seg_bar_subplot(axes[2, 1], x, pct, colors, xlabels, "% env×seg", "Heavy-tail: %env peak>0.1m")

    fig.tight_layout()
    fig.savefig(os.path.join(output_dir, "summary_position.png"), dpi=150)
    plt.close(fig)


def _plot_seg_summary_attitude(all_metrics: dict, levels: list[str], output_dir: str) -> None:
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
    _seg_bar_subplot(axes[1, 0], x, pct_r, colors_single, xlabels, "% env×seg", "Heavy-tail: %env roll peak>5°")
    _seg_bar_subplot(axes[1, 1], x, pct_p, colors_single, xlabels, "% env×seg", "Heavy-tail: %env pitch peak>5°")
    _seg_bar_subplot(axes[2, 0], x, pct_y, colors_single, xlabels, "% env×seg", "Heavy-tail: %env yaw peak>5°")

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
    fig.savefig(os.path.join(output_dir, "summary_attitude.png"), dpi=150)
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
    fig.savefig(os.path.join(output_dir, "traj_transient.png"), dpi=150)
    plt.close(fig)


# ============================================================================
# segmented mode: run function (was eval_dr_switching main)
# ============================================================================

def run_segmented(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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
    elif (_run_eval_dir := eval_dir_for_checkpoint(resume_path, "segmented")) is not None:
        # Checkpoint lives in a run_id tree -> write eval under experiments/<run_id>/eval/ (#2).
        output_dir = str(_run_eval_dir)
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
        from constrained_albc.analysis.student_policy import build_student_policy_fn

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
        runner_cls_map = {"ALBCConstraintEncoderRunner": ConstraintEncoderRunner}
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
            os.path.join(output_dir, f"data_{level}.npz"),
            **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
        )
        all_metrics[level] = compute_seg_metrics(data)

    # Plots
    print("\n[INFO] Generating plots...")
    _plot_position_drift(all_data, DR_LEVELS, output_dir)
    _plot_attitude_drift(all_data, DR_LEVELS, output_dir)
    _plot_summary_pos(all_metrics, all_data, DR_LEVELS, output_dir)
    _plot_seg_summary_attitude(all_metrics, DR_LEVELS, output_dir)
    _plot_transient_overlay(all_data, DR_LEVELS, output_dir)

    # Save summary JSON
    with open(os.path.join(output_dir, "summary_segmented.json"), "w") as f:
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


# ============================================================================
# Dispatch
# ============================================================================

_MODE_DISPATCH = {
    "static": run_static,
    "periodic": run_periodic,
    "segmented": run_segmented,
}


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    _MODE_DISPATCH[args_cli.mode](env_cfg, agent_cfg)


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]  -- hydra_task_config injects env_cfg, agent_cfg
    assert simulation_app is not None
    simulation_app.close()
