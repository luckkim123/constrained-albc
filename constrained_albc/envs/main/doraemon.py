# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""ALBC overlay for the DORAEMON DR curriculum.

The engine now lives in marinelab.algorithms.doraemon (robot-agnostic). This module keeps
ONLY the ALBC-specific parameter definitions and re-exports the engine, so existing
``from .doraemon import DoraemonCfg / DoraemonScheduler / build_param_specs`` imports keep
working. Callers inject ``_PARAM_DEFS`` / ``_NOMINAL_OVERRIDES`` into the engine.
"""

from __future__ import annotations

from marinelab.algorithms.doraemon import (
    BetaDistribution,
    DoraemonCfg,
    DoraemonScheduler,
    EpisodeBuffer,
    ParamSpec,
    build_param_specs,
)

__all__ = [
    "BetaDistribution",
    "DoraemonCfg",
    "DoraemonScheduler",
    "EpisodeBuffer",
    "ParamSpec",
    "build_param_specs",
    "PARAM_SPECS",
    "NDIMS",
    "SUCCESS_AXIS_DEFS",
    "SUCCESS_AXIS_LABELS",
    "SUCCESS_AXIS_ERR_THRESHOLDS",
    "SUCCESS_AXIS_ALPHA",
]

# --- ALBC-specific DR parameter definitions (the only research coupling) ---
# (doraemon_name, dr_config_field_name, default_lo, default_hi)
# Order matches BetaDistribution dimension indices.
_PARAM_DEFS: list[tuple[str, str, float, float]] = [
    ("payload_mass", "payload_mass_range", 0.0, 1.0),
    ("added_mass_scale", "added_mass_scale", 0.85, 1.15),
    ("linear_damping_scale", "linear_damping_scale", 0.5, 1.5),
    ("quadratic_damping_scale", "quadratic_damping_scale", 0.5, 1.5),
    ("water_density", "water_density_range", 995.0, 1025.0),
    ("cog_offset_z", "cog_offset_z", -0.02, 0.02),
    ("cob_offset_z", "cob_offset_z", -0.02, 0.02),
    ("volume_scale", "volume_scale", 0.9, 1.1),
    ("cob_offset_x", "cob_offset_x", -0.01, 0.01),
    ("cob_offset_y", "cob_offset_y", -0.01, 0.01),
    ("cog_offset_x", "cog_offset_x", -0.01, 0.01),
    ("cog_offset_y", "cog_offset_y", -0.01, 0.01),
    ("inertia_scale", "inertia_scale", 0.75, 1.3),
    ("body_mass_scale", "body_mass_scale", 0.9, 1.1),
    ("payload_cog_offset_z", "payload_cog_offset_z", -0.03, 0.0),
    # r13: ocean current strength managed by DORAEMON.
    # Nominal=0 (_NOMINAL_OVERRIDES below) so curriculum starts with no current
    # and expands to full range (up to cfg.ocean_current.max_velocity) as policy
    # learns simpler variants.
    ("ocean_current_strength", "ocean_current_strength_range", 0.0, 1.0),
]
NDIMS = len(_PARAM_DEFS)

# Per-parameter nominal overrides; defaults to midpoint of [lo, hi] when absent.
_NOMINAL_OVERRIDES: dict[str, float] = {
    "ocean_current_strength": 0.0,
}

# Default specs (base bounds) for callers without a DR cfg; matches pre-promotion PARAM_SPECS.
# Pre-change source used a PLAIN midpoint (does NOT apply _NOMINAL_OVERRIDES here) -- keep identical
# so the regression guard passes.
PARAM_SPECS: list[ParamSpec] = [
    ParamSpec(name, lo, hi, (lo + hi) / 2.0) for name, _f, lo, hi in _PARAM_DEFS
]

# --- ALBC-specific per-axis success-floor definitions (the second research coupling) ---
# Maps each control axis to its per-episode MEAN-ABS-ERROR threshold. An episode "succeeds" on
# an axis when its mean-abs tracking error over the episode is <= the threshold. These error
# thresholds are physical (rad / m/s / rad/s), calibrated from the baseline teacher run's
# TRAINING-time per-axis error (WandB qd49fd71, iter 4000+), NOT its eval steady-state error.
# Rationale (2026-05-27 diagnosis, docs/results/2026-05-27-per-axis-floor-recalibration.md):
# success is computed DURING TRAINING where the attitude command is sampled uniform over
# +/-30deg (att_cmd_rp_range, FIXED -- not a DORAEMON axis), so the teacher's roll error there is
# 2-4deg, NOT the 0.6deg seen in eval (eval tracks much smaller targets). The earlier eval-based
# 0.69deg threshold was ~8x too tight -> success stuck at 0 -> DORAEMON froze DR at nominal
# (mode=-3). roll/pitch fixed at 3deg per user intent ("tracking error each within ~3deg");
# lin_vel/yaw matched to training scale. Still INITIAL -- refine from logged success_rate/<axis>
# (target ~0.5 so the floor binds without freezing DR).
#
# (axis_label, mean_abs_error_threshold). roll separated from pitch so the strong rotational axis
# (pitch, training error 1-2deg) cannot mask the weak one (roll, 2-4deg, ~11x lower control
# authority); at the shared 3deg threshold roll binds first, which is the masking-fix intent.
# lin_vel stays a single 3D-Euclidean channel (the linear axes are already strong; spec requires
# only roll separated). These ALBC names live ONLY here -- the marinelab engine never sees them
# (it gets an opaque [K, A] success tensor + the label list via set_axis_labels()).
SUCCESS_AXIS_DEFS: list[tuple[str, float]] = [
    ("roll", 0.052),      # rad (~3.0 deg); teacher training roll err 2-4deg, user-specified
    ("pitch", 0.052),     # rad (~3.0 deg); teacher training pitch err 1-2deg, =roll so roll binds first
    ("lin_vel", 0.10),    # m/s (Euclidean norm of vx/vy/vz error); teacher training norm 0.07-0.09
    ("yaw_vel", 0.20),    # rad/s; teacher training yaw-rate err 0.16-0.20
]
SUCCESS_AXIS_LABELS: list[str] = [name for name, _thr in SUCCESS_AXIS_DEFS]
SUCCESS_AXIS_ERR_THRESHOLDS: list[float] = [thr for _name, thr in SUCCESS_AXIS_DEFS]
# Per-axis success-rate floor (fraction of episodes that must pass each axis). Uniform 0.5.
SUCCESS_AXIS_ALPHA: list[float] = [0.5] * len(SUCCESS_AXIS_DEFS)
