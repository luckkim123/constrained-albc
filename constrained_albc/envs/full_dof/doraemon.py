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
    CurriculumReplayer,
    DoraemonCfg,
    DoraemonScheduler,
    EpisodeBuffer,
    ParamSpec,
    build_param_specs,
)

__all__ = [
    "BetaDistribution",
    "CurriculumReplayer",
    "DoraemonCfg",
    "DoraemonScheduler",
    "EpisodeBuffer",
    "ParamSpec",
    "build_param_specs",
    "PARAM_SPECS",
    "NDIMS",
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
    # payload XY offset radius promoted to a DORAEMON curriculum as a NORMALIZED
    # quantile u in [0,1]. cfg field is the (0,1) tuple payload_cog_offset_xy_u_range;
    # events applies r = r_max * sqrt(u) (sqrt = area correction, kept in events).
    # Nominal=0 (_NOMINAL_OVERRIDES below) -> curriculum starts with no XY offset.
    ("payload_cog_offset_xy_u", "payload_cog_offset_xy_u_range", 0.0, 1.0),
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
    "payload_cog_offset_xy_u": 0.0,  # start with no XY offset, widen as policy masters it
}

# Default specs (base bounds) for callers without a DR cfg; matches pre-promotion PARAM_SPECS.
# Pre-change source used a PLAIN midpoint (does NOT apply _NOMINAL_OVERRIDES here) -- keep identical
# so the regression guard passes.
PARAM_SPECS: list[ParamSpec] = [
    ParamSpec(name, lo, hi, (lo + hi) / 2.0) for name, _f, lo, hi in _PARAM_DEFS
]
