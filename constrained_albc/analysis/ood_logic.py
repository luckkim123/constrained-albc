# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pure (sim-free) OOD DR-bound logic for the `--ood` eval level (GAP 1, 2b).

Split out of dr_config.py so it is importable WITHOUT Isaac Sim (dr_config pulls
DomainRandomizationCfg -> carb). Operates on plain dicts/tuples only, mirroring
the `_analyze.recompute_metrics` sim-free seam. dr_config.build_ood_dr_config is
the thin cfg-mutating wrapper that consumes compute_ood_bounds().

OOD definition (user-agreed, see docs/plans/2026-06-06-ood-eval-design.md):
  - magnitude OOD (cog/cob offsets, DORAEMON-managed): push BEYOND the achieved
    DORAEMON ceiling = mean + 2*std, by OOD_MAGNITUDE_FACTOR.
  - held-out OOD (thruster axes, NOT DORAEMON-managed -- fixed training range):
    push the training-range CENTER past the training max by OOD_HELD_OUT_PUSH,
    preserving the training half-width as the OOD spread.

The three multipliers below are the ONLY tunable constants and are DESIGN
parameters (not workspace-specific physics values). No hardcoded absolute
magnitude appears here -- magnitude ceilings are READ from `doraemon_raw`.
"""
from __future__ import annotations

# ---- Design constants (the only tunables; see design doc section 1) ----
# Held-out (thruster) axes: multiply the training-range center to push past it.
OOD_HELD_OUT_PUSH: float = 1.4
# Magnitude (cog/cob offset) axes: multiply the DORAEMON ceiling.
OOD_MAGNITUDE_FACTOR: float = 1.5
# DORAEMON ceiling = mean + OOD_CEILING_STD_K * std (matches load_doraemon_dr's
# mean +/- 2*std hard-DR anchor).
OOD_CEILING_STD_K: float = 2.0

# Magnitude OOD axes: symmetric offsets DORAEMON curriculum-widens during training.
# These are read from the learned distribution (ceiling = mean + k*std).
_MAGNITUDE_AXES: tuple[str, ...] = (
    "cog_offset_x", "cog_offset_y", "cog_offset_z",
    "cob_offset_x", "cob_offset_y", "cob_offset_z",
)
# Held-out OOD axes: thruster params randomized at a FIXED range during training
# (NOT DORAEMON-managed), so there is no learned ceiling -- anchor on the fixed
# training range and push the center past it.
_HELD_OUT_AXES: tuple[str, ...] = (
    "thrust_coefficient_scale",
    "time_constant_scale",
)


def compute_ood_bounds(
    doraemon_raw: dict[str, tuple[float, float]],
    hard_ranges: dict[str, tuple[float, float]],
) -> dict[str, tuple[float, float]]:
    """Compute OOD DR (lo, hi) bounds for the `ood` level. Pure: no sim, no cfg.

    Args:
        doraemon_raw: field -> (mean, std) from load_doraemon_dr's raw return.
            Only the magnitude (cog/cob offset) axes present here are used.
        hard_ranges: field -> (lo, hi) fixed training ranges for the held-out
            (thruster) axes, read from HardDomainRandomizationCfg.

    Returns:
        field -> (lo, hi) for every OOD-overridden axis. Magnitude axes are
        symmetric about 0 (lo = -hi). Held-out axes are centered at
        center*OOD_HELD_OUT_PUSH; the spread is the LARGEST half-width that keeps
        the whole range past the training max (half = pushed_center - training_max,
        so lo sits exactly at the training max edge -- NOT the training half-width).

    Raises:
        ValueError: if no magnitude axis is present in doraemon_raw (loud-fail:
            an OOD config with no magnitude OOD would be silently degenerate).
    """
    bounds: dict[str, tuple[float, float]] = {}

    # ---- magnitude OOD: ceiling = mean + k*std, pushed by the magnitude factor ----
    n_magnitude = 0
    for axis in _MAGNITUDE_AXES:
        if axis not in doraemon_raw:
            # Documented fallback: axis absent from the learned distribution ->
            # leave at the hard anchor (omit here), never invent a value.
            continue
        mean, std = doraemon_raw[axis]
        ceiling = abs(mean) + OOD_CEILING_STD_K * abs(std)
        hi = ceiling * OOD_MAGNITUDE_FACTOR
        bounds[axis] = (-hi, hi)
        n_magnitude += 1

    if n_magnitude == 0:
        raise ValueError(
            "compute_ood_bounds: no DORAEMON magnitude axis found in doraemon_raw "
            f"(expected any of {_MAGNITUDE_AXES}). Cannot build a magnitude-OOD level."
        )

    # ---- held-out OOD: push the fixed training-range center past the max ----
    # Design 2b: "center the range at 1.4, keep a small spread". The whole OOD
    # range must sit past the training max (no overlap back into trained region),
    # so the spread is the LARGEST half-width that still keeps lo >= training_max:
    # half = pushed_center - training_max  ->  lo = training_max exactly at the edge.
    # This is fully determined by existing values (no new magic constant) and is
    # "small" (it shrinks toward 0 as the push approaches the training max).
    for axis in _HELD_OUT_AXES:
        if axis not in hard_ranges:
            continue
        lo_tr, hi_tr = hard_ranges[axis]
        center = (lo_tr + hi_tr) / 2.0
        pushed_center = center * OOD_HELD_OUT_PUSH
        half_width = max(pushed_center - hi_tr, 0.0)
        bounds[axis] = (pushed_center - half_width, pushed_center + half_width)

    return bounds
