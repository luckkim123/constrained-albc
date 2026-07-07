# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free unit tests for the OOD DR-bound pure logic (GAP 1, change 2b).

`dr_config.py` cannot be imported without Isaac Sim (DomainRandomizationCfg pulls
carb via isaaclab.sim). So the OOD-bound math lives in `ood_logic.py`, a pure
sim-free module that takes/returns plain dicts/tuples -- the same seam pattern as
`_analyze.recompute_metrics`. `dr_config.build_ood_dr_config` is a thin
cfg-mutating wrapper around it (exercised by the user's GPU smoke, not here).
"""
from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
import ood_logic  # noqa: E402  (sim-free module under test)

# Synthetic DORAEMON raw: field -> (mean, std). Realistic offset magnitudes.
_RAW = {
    "cog_offset_x": (0.010, 0.005),   # ceiling = 0.010 + 2*0.005 = 0.020
    "cog_offset_y": (0.008, 0.004),   # ceiling = 0.016
    "cog_offset_z": (0.020, 0.010),   # ceiling = 0.040
    "cob_offset_x": (0.012, 0.006),   # ceiling = 0.024
    "cob_offset_y": (0.000, 0.005),   # ceiling = 0.010
    "cob_offset_z": (0.018, 0.011),   # ceiling = 0.040
    # a non-offset DORAEMON field that must NOT be treated as a magnitude axis
    "added_mass_scale": (1.4, 0.05),
}
# Fixed training ranges for held-out axes (from the hard DomainRandomizationCfg).
_HARD = {
    "thrust_coefficient_scale": (0.7, 1.3),
    "time_constant_scale": (0.7, 1.3),
}


def test_magnitude_axis_bound_is_ceiling_times_factor():
    bounds = ood_logic.compute_ood_bounds(_RAW, _HARD)
    # cog_offset_z ceiling = 0.020 + 2*0.010 = 0.040; *1.5 = 0.060.
    lo, hi = bounds["cog_offset_z"]
    assert hi == pytest.approx(0.040 * ood_logic.OOD_MAGNITUDE_FACTOR)
    # Offset axes are symmetric about 0: lo == -hi.
    assert lo == pytest.approx(-hi)


def test_all_six_offset_axes_present_and_factored():
    bounds = ood_logic.compute_ood_bounds(_RAW, _HARD)
    expected = {
        "cog_offset_x": 0.020, "cog_offset_y": 0.016, "cog_offset_z": 0.040,
        "cob_offset_x": 0.024, "cob_offset_y": 0.010, "cob_offset_z": 0.040,
    }
    for field, ceiling in expected.items():
        lo, hi = bounds[field]
        assert hi == pytest.approx(ceiling * ood_logic.OOD_MAGNITUDE_FACTOR), field
        assert lo == pytest.approx(-ceiling * ood_logic.OOD_MAGNITUDE_FACTOR), field


def test_held_out_axis_pushed_past_training_range():
    bounds = ood_logic.compute_ood_bounds(_RAW, _HARD)
    # thrust_coefficient_scale training range (0.7,1.3), center=1.0.
    # pushed center = 1.0 * 1.4 = 1.4; must be ABOVE the training upper bound 1.3.
    lo, hi = bounds["thrust_coefficient_scale"]
    center = (lo + hi) / 2.0
    assert center == pytest.approx(1.0 * ood_logic.OOD_HELD_OUT_PUSH)
    # Design (section 2b): "center at 1.4, keep a small spread" -> no value in the
    # OOD range falls inside the trained interior, so lo >= training_max.
    train_max = _HARD["thrust_coefficient_scale"][1]
    assert lo >= train_max, "OOD range must not re-enter the trained interior"
    # The spread is fully determined by existing values (no new magic constant):
    # half-width = pushed_center - training_max, so lo lands exactly at training_max.
    assert hi - lo == pytest.approx(2.0 * (center - train_max))
    assert lo == pytest.approx(train_max)


def test_time_constant_axis_also_pushed():
    bounds = ood_logic.compute_ood_bounds(_RAW, _HARD)
    lo, hi = bounds["time_constant_scale"]
    assert (lo + hi) / 2.0 == pytest.approx(1.0 * ood_logic.OOD_HELD_OUT_PUSH)
    assert lo >= _HARD["time_constant_scale"][1]


def test_non_offset_doraemon_field_not_in_bounds():
    # added_mass_scale is DORAEMON-managed but NOT a magnitude (offset) axis;
    # the OOD builder leaves it at the hard anchor, so it must not appear here.
    bounds = ood_logic.compute_ood_bounds(_RAW, _HARD)
    assert "added_mass_scale" not in bounds


def test_missing_doraemon_axis_is_skipped_not_invented():
    # If a magnitude axis is absent from raw, it must be omitted (documented
    # fallback: leave at hard anchor), NOT invented from a hardcoded value.
    partial = {"cog_offset_x": (0.01, 0.005)}
    bounds = ood_logic.compute_ood_bounds(partial, _HARD)
    assert "cog_offset_x" in bounds
    assert "cog_offset_y" not in bounds
    # held-out axes still derived from _HARD regardless.
    assert "thrust_coefficient_scale" in bounds


def test_empty_raw_loud_fails():
    # No DORAEMON magnitude data at all -> the design requires loud-fail
    # (do not silently produce an OOD config with no magnitude OOD).
    with pytest.raises(ValueError, match="no DORAEMON magnitude"):
        ood_logic.compute_ood_bounds({}, _HARD)


def test_constants_have_expected_design_values():
    assert ood_logic.OOD_HELD_OUT_PUSH == 1.4
    assert ood_logic.OOD_MAGNITUDE_FACTOR == 1.5
    assert ood_logic.OOD_CEILING_STD_K == 2.0
