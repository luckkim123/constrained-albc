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
    ./isaaclab.sh -p constrained_albc/analysis/eval.py static --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 64 --headless
    ./isaaclab.sh -p constrained_albc/analysis/eval.py static --extreme-ood --ood-preset v2 --headless
    ./isaaclab.sh -p constrained_albc/analysis/eval.py periodic --num_steps 4 --headless
    ./isaaclab.sh -p constrained_albc/analysis/eval.py segmented --segment_duration 5 --headless
"""

import argparse
import os
import sys

# cli_args is vendored locally (was scripts/reinforcement_learning/rsl_rl/ in isaaclab, not migrated)
# common.py and cli_args.py both live alongside this file
sys.path.insert(0, os.path.dirname(__file__))

# Pure (Isaac-Sim-free) trajectory + metric helpers, extracted to _eval_dr/.
# Safe to import before the AppLauncher boot below (numpy only).
from _eval_dr.dr_snapshot import (  # type: ignore[import-not-found]  # noqa: E402
    per_env_dr_from_tensors,
    per_env_fault_from_tensors,
)
from _eval_dr.metrics import (  # type: ignore[import-not-found]  # noqa: E402
    _get_block_step_range,
    _periodic_compute_metrics,
    _pick_sample_env,
    compute_metrics,
    compute_seg_metrics,
    summarize_student_extra,
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
    sp.add_argument(
        "--fault",
        action="store_true",
        help="Enable per-env fault injection (cfg.fault.enable). Records fault_<name>[N] "
        "per-env into data_<level>.npz alongside dr_<name>. Off -> npz is fault-free.",
    )
    sp.add_argument(
        "--fault_fixed_health",
        type=str,
        default=None,
        help="Deterministic per-thruster health for ALL envs: num_thrusters comma-separated "
        "values in [0,1] (e.g. '1,1,1,1,0,1' = thruster m4 dead, the FTC-m4 probe). Implies "
        "--fault and bypasses the Bernoulli sampler. Off -> Bernoulli path unchanged.",
    )
    sp.add_argument(
        "--privileged-fault-obs",
        action="store_true",
        help="Arm B (FaultDR-AB): build the env with use_privileged_fault_obs=True (28->34D "
        "privileged obs). REQUIRED to eval an Arm-B checkpoint whose encoder was trained on 34D "
        "privileged input -- omitting it dim-mismatches the encoder. No-op for Arm-A/anchor (28D).",
    )
    cli_args.add_rsl_rl_args(sp)


def _apply_fault_cli(env_cfg, args_cli) -> None:
    """Wire the --fault / --fault_fixed_health CLI onto env_cfg.fault (no-op if absent).

    --fault enables per-env fault injection; --fault_fixed_health additionally pins a
    deterministic per-thruster health vector across all envs (and implies enable=True).
    Shared by every eval mode so the two flags behave identically in each.
    """
    # Arm-B privileged-fault-obs: set BEFORE any env build so state_space 28->34
    # materializes (mirrors train.py). No-op when the cfg lacks the field.
    if getattr(args_cli, "privileged_fault_obs", False) and hasattr(env_cfg, "use_privileged_fault_obs"):
        env_cfg.use_privileged_fault_obs = True
    if not hasattr(env_cfg, "fault"):
        return
    if getattr(args_cli, "fault", False):
        env_cfg.fault.enable = True
    ffh = getattr(args_cli, "fault_fixed_health", None)
    if ffh:
        env_cfg.fault.enable = True
        env_cfg.fault.thruster_fixed_health = tuple(float(x) for x in ffh.split(","))


parser = argparse.ArgumentParser(description="DR-robustness evaluation for ALBC.")
subparsers = parser.add_subparsers(dest="mode", required=True)

# ----------------------------------------------------------------------------
# static: evaluate policy across fixed DR levels (none/soft/medium/hard) [main eval]
# ----------------------------------------------------------------------------
sp_static = subparsers.add_parser("static", description="Evaluate DR robustness across fixed DR levels.")
_add_common(sp_static)
sp_static.add_argument("--segment_duration", type=float, default=5.0, help="Duration per segment in seconds.")
sp_static.add_argument(
    "--control-delay",
    type=int,
    default=0,
    help="E2 latency instrument: inject a FIXED N-step transport delay "
    "(control_delay_steps=(N,N)) on the applied action at EVERY DR level "
    "(1 step = 20 ms @ 50 Hz). 0 = off, byte-identical to stock (the env skips the "
    "DelayBuffer when hi<=0). Does not touch _DR_TUPLE_FIELDS, so all DR levels stay "
    "comparable with prior evals.",
)
sp_static.add_argument(
    "--inject-yaw-torque",
    type=float,
    default=0.0,
    help="E3 yaw-torque instrument: apply a CONSTANT external body-frame yaw torque Mz "
    "(N.m) on the robot base link at EVERY physics step, at every DR level. "
    "0.0 = off, byte-identical to stock (no wrench-composer hook installed).",
)
sp_static.add_argument(
    "--att-amp-deg",
    type=float,
    default=None,
    help="Static eval attitude step amplitude in deg; default = full trained box (trajectory.ATT_AMP_DEG).",
)
sp_static.add_argument(
    "--yaw-rate-amp",
    type=float,
    default=None,
    help="Static eval yaw-rate step amplitude in rad/s; default = full trained box (trajectory.YAW_RATE_AMP).",
)
sp_static.add_argument(
    "--save-policy-obs",
    action="store_true",
    default=False,
    help="Also store the realized 69D policy obs per step into data_<level>.npz (additive; off by default).",
)
sp_static.add_argument(
    "--save-action-std",
    action="store_true",
    default=False,
    help="Also store the per-step action std (from the non-sampling Gaussian distribution) into "
    "data_<level>.npz (additive; off by default).",
)
sp_static.add_argument(
    "--doraemon-dr",
    action=argparse.BooleanOptionalAction,
    default=True,
    help="Use DORAEMON-learned DR (mean +/- 2*std) as hard level. Default: auto-load from run dir. "
         "Use --no-doraemon-dr to fall back to the static hard DomainRandomizationCfg.",
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
    "--ood",
    action="store_true",
    default=False,
    help="APPEND a 5th 'ood' level to the none/soft/medium/hard sweep (side-by-side). "
         "The ood level uses DORAEMON-derived OOD bounds (held-out thruster axes pushed "
         "past their fixed training range; cog/cob offsets past the DORAEMON ceiling) so "
         "summary.json can report a per-axis generalization gap (ood - hard). Requires "
         "--doraemon-dr (the default). Distinct from --ood-scale (which REPLACES the sweep).",
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
# C1-latsens probe: how sensitive is the frozen actor to error in the latent it is handed?
# Perturbs ONLY the actor's input, in units of the error the student already exhibits, so
# k=1 means 'double the latent error this student already has, in the shape it already has'.
# k=0 (default) is byte-identical to every existing eval.
sp_static.add_argument("--latent_noise_k", type=float, default=0.0,
                       help="Latent perturbation multiplier for the C1-latsens sweep (0 = off).")
sp_static.add_argument("--latent_noise_sigma_from", type=str, default=None,
                       help="summary_latent.json whose per-level per_dim_mse sets the per-dim sigma "
                            "(sigma = sqrt(per_dim_mse)); required when --latent_noise_k > 0.")
sp_static.add_argument(
    "--z_ablation",
    type=str,
    default=None,
    choices=["zero", "mean"],
    help="Inference-time encoder z-ablation (gap-#1 diagnostic): zero=z->0, "
    "mean=z->encode(nominal). Unset=normal eval (default).",
)
sp_static.add_argument(
    "--flat-target",
    dest="flat_target",
    action="store_true",
    default=False,
    help="Zero all attitude/yaw/lin commands (pure station-keeping at (0,0)). "
    "Isolates joint1 drift: a monotonic ramp in joint1_target with no command "
    "is the free-DOF drift signature. Keeps the trajectory length/DR sweep.",
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
    import plotly.graph_objects as go  # noqa: F401
    from plotly.subplots import make_subplots  # noqa: F401
    _HAS_PLOTLY = True
except ImportError:
    _HAS_PLOTLY = False

matplotlib.use("Agg")
import dr_config as _dr_config_module  # type: ignore[import-not-found]  # noqa: E402
import matplotlib.pyplot as plt
import numpy as np
import rsl_rl.runners.on_policy_runner as _runner_module
import torch
from common import DR_COLORS
from common import DR_LEVELS as _DEFAULT_DR_LEVELS
from common import DR_SCALE as _DEFAULT_DR_SCALE
from dr_config import (  # type: ignore[import-not-found]  # noqa: E402
    _DR_TUPLE_FIELDS,
    _apply_extreme_ood_physics,
    _collapse_dr_to_midpoint,
    build_dr_config,
    build_ood_dr_config,
    get_hard_dr_config,
    load_doraemon_dr,
)
from eval_plots import (  # type: ignore[import-not-found]  # noqa: E402
    _bar_subplot,
    _periodic_generate_plots,
    _plot_attitude_drift,
    _plot_position_drift,
    _plot_seg_summary_attitude,
    _plot_summary_pos,
    _plot_transient_overlay,
    generate_plots,
)
from eval_serialize import _build_mat_meta, write_eval_npz  # type: ignore[import-not-found]  # noqa: E402
from matplotlib.ticker import MultipleLocator
from paths import eval_dir_for_checkpoint  # type: ignore[import-not-found]  # noqa: E402  run_id-tree eval output (#2)
from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import DirectRLEnvCfg
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.math import euler_xyz_from_quat, quat_rotate_inverse

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

from constrained_albc.envs.main.algorithms import ConstraintTRPO
from constrained_albc.envs.main.config import (
    DomainRandomizationCfg,
)
from constrained_albc.envs.main.encoder import ActorCriticEncoder
from constrained_albc.envs.main.mdp import (
    DRSampler,
    randomize_body_mass,
    randomize_hydrodynamics,
    randomize_ocean_current,
    randomize_payload,
)
from constrained_albc.envs.main.runners import ConstraintEncoderRunner, sync_policy_obs_dim
from constrained_albc.envs.main.utils import update_latest_symlink

# Runtime-mutable copies (overridden by --ood-scale in static mode)
DR_LEVELS: list[str] = list(_DEFAULT_DR_LEVELS)
DR_SCALE: dict[str, float] = dict(_DEFAULT_DR_SCALE)

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




def apply_dr_config(env_cfg, scale: float) -> None:
    """Apply interpolated DR config to the environment config."""
    env_cfg.randomization = build_dr_config(scale)
    if _dr_config_module._DETERMINISTIC_DR:
        _collapse_dr_to_midpoint(env_cfg.randomization)
    if _dr_config_module._APPLY_EXTREME_OOD:
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
    """Visualize DR ranges per level, normalized to the hard DomainRandomizationCfg.

    Each row is one DR parameter; each row contains 4 horizontal bars (one per
    DR level) showing the [lo, hi] range. The hard DomainRandomizationCfg range
    is the gray background and is normalized to [0, 1]. When DORAEMON state was
    loaded, the learned mean +/- 2*std is overlaid as a black star with caps.
    """
    fields = list(_DR_TUPLE_FIELDS)
    n_params = len(fields)
    levels = [lvl for lvl in DR_LEVELS if lvl in dr_configs]
    n_levels = len(levels)
    if n_params == 0 or n_levels == 0:
        return

    hard = DomainRandomizationCfg()
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
        "Normalized to DomainRandomizationCfg range  [0 = HardDR low, 1 = HardDR high]",
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


def _read_per_env_dr(raw_env) -> dict[str, np.ndarray]:
    """Read each env's post-randomize DR physics tensors and shape them into dr_<name>[N].

    Called right after the throwaway reset has fixed per-env domain randomization. The
    physics tensors ARE the per-env DR values (post-clamp = what the policy experienced);
    we snapshot them and hand them to the pure ``per_env_dr_from_tensors`` transform.
    Robust to envs without payload/hydro state (returns whatever channels exist).
    """
    from constrained_albc.envs.main.mdp.events import _get_hydro_base  # sim-bound, lazy

    def _np(t):
        return t.detach().cpu().numpy()

    tensors: dict[str, np.ndarray] = {}
    if getattr(raw_env, "_payload_mass", None) is not None:
        tensors["payload_mass"] = _np(raw_env._payload_mass)
    if getattr(raw_env, "_payload_cog_offset", None) is not None:
        tensors["payload_cog_offset"] = _np(raw_env._payload_cog_offset)

    hydro = getattr(raw_env, "_hydro", None)
    if hydro is not None:
        base = _get_hydro_base(hydro)
        tensors["cob"] = _np(hydro.center_of_buoyancy)
        tensors["cob_base"] = _np(base.cob)
        tensors["cog"] = _np(hydro.center_of_gravity)
        tensors["cog_base"] = _np(base.cog)
        tensors["added_mass"] = _np(hydro.added_mass_matrix)
        tensors["linear_damping"] = _np(hydro.linear_damping)
        if getattr(hydro, "body_mass", None) is not None:
            tensors["body_mass"] = _np(hydro.body_mass)

    return per_env_dr_from_tensors(tensors)


def _read_per_env_fault(raw_env) -> dict[str, np.ndarray]:
    """Read each env's post-reset FAULT tensors and shape them into fault_<name>[N].

    Namespace-disjoint from _read_per_env_dr (dr_ vs fault_): a fault is an actuator /
    sensor FAILURE, not a DR physical-parameter spread, so it gets its own axis for the
    failing-env join. Every buffer is read defensively with getattr -- if fault injection
    is disabled (or this env predates the fault buffers) the channel is simply absent and
    no fault_ key is emitted. The npz still records the contract explicitly via the scalar
    ``fault_injection`` flag (True iff any fault_ key was captured), so consumers branch
    on the flag rather than on a KeyError.

    Buffer locations:
        thruster_health  raw_env._thruster._thruster_health  (N, 6) -- in the marinelab model
        sensor_noise     raw_env._sensor_noise_scale          (N,)   -- on the env
        joint_health     raw_env._joint_health                (N,)   -- on the env
    """

    def _np(t):
        return t.detach().cpu().numpy()

    tensors: dict[str, np.ndarray] = {}

    thruster = getattr(raw_env, "_thruster", None)
    if thruster is not None and getattr(thruster, "_thruster_health", None) is not None:
        tensors["thruster_health"] = _np(thruster._thruster_health)

    if getattr(raw_env, "_sensor_noise_scale", None) is not None:
        tensors["sensor_noise"] = _np(raw_env._sensor_noise_scale)

    if getattr(raw_env, "_joint_health", None) is not None:
        tensors["joint_health"] = _np(raw_env._joint_health)

    return per_env_fault_from_tensors(tensors)


def _install_yaw_torque_injector(raw_env, mz: float) -> None:
    """E3 instrument: apply a constant external body-frame yaw torque Mz on the base link.

    Wraps `raw_env._apply_action` (called once per physics substep, isaaclab
    envs/direct_rl_env.py `step()` decimation loop) so the injected torque is re-added
    AFTER the env's own hydro/thruster wrench is set on the same body every substep --
    `permanent_wrench_composer.set_forces_and_torques` is a SET, not an ADD, so injecting
    only once (e.g. before `env.step()`) would be silently overwritten by `_apply_action`.
    Re-adding every substep also survives env resets: `_reset_idx` -> `robot.reset()`
    zeroes the composer for the reset envs, but the very next `_apply_action` call
    (start of the next substep, for ALL envs) re-adds Mz before `write_data_to_sim()`
    pushes the buffer to PhysX, so no env is ever left without the injected torque.
    """
    body_ids = raw_env._body_id  # same "base" link the main hydro/thruster wrench uses
    num_envs = raw_env.num_envs
    device = raw_env.device
    zero_forces = torch.zeros(num_envs, len(body_ids), 3, device=device)
    torques = torch.zeros(num_envs, len(body_ids), 3, device=device)
    torques[:, :, 2] = mz

    orig_apply_action = raw_env._apply_action

    def _apply_action_with_yaw_torque():
        orig_apply_action()
        raw_env._robot.permanent_wrench_composer.add_forces_and_torques(
            forces=zero_forces, torques=torques, body_ids=body_ids, is_global=False
        )

    raw_env._apply_action = _apply_action_with_yaw_torque
    print(
        f"[INFO] inject_yaw_torque={mz:.3f} N.m constant Mz on body {body_ids} "
        f"('{raw_env.cfg.hydrodynamics.body_name}') every physics step (all DR levels)"
    )


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
    save_policy_obs: bool = False,
    save_action_std: bool = False,
) -> dict:
    """Run one evaluation pass and collect per-step data.

    Injects 6-DOF commands from targets dict:
    - roll_deg, pitch_deg: attitude commands (deg -> rad)
    - vx, vy, vz: linear velocity commands (m/s, body frame)
    - yaw_rate: yaw rate command (rad/s)

    save_policy_obs / save_action_std: purely additive diagnostics. When set, also
    accumulate the realized 69D policy obs (pre-step) and the per-step action std
    (from a non-sampling distribution populate, NOT .act() -- the stepped action stays
    the deterministic act_inference mean either way) into the returned dict under
    "policy_obs" / "action_std". Off by default -> no extra memory, no extra keys.
    """
    if save_action_std and not hasattr(policy_nn, "_update_distribution"):
        raise AttributeError(
            f"--save-action-std set but policy {type(policy_nn).__name__} has no "
            "_update_distribution (not a PolicyBase-derived policy)"
        )
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
    # Joint1 (arm rotation) trajectory for flat-target drift analysis. joint1_cmd
    # is the policy's action[0] (the delta fed to the integrator); joint1_target is
    # the integrated setpoint (_joint_pos_targets[:,0]); joint1_pos is the measured
    # joint angle. A monotonic ramp in joint1_target at a flat (0,0) command is the
    # drift signature; a bounded target near nominal means centering worked.
    joint1_cmd = np.zeros((total_steps, num_envs))
    joint1_pos = np.zeros((total_steps, num_envs))
    joint1_target = np.zeros((total_steps, num_envs))
    # z-ablation diagnostic (#1-A): ||action(z) - action(z_ablated)|| per env-step.
    # Only populated when the policy has an active z-ablation; stays zeros otherwise.
    delta_action = np.zeros((total_steps, num_envs))
    _ablation_active = getattr(policy_nn, "_z_ablation", None) is not None
    # Termination
    terminated = np.zeros((total_steps, num_envs), dtype=bool)
    time_to_failure = np.full(num_envs, float("nan"))
    # Optional raw policy-obs / action-std logs (populated only when the matching
    # flag is set; empty lists -> excluded from `out` below -> byte-identical npz
    # to before this diagnostic existed).
    policy_obs_log: list[np.ndarray] = []
    action_std_log: list[np.ndarray] = []

    # Force full reset via throwaway step
    raw_env.episode_length_buf[:] = raw_env.max_episode_length
    obs = env.get_observations()
    with torch.inference_mode():
        obs, _, _, _ = env.step(policy(obs))
        if hasattr(policy_nn, "reset"):
            policy_nn.reset(torch.ones(num_envs, 1, dtype=torch.bool, device=device))
    raw_env.episode_length_buf[:] = 0

    # Snapshot each env's now-fixed DR (post-clamp physics tensors = what the policy
    # experiences). Saved per-env so analysis can join failing envs <-> their DR.
    per_env_dr = _read_per_env_dr(raw_env)
    # Snapshot each env's now-fixed FAULT (thruster health / sensor noise / joint health).
    # Empty when fault injection is disabled -> npz stays byte-identical to the DR-only case.
    per_env_fault = _read_per_env_fault(raw_env)

    target_roll_rad = np.deg2rad(target_roll_deg)
    target_pitch_rad = np.deg2rad(target_pitch_deg)
    terminated_ever = np.zeros(num_envs, dtype=bool)

    # Capability guard (NOT a --task string match): the attitude_only env has only
    # _ang_cmd (roll/pitch/yaw_rate) and no _vel_cmd_lin, so lin-vel command
    # injection + lin-vel data/metrics are skipped for it. The full-DOF teacher
    # has _vel_cmd_lin -> has_lin_vel True -> code path byte-identical (zero regression).
    has_lin_vel = hasattr(raw_env, "_vel_cmd_lin")

    for step_idx in range(total_steps):
        # Inject commands from trajectory. _ang_cmd (attitude + yaw rate) is always
        # present; lin-vel is injected only when the env tracks it.
        raw_env._ang_cmd[:, 0] = target_roll_rad[step_idx]
        raw_env._ang_cmd[:, 1] = target_pitch_rad[step_idx]
        raw_env._ang_cmd[:, 2] = targets["yaw_rate"][step_idx]
        if has_lin_vel:
            raw_env._vel_cmd_lin[:, 0] = targets["vx"][step_idx]
            raw_env._vel_cmd_lin[:, 1] = targets["vy"][step_idx]
            raw_env._vel_cmd_lin[:, 2] = targets["vz"][step_idx]

        with torch.inference_mode():
            actions = policy(obs)  # ablated action (z_ablation active) -> stepped into env
            if save_policy_obs:
                policy_obs_log.append(obs["policy"].detach().cpu().numpy())
            if save_action_std:
                # Non-sampling: populates policy_nn.distribution from the already-computed
                # (deterministic) `actions` mean, does NOT call .act()/.sample(), and does
                # NOT change `actions` itself (env.step still steps the same tensor below).
                policy_nn._update_distribution(actions)
                action_std_log.append(policy_nn.action_std.detach().cpu().numpy())
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

        # Joint1 trajectory (per-axis action[0] + integrated target + measured pos)
        joint1_cmd[step_idx] = actions[:, 0].detach().cpu().numpy()
        joint1_target[step_idx] = raw_env._joint_pos_targets[:, 0].detach().cpu().numpy()
        joint1_pos[step_idx] = (
            raw_env._robot.data.joint_pos[:, raw_env._albc_joint_ids[0]].detach().cpu().numpy()
        )

        # Attitude: actual + error
        roll_cur, pitch_cur, _ = euler_xyz_from_quat(raw_env._robot.data.root_quat_w)
        actual_roll[step_idx] = torch.rad2deg(roll_cur).cpu().numpy()
        actual_pitch[step_idx] = torch.rad2deg(pitch_cur).cpu().numpy()

        att_err = raw_env._att_rp_err
        error_roll[step_idx] = torch.rad2deg(att_err[:, 0]).cpu().numpy()
        error_pitch[step_idx] = torch.rad2deg(att_err[:, 1]).cpu().numpy()

        # Linear velocity (body frame) -- only meaningful when the env tracks lin-vel.
        if has_lin_vel:
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
            seg_idx = min(step_idx // steps_per_seg, len(segment_names) - 1)
            lv_str = ""
            if has_lin_vel:
                lv_mean = np.mean(lin_vel_norm[step_idx][alive_mask]) if alive_mask.any() else float("nan")
                lv_str = f"lin_vel={lv_mean:.3f}m/s "
            print(
                f"  [{step_idx + 1:6d}/{total_steps}] "
                f"seg={segment_names[seg_idx]:30s} "
                f"att_err={mean_err:5.1f}deg "
                f"{lv_str}"
                f"alive={alive_count}/{num_envs}"
            )

    out = {
        "time": time_s,
        "target_roll_deg": target_roll_deg,
        "target_pitch_deg": target_pitch_deg,
        "target_yaw_rate": targets["yaw_rate"],
        "actual_roll_deg": actual_roll,
        "actual_pitch_deg": actual_pitch,
        "error_roll": error_roll,
        "error_pitch": error_pitch,
        "yaw_rate": yaw_rate,
        "action_magnitude": action_magnitude,
        "delta_action": delta_action,
        # Joint1 drift diagnostics (per-step, (T, num_envs)): policy command,
        # integrated target, measured position. Used by the flat-target drift check.
        "joint1_cmd": joint1_cmd,
        "joint1_target": joint1_target,
        "joint1_pos": joint1_pos,
        "terminated": terminated,
        "time_to_failure": time_to_failure,
        "steps_per_segment": steps_per_seg,
        "segment_duration": segment_duration,
        "segment_names": segment_names,
        "warmup_steps": WARMUP_SEGMENTS * steps_per_seg,
        # Capability flag consumed by compute_metrics (and downstream) to skip the
        # lin-vel block for the attitude_only env. True for the full-DOF teacher.
        "has_lin_vel": has_lin_vel,
        # Per-env DR sampled values (dr_<name>[num_envs]) for failure<->DR join analysis.
        **per_env_dr,
        # Per-env fault values (fault_<name>[num_envs]); empty when fault disabled.
        **per_env_fault,
        # G5: explicit contract flag. fault_<name> keys are absent-by-design on a
        # healthy eval, so consumers branch on this scalar instead of a KeyError.
        "fault_injection": np.array(bool(per_env_fault)),
    }
    # lin-vel arrays/targets only when the env tracks lin-vel (attitude_only omits
    # them -> compute_metrics sees no lin_vel keys and the npz stays lin-vel-free).
    if has_lin_vel:
        out.update({
            "target_vx": targets["vx"],
            "target_vy": targets["vy"],
            "target_vz": targets["vz"],
            "lin_vel_x": lin_vel_x,
            "lin_vel_y": lin_vel_y,
            "lin_vel_z": lin_vel_z,
            "lin_vel_norm": lin_vel_norm,
        })
    # Optional raw diagnostics (additive; keys present only when the matching
    # --save-* flag was set, so default output is byte-identical to before).
    if policy_obs_log:
        out["policy_obs"] = np.stack(policy_obs_log, axis=0)  # (T, num_envs, policy_obs_dim: 69 main / 87 full_dof)
    if action_std_log:
        out["action_std"] = np.stack(action_std_log, axis=0)  # (T, num_envs, action_dim)
    return out


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

    DELEGATES to the wrapped policy and reads the latent it publishes as `last_l_hat`.
    An earlier version instead REPLICATED StudentInLoopPolicy.__call__'s forward (to avoid
    double-advancing the TCN ring / GRU hidden state), and that copy silently dropped the
    obs normalization on the TCN branch: every TCN in-loop number produced by `static`
    between 2026-05-26 (096f5b8) and 2026-07-29 was measured with out-of-distribution
    encoder inputs, which invalidated the "observability floor" and DAgger readouts.
    Delegation makes that divergence class structurally impossible -- do NOT reintroduce a
    second encoder forward here.
    """

    def __init__(self, student) -> None:
        self._s = student
        self.l_hat_log: list[np.ndarray] = []
        self.l_true_log: list[np.ndarray] = []
        # B0 (2026-08-03): capture the obs4 extra channels for the bite check. This is pure
        # OBSERVATION -- it advances no state, draws no RNG, and copies to host immediately, so
        # the instrument is unperturbed. Local import because constrained_albc.envs triggers env
        # registration (and Isaac) at import time; same pattern as build_student_policy_fn.
        from constrained_albc.envs._core.student.models import STUDENT_EXTRA_OBS_KEY

        self._extra_key = STUDENT_EXTRA_OBS_KEY
        # X1 tail mode: the channels ride inside policy_obs (last _tail_n dims, raw),
        # not under the side-channel key -- capture them from there so the bite check /
        # channel-health summary exists for tail-mode runs too (the proposal registers
        # their absence as a VOID condition). 0 for every non-tail student.
        self._tail_n = getattr(student, "_tail_n", 0)
        self.extra_log: list[np.ndarray] = []

    def reset_logs(self) -> None:
        self.l_hat_log = []
        self.l_true_log = []
        self.extra_log = []

    def reset(self, env_ids=None) -> None:
        if env_ids is None or isinstance(env_ids, torch.Tensor):
            self._s.reset(env_ids)
        else:
            self._s.reset(torch.as_tensor(env_ids, dtype=torch.long))

    @torch.no_grad()
    def __call__(self, obs_td) -> torch.Tensor:
        s = self._s
        l_true = s.teacher.encode_privileged(obs_td["privileged"])  # (B, 9)
        action = s(obs_td)                                          # advances ring/hidden once
        l_hat = s.last_l_hat                                        # (B, 9), published by __call__

        self.l_hat_log.append(l_hat.detach().cpu().numpy())
        self.l_true_log.append(l_true.detach().cpu().numpy())
        if self._extra_key in obs_td:
            self.extra_log.append(obs_td[self._extra_key].detach().cpu().numpy())
        elif self._tail_n:
            self.extra_log.append(obs_td["policy"][..., -self._tail_n:].detach().cpu().numpy())
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
# shared eval setup helpers (used by run_static / run_periodic / run_segmented)
# ============================================================================

