# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""DR-config construction extracted from eval.py.

Reads DORAEMON TB ranges and interpolates DomainRandomizationCfg across DR
levels (none/soft/medium/hard). Sim-free in logic; importability depends on
whether DomainRandomizationCfg pulls Isaac Sim (Step 1 probe result: NO --
DomainRandomizationCfg transitively imports carb via isaaclab.sim, so this
module is structural-only and NOT directly importable by omx without sim).

Module-level mutable state
--------------------------
_DORAEMON_FULL_DR, _DETERMINISTIC_DR, _APPLY_EXTREME_OOD, _EXTREME_OOD_PHYSICS,
_EXTREME_OOD_PHYSICS_FLOATS are owned here. eval.py mutates them via direct
attribute assignment:
    import dr_config as _dr_config_module
    _dr_config_module._DORAEMON_FULL_DR = cfg
"""

from __future__ import annotations

import os

from constrained_albc.envs.main.config import (  # type: ignore[import-not-found]
    DomainRandomizationCfg,
    HardDomainRandomizationCfg,
)
from constrained_albc.envs.main.doraemon import (  # type: ignore[import-not-found]
    _NOMINAL_OVERRIDES,
    _PARAM_DEFS,
    build_param_specs,
)
from ood_logic import (  # type: ignore[import-not-found]  # sim-free OOD bound math
    _HELD_OUT_AXES,
    compute_ood_bounds,
)

# ---- Module-level mutable state (mutated by eval.py at CLI parse time) ----

# DORAEMON-learned distribution as the hard-DR anchor.
# _DORAEMON_FULL_DR: DR config (mean +/- 2*std clamped to PARAM_SPEC bounds).
# _DORAEMON_RAW: underlying mean/std per parameter, used by visualization.
_DORAEMON_FULL_DR: DomainRandomizationCfg | None = None
_DORAEMON_RAW: dict[str, tuple[float, float]] = {}

# Set True by --deterministic-dr (static mode) to collapse DR bounds inside apply_dr_config.
_DETERMINISTIC_DR: bool = False
# Set True by --extreme-ood (static mode) to overwrite DR with fixed OOD preset values.
_APPLY_EXTREME_OOD: bool = False

# ---- DR interpolation helpers ----

# Mapping from DORAEMON param names to DomainRandomizationCfg field names.
# Most share the same name except payload_mass and water_density.
_DORAEMON_TO_DR_FIELD: dict[str, str] = {
    "payload_mass": "payload_mass_range",
    "water_density": "water_density_range",
}

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


# ---- Extreme-OOD physics presets ----
# Selectable via --ood-preset {v1,v2} (static mode).
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


# ============================================================================
# DR-config functions (verbatim from eval.py)
# ============================================================================

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


def build_ood_dr_config(
    doraemon_raw: dict[str, tuple[float, float]] | None = None,
) -> DomainRandomizationCfg:
    """Build the DR config for the GAP-1 `ood` level (thin sim-touching wrapper).

    Starts from the hard-DR anchor (so all in-dist axes are at their trained max),
    then overrides the OOD axes with bounds from the sim-free `compute_ood_bounds`:
      - magnitude axes (cog/cob offsets): DORAEMON ceiling (mean+2*std) * 1.5,
        read from `doraemon_raw` (falls back to the module's _DORAEMON_RAW).
      - held-out axes (thruster): training range pushed past its max (no overlap).

    NO hardcoded absolute magnitude appears here -- magnitude ceilings are READ
    from the learned distribution; the only constants live in ood_logic as named
    DESIGN parameters (OOD_HELD_OUT_PUSH / OOD_MAGNITUDE_FACTOR / OOD_CEILING_STD_K).

    Not unit-tested in CI (constructs DomainRandomizationCfg -> needs Isaac Sim);
    exercised by the user's GPU smoke. The bound math is unit-tested via ood_logic.
    """
    raw = doraemon_raw if doraemon_raw is not None else _DORAEMON_RAW
    if not raw:
        raise RuntimeError(
            "build_ood_dr_config: no DORAEMON raw distribution available. The OOD "
            "level needs the run's learned mean/std (load_doraemon_dr must succeed) "
            "to derive magnitude-OOD ceilings. Pass --doraemon-dr (the default)."
        )

    # Hard anchor: DORAEMON-learned full DR if loaded, else static HardDR.
    cfg: DomainRandomizationCfg = get_hard_dr_config()

    # Held-out axes anchor on the FIXED training range from the hard config itself.
    hard_ranges: dict[str, tuple[float, float]] = {}
    for axis in _HELD_OUT_AXES:
        if hasattr(cfg, axis):
            lo, hi = getattr(cfg, axis)
            hard_ranges[axis] = (lo, hi)

    bounds = compute_ood_bounds(raw, hard_ranges)
    for field_name, (lo, hi) in bounds.items():
        if not hasattr(cfg, field_name):
            print(f"[WARN] build_ood_dr_config: DR has no field '{field_name}', skipping.")
            continue
        setattr(cfg, field_name, (lo, hi))
        print(f"  OOD DR: {field_name:30s} -> [{lo:.4f}, {hi:.4f}]")

    cfg.enable = True
    return cfg