def _resolve_eval_output_dir(resume_path, mode: str):
    """Resolve the two universally-shared output-dir branches across run modes.

    All three run funcs (static/periodic/segmented) begin output-dir resolution
    with the same two checks: an explicit --output_dir override, then the
    run_id-tree path via eval_dir_for_checkpoint (#2). This centralizes only
    those two; each caller keeps its OWN mode-specific fallback (ood/robustness/
    switching suffix, ts-based dir, student dir) because those genuinely differ.

    Returns (output_dir, handled):
      - (path, True)  -> output_dir is final; caller skips its fallback.
      - (None, False) -> caller applies its mode-specific fallback.
    """
    if args_cli.output_dir:
        return args_cli.output_dir, True
    if resume_path:
        run_eval_dir = eval_dir_for_checkpoint(resume_path, mode)
        if run_eval_dir is not None:
            # Checkpoint lives in a run_id tree -> write eval under experiments/<run_id>/eval/ (#2).
            return str(run_eval_dir), True
        print(
            f"[WARN] Checkpoint path has no 'train' path segment ({resume_path}), so it is not "
            "recognized as an experiments/<run_id>/train/ tree -- falling back to a legacy eval "
            "dir instead of experiments/<run_id>/eval/. Canonical form: "
            "experiments/<...>/<run_id>/train/<model>.pt."
        )
    return None, False


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
    # Fault injection: opt-in via --fault. Independent of observation_noise_model (which
    # eval turns off above) -- fault sensor noise is added directly in _get_observations.
    _apply_fault_cli(env_cfg, args_cli)

    # Compute episode_length_s from trajectory (see TRAJECTORY_N_SEGMENTS).
    env_cfg.episode_length_s = TRAJECTORY_N_SEGMENTS * args_cli.segment_duration + 10.0

    # ---- Load checkpoint ----
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)

    # Student mode short-circuits the teacher-runner checkpoint search (mirrors segmented):
    # resume_path = student_ckpt so eval output lands under the STUDENT's run_id tree, while
    # params / DORAEMON DR resolve from the teacher's run dir.
    is_student_mode = getattr(args_cli, "student_ckpt", None) is not None
    _latent_sigma_by_level: dict[str, torch.Tensor] | None = None  # C1-latsens, armed below
    if is_student_mode:
        if args_cli.teacher_ckpt is None or args_cli.encoder_type is None:
            raise ValueError("--student_ckpt requires both --teacher_ckpt and --encoder_type.")

    # A student trained with the extra sensor channels needs the env to publish them,
    # AND needs the exact sensor-model parameters it was trained on (extra_obs_hold_steps,
    # heave_lag_tau, depth_noise_std, accel_noise_std -- these define what the channels
    # physically ARE, set by hydra override at train time and otherwise persisted
    # nowhere). Read both off the CHECKPOINT rather than adding CLI flags: a flag can be
    # forgotten, and a forgotten flag would silently evaluate the student against an
    # absent key or against a DIFFERENT sensor model than it was trained on (IMPORTANT-1
    # fix, fix-wave 2026-08-03). weights_only=False explicit: see StudentCfg docstring.
    _ENV_SENSOR_CFG_KEYS = ("extra_obs_hold_steps", "heave_lag_tau", "depth_noise_std", "accel_noise_std")
    if is_student_mode:
        _student_blob = torch.load(args_cli.student_ckpt, map_location="cpu", weights_only=False)
        _sc = _student_blob.get("cfg", {})
        _gen1 = _sc.get("extra_obs_dim", 0) > 0
        _tail = bool(_sc.get("extra_obs_from_policy_tail", False))
        if _gen1 or _tail:
            # gen-1 publishes the channels as a side-channel obs key; X1 tail mode needs the
            # gen-2 env to fold them into the policy_obs tail instead. Both flags read off
            # the CHECKPOINT, which closes the remembered-CLI-flag trap for tail-mode ckpts.
            # (A PLAIN gen-2 student -- extra_obs_dim=0, tail off, e.g. Phase E -- is not
            # detectable from its cfg and still needs env.use_extra_policy_obs=True on the
            # CLI, exactly as before.) The sensor-model knobs below restore identically in
            # both modes: the channels are the same compute_student_extra_obs output.
            _env_flag = "use_student_extra_obs" if _gen1 else "use_extra_policy_obs"
            # Guard the whole block, not each setattr: the flag and the four sensor params are
            # declared as one unit on ALBCEnvCfg, so if the gate field is absent this is a
            # non-main variant (full_dof/TDC) that cannot publish the channels at all. Without
            # this, setattr would CREATE dead fields and the student would be evaluated against
            # an env silently missing its extra channels.
            if not hasattr(env_cfg, _env_flag):
                raise RuntimeError(
                    f"student checkpoint requires env flag '{_env_flag}' but "
                    f"{type(env_cfg).__name__} has no such field -- the extra sensor channels "
                    "are envs/main only; this student cannot be evaluated on this task."
                )
            setattr(env_cfg, _env_flag, True)
            _env_sensor_cfg = _student_blob.get("env_sensor_cfg")
            if _env_sensor_cfg:
                for _k in _ENV_SENSOR_CFG_KEYS:
                    if _k in _env_sensor_cfg:
                        setattr(env_cfg, _k, _env_sensor_cfg[_k])
            else:
                print(
                    f"[WARN] student checkpoint {args_cli.student_ckpt} has no "
                    "'env_sensor_cfg' (pre-fix-wave checkpoint) -- falling back to "
                    "ALBCEnvCfg defaults for extra_obs_hold_steps/heave_lag_tau/"
                    "depth_noise_std/accel_noise_std. These may NOT match what this "
                    "student was actually trained on."
                )

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

    # ---- OOD side-by-side: APPEND a 5th 'ood' level to the in-dist sweep ----
    # Unlike --ood-scale (which REPLACES the sweep), --ood keeps none/soft/medium/hard
    # and adds 'ood' so summary.json can report the in-dist(hard)-vs-ood generalization
    # gap. The ood level's DR is NOT a scalar interpolation; DR_SCALE["ood"]=1.0 is a
    # display sentinel only -- the actual cfg is built by build_ood_dr_config at the
    # apply/plot sites (special-cased on level == "ood").
    if args_cli.ood:
        # DR_LEVELS / DR_SCALE are already declared global by the --ood-scale block
        # above (a single compile-time global covers the whole function).
        if "ood" not in DR_LEVELS:
            DR_LEVELS = [*DR_LEVELS, "ood"]
        DR_SCALE = {**DR_SCALE, "ood": 1.0}  # sentinel for display (DR% label); not used to build the cfg
        DR_COLORS["ood"] = "#FF00FF"  # magenta for OOD
        print("\n[INFO] OOD side-by-side: appended 'ood' level (DORAEMON-derived OOD bounds).\n")

    # ---- Deterministic DR: disable DORAEMON + collapse tuple DR ranges to midpoint ----
    # Applied AFTER env_cfg is built but BEFORE gym.make(...) so env init uses fixed values.
    if args_cli.deterministic_dr or args_cli.extreme_ood:
        if hasattr(env_cfg, "doraemon"):
            env_cfg.doraemon.enable = False
            print("[INFO] DORAEMON disabled")
    if args_cli.deterministic_dr:
        _dr_config_module._DETERMINISTIC_DR = True  # apply_dr_config will now collapse tuples to midpoint
        print("[INFO] deterministic-dr: DR tuple ranges collapsed to midpoint -> fixed physics")

    # ---- Extreme OOD preset: overwrite DR with explicit out-of-training values ----
    if args_cli.extreme_ood:
        _dr_config_module._APPLY_EXTREME_OOD = True
        if args_cli.ood_preset == "v1":
            _dr_config_module._EXTREME_OOD_PHYSICS = _dr_config_module._EXTREME_OOD_PHYSICS_V1
            _dr_config_module._EXTREME_OOD_PHYSICS_FLOATS = _dr_config_module._EXTREME_OOD_PHYSICS_V1_FLOATS
        else:
            _dr_config_module._EXTREME_OOD_PHYSICS = _dr_config_module._EXTREME_OOD_PHYSICS_V2
            _dr_config_module._EXTREME_OOD_PHYSICS_FLOATS = _dr_config_module._EXTREME_OOD_PHYSICS_V2_FLOATS
        print(f"[INFO] extreme-ood preset={args_cli.ood_preset}: will apply {len(_dr_config_module._EXTREME_OOD_PHYSICS)} fixed OOD physics values\n")

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
    # Flat-target eval gets its own mode tag so its eval/static_flat_<ts>/ dir does
    # not collide with (or look identical to) the tilted eval/static_<ts>/ dir.
    _static_mode = "static_flat" if getattr(args_cli, "flat_target", False) else "static"
    output_dir, _handled = _resolve_eval_output_dir(resume_path, _static_mode)
    if not _handled and resume_path:
        suffix = f"eval_dr_ood_{args_cli.ood_scale:.1f}x" if args_cli.ood_scale else "eval_dr"
        output_dir = os.path.join(os.path.dirname(resume_path), suffix)
    elif not _handled:
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
    # the static hard DomainRandomizationCfg (the training-time physics ranges).
    #
    # --doraemon-dr-from=<path> overrides the auto-load path with an explicit
    # run dir. This is used to evaluate every ablation variant on a common test
    # distribution (typically the r13_A baseline's final DR), so cross-variant
    # comparisons are not confounded by per-variant curriculum drift.
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
        _dr_config_module._DORAEMON_FULL_DR = cfg
        _dr_config_module._DORAEMON_RAW = raw
        print("[INFO] Hard DR = DORAEMON-learned distribution from override (mean +/- 2*std).\n")
    elif args_cli.doraemon_dr and (params_search_ckpt or resume_path):
        # Student mode: DORAEMON tags live in the teacher's TB events, not the student dir.
        run_dir = os.path.dirname(params_search_ckpt if is_student_mode else resume_path)
        print(f"\n[INFO] Attempting to load DORAEMON-learned DR from: {run_dir}")
        cfg, raw = load_doraemon_dr(run_dir)
        if cfg is not None:
            _dr_config_module._DORAEMON_FULL_DR = cfg
            _dr_config_module._DORAEMON_RAW = raw
            print("[INFO] Hard DR = DORAEMON-learned distribution (mean +/- 2*std).\n")
        else:
            print("[INFO] No DORAEMON state found in run dir. Falling back to the static hard DomainRandomizationCfg.\n")
    else:
        print("\n[INFO] DORAEMON-DR disabled. Hard DR = static DomainRandomizationCfg.\n")

    # ---- Create env (initial DR = none) ----
    apply_dr_config(env_cfg, DR_SCALE["none"])
    # E2 latency instrument: control_delay_steps MUST be non-(0,0) at env __init__ so
    # _draw_control_delay allocates the DelayBuffer (albc_env.py:338); a buffer that starts
    # None stays None (the _reset_idx redraw is guarded by `if buf is not None`, line 1496),
    # so a purely per-level cfg change would never take effect. Set it here (after
    # apply_dr_config, which rebuilds randomization) AND per-level below (apply_dr_config wipes
    # it back to (0,0) each level, so the per-level reset must re-set it to draw lag=d).
    if args_cli.control_delay > 0:
        _cd0 = args_cli.control_delay
        env_cfg.randomization.control_delay_steps = (_cd0, _cd0)
    env = gym.make(args_cli.task, cfg=env_cfg)
    clip_actions = run_agent_dict.get("clip_actions") if run_agent_dict else agent_cfg.clip_actions
    env = RslRlVecEnvWrapper(env, clip_actions=clip_actions)

    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device

    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")
    print(f"[INFO] Segment duration: {args_cli.segment_duration}s")

    # E3 yaw-torque instrument: constant external Mz on the base link, applied at every
    # DR level (single hook, installed once -- raw_env persists across the level loop
    # below). 0.0 = off, byte-identical to stock (no hook installed).
    if args_cli.inject_yaw_torque != 0.0:
        _install_yaw_torque_injector(raw_env, args_cli.inject_yaw_torque)

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
        # C1-latsens: build the per-level per-dim sigma table from a previous summary_latent.json.
        # sigma_d = sqrt(per_dim_mse_d) = the RMSE this student already has on dim d at that level.
        if args_cli.latent_noise_k:
            if not args_cli.latent_noise_sigma_from:
                raise ValueError("--latent_noise_k > 0 requires --latent_noise_sigma_from")
            with open(args_cli.latent_noise_sigma_from) as _f:
                _lat = json.load(_f)
            _latent_sigma_by_level = {
                lv: torch.sqrt(torch.tensor(v["per_dim_mse"], dtype=torch.float32, device=device))
                for lv, v in _lat["levels"].items()
            }
            print(f"[INFO] C1-latsens armed: k={args_cli.latent_noise_k} "
                  f"sigma from {args_cli.latent_noise_sigma_from}")
            for _lv, _s in _latent_sigma_by_level.items():
                print(f"[INFO]   sigma[{_lv}] = {[round(float(x), 4) for x in _s]}")
    elif use_checkpoint and resume_path:
        # Encoder policies build at the env's real obs width (69->72 with use_bias_ema_obs);
        # stock OnPolicyRunner has no sync of its own (PPO-Enc arm), so sync here for every path.
        sync_policy_obs_dim(env, agent_dict)
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
        att_amp_deg=args_cli.att_amp_deg,
        yaw_rate_amp=args_cli.yaw_rate_amp,
    )
    if getattr(args_cli, "flat_target", False):
        # Pure station-keeping: zero every command channel so the only thing that
        # can move joint1 is the policy's own bias -> isolates free-DOF drift.
        for _k in targets:
            targets[_k] = np.zeros_like(targets[_k])
        print("[INFO] --flat-target: all commands zeroed (station-keeping drift check).")
    print(
        f"[INFO] Trajectory: {len(segment_names)} segs x {args_cli.segment_duration}s"
        f" = {len(time_s)} steps ({time_s[-1]:.0f}s)"
        f", warmup={WARMUP_SEGMENTS} segs ({warmup_steps} steps)"
    )
    _att_amp_used = ATT_AMP_DEG if args_cli.att_amp_deg is None else args_cli.att_amp_deg
    _yaw_rate_amp_used = YAW_RATE_AMP if args_cli.yaw_rate_amp is None else args_cli.yaw_rate_amp
    print(f"[INFO] Targets: att +-{_att_amp_used}deg, lin +-{LIN_VEL_AMP}m/s, yaw +-{_yaw_rate_amp_used}rad/s")

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

        if level == "ood":
            # GAP 1: the ood level is a full DORAEMON-derived OOD config, not a
            # scalar interpolation -- route around apply_dr_config (Option A).
            raw_env.cfg.randomization = build_ood_dr_config(_dr_config_module._DORAEMON_RAW)
        else:
            apply_dr_config(raw_env.cfg, DR_SCALE[level])

        # E2 latency instrument: fixed N-step transport delay at every DR level. Set AFTER
        # the DR cfg is (re)built above and BEFORE the level's rollout reset, which redraws
        # per-env delay from cfg.randomization.control_delay_steps (albc_env.py:1497-1501).
        # control_delay_steps is not a _DR_TUPLE_FIELDS dim, so build_dr_config never sets it;
        # at --control-delay 0 this block is skipped and it stays (0,0) = byte-identical stock.
        if args_cli.control_delay > 0:
            _cd = args_cli.control_delay
            raw_env.cfg.randomization.control_delay_steps = (_cd, _cd)
            print(f"[INFO] control_delay={_cd} steps ({_cd * 20} ms) injected at level {level}")

        if is_student_mode:
            policy.reset_logs()  # per-level latent logs (don't carry across DR levels)
            # C1-latsens: arm the latent perturbation for THIS level. sigma is level-dependent
            # because it is the student's own measured per-dim in-loop RMSE at that level, which
            # is what makes k interpretable as a multiple of the error the student already has.
            if _latent_sigma_by_level is not None:
                policy._s.set_latent_noise(args_cli.latent_noise_k, _latent_sigma_by_level.get(level))

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
            save_policy_obs=args_cli.save_policy_obs,
            save_action_std=args_cli.save_action_std,
        )
        all_data[level] = data

        if is_student_mode and args_cli.latent_noise_k:
            # Bite check: a flat control result must be distinguishable from an injector that
            # silently did nothing (a previous eval-side delay probe was exactly that no-op).
            print(f"[C1-latsens] {level}: {policy._s.noise_report()}")

        array_data = {k: v for k, v in data.items() if isinstance(v, np.ndarray)}
        write_eval_npz(output_dir, level, array_data)
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
            # B0: the extra channels get their OWN file, never a new key inside latent_<level>.npz.
            # That file must stay identical to what the unpatched eval.py produced -- the
            # instrument-unperturbed proof this change has to pass, since C3's baseline came from
            # the unpatched instrument and B2's would come from this one. 38d979e is the cost of
            # asserting that identity instead of checking it.
            if policy.extra_log:
                # Isolated: an exception here would abort the level loop and lose
                # summary_latent.json for EVERY level, even though the per-level .npz already
                # landed. A diagnostic must not be able to destroy the measurement it annotates.
                try:
                    extra_arr = np.stack(policy.extra_log, axis=0)  # (T, E, 4)
                    np.savez_compressed(
                        os.path.join(output_dir, f"student_extra_{level}.npz"), extra=extra_arr
                    )
                    # Sensor params come from env_cfg, which the student checkpoint already
                    # restored above -- the noise floor tracks the sensor model the student was
                    # actually trained on instead of a hardcoded default that would silently
                    # stop matching the moment depth_noise_std or heave_lag_tau is varied.
                    es = summarize_student_extra(
                        extra_arr,
                        hold_steps=getattr(env_cfg, "extra_obs_hold_steps", 2),
                        control_dt=float(step_dt),
                        depth_noise_std=float(getattr(env_cfg, "depth_noise_std", 0.01)),
                        heave_lag_tau=float(getattr(env_cfg, "heave_lag_tau", 0.05)),
                    )
                    # Persist: a gate verdict that lives only in stdout is a gate someone
                    # re-derives by hand. New filename, so latent_<level>.npz stays identical.
                    with open(
                        os.path.join(output_dir, f"student_extra_summary_{level}.json"), "w"
                    ) as f:
                        json.dump(es, f, indent=2)
                    print(
                        f"  [extra] nonzero={es['nonzero']} time_varying={es['time_varying']} "
                        f"degenerate_envs={es['n_env_degenerate']} "
                        f"gravity_ok={es['gravity_ok']} (mean {es['gravity_mean']:+.3f}) "
                        f"hold_ok={es['hold_ok']} (repeat {es['repeat_fraction']:.3f} vs "
                        f"{es['expected_repeat_fraction']:.3f}) heave_snr={es['heave_snr']:.2f}"
                    )
                except Exception as e:  # noqa: BLE001 -- diagnostic must not abort the eval
                    print(f"  [WARN] extra-channel bite check failed: {e}")
            elif getattr(env_cfg, "use_student_extra_obs", False) or getattr(
                env_cfg, "use_extra_policy_obs", False
            ):
                # Loud on absence: the env was configured to publish/fold the channels and
                # none were logged. Staying silent here would reproduce the exact no-op the
                # gate exists to catch, one layer out. (Fires for a plain gen-2 student too:
                # its channel-health evidence genuinely is absent -- only tail-mode ckpts
                # extract the channels from the policy_obs tail.)
                print(
                    f"  [extra] NO channels logged at level={level} despite the env "
                    "being configured to publish/fold them (use_student_extra_obs / "
                    "use_extra_policy_obs) -- none were captured; "
                    "this run CANNOT be graded on the observability question."
                )
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
        # Lin-vel block only when the env tracks it (attitude_only skips it; the
        # metrics are all-NaN there and a printed line would be a meaningless lie).
        if data.get("has_lin_vel", True):
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
    # The ood level (GAP 1) is a full DORAEMON-derived cfg, not a scalar interp.
    dr_configs_used = {
        lvl: (build_ood_dr_config(_dr_config_module._DORAEMON_RAW) if lvl == "ood"
              else build_dr_config(DR_SCALE[lvl]))
        for lvl in DR_LEVELS
    }
    _plot_dr_distributions(dr_configs_used, _dr_config_module._DORAEMON_RAW, output_dir)

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
        # LinVel column shows '--' when the env doesn't track lin-vel (attitude_only).
        lv = m['total_lin_vel_error']
        lv_col = f"{lv:7.3f}" if all_data[lvl].get("has_lin_vel", True) and lv == lv else f"{'--':>7}"
        print(
            f"{lvl:<10} "
            f"{int(DR_SCALE[lvl] * 100):4d}% "
            f"{m['total_att_error']:5.1f}+/-{m['total_att_error_std']:.1f} "
            f"{np.nanmean(m['att_ss_errors']):7.1f}d "
            f"{np.nanmean(m['att_ss_jitters']):6.2f}d "
            f"{np.nanmean(m['att_settling_times']):6.2f}s "
            f"{np.nanmean(m['att_overshoot_pcts']):5.1f}% "
            f"{np.nanmean(m['att_zero_crossings']):5.1f} "
            f"{lv_col} "
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


# (plotting helpers moved to eval_plots.py)


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
    # Fault injection: opt-in via --fault. Independent of observation_noise_model (which
    # eval turns off above) -- fault sensor noise is added directly in _get_observations.
    _apply_fault_cli(env_cfg, args_cli)

    # Episode must be long enough for all DR steps
    env_cfg.episode_length_s = args_cli.step_duration * args_cli.num_steps + 10.0

    # Start with hard DR (will be re-randomized each step)
    env_cfg.randomization = DomainRandomizationCfg()
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
    output_dir, _handled = _resolve_eval_output_dir(resume_path, "periodic")
    if not _handled and resume_path:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr_robustness")
    elif not _handled:
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        folder_name = task_name.removeprefix("Isaac-").lower().replace("-", "_").removesuffix("_v0")
        output_dir = os.path.join("logs", "eval_dr_robustness", folder_name, ts)
        os.makedirs(output_dir, exist_ok=True)
        update_latest_symlink(output_dir)  # logs/eval_dr_robustness/<folder>/latest -> newest eval
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR override ----
    if args_cli.doraemon_dr and resume_path:
        run_dir = os.path.dirname(resume_path)
        print(f"\n[INFO] Attempting to load DORAEMON-learned DR from: {run_dir}")
        cfg, _ = load_doraemon_dr(run_dir)
        if cfg is not None:
            _dr_config_module._DORAEMON_FULL_DR = cfg
            print("[INFO] Hard DR = DORAEMON-learned distribution (mean +/- 2*std).\n")
        else:
            print("[INFO] No DORAEMON state found. Falling back to the static hard DomainRandomizationCfg.\n")
    else:
        print("\n[INFO] DORAEMON-DR disabled. Hard DR = static DomainRandomizationCfg.\n")

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
        # Same sync as run_static: stock OnPolicyRunner carries no obs-width sync (PPO-Enc arm).
        sync_policy_obs_dim(env, agent_dict)
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

    # Save raw data (G5: carry the same fault contract as the other modes)
    per_env_fault = _read_per_env_fault(raw_env)
    np.savez_compressed(
        os.path.join(output_dir, "data_periodic.npz"),
        **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
        **per_env_fault,
        fault_injection=np.array(bool(per_env_fault)),
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
# Plots (moved to eval_plots.py)
# ---------------------------------------------------------------------------


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
    # Fault injection: opt-in via --fault. Independent of observation_noise_model (which
    # eval turns off above) -- fault sensor noise is added directly in _get_observations.
    _apply_fault_cli(env_cfg, args_cli)
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
    output_dir, _handled = _resolve_eval_output_dir(resume_path, "segmented")
    if not _handled and is_student_mode:
        output_dir = os.path.join(os.path.dirname(os.path.dirname(resume_path)), "eval_dr_switching")
    elif not _handled:
        output_dir = os.path.join(os.path.dirname(resume_path), "eval_dr_switching")
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output: {output_dir}")

    # DORAEMON DR -- use teacher run for loading (student doesn't produce DORAEMON state)
    if args_cli.doraemon_dr:
        run_dir = os.path.dirname(args_cli.teacher_ckpt) if is_student_mode else os.path.dirname(resume_path)
        print(f"[INFO] Loading DORAEMON DR from: {run_dir}")
        cfg, raw = load_doraemon_dr(run_dir)
        if cfg is not None:
            _dr_config_module._DORAEMON_FULL_DR = cfg
            _dr_config_module._DORAEMON_RAW = raw
            print("[INFO] Hard DR = DORAEMON-learned distribution")
        else:
            print("[INFO] No DORAEMON state; using static DomainRandomizationCfg (hard)")

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
        # G5: same fault contract as static mode -- per-env fault_ keys plus the
        # explicit fault_injection flag (values reflect the last reset state).
        per_env_fault = _read_per_env_fault(raw_env)
        seg_arrays = {k: v for k, v in data.items() if isinstance(v, np.ndarray)}
        seg_arrays.update(per_env_fault)
        seg_arrays["fault_injection"] = np.array(bool(per_env_fault))
        write_eval_npz(output_dir, level, seg_arrays)
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
