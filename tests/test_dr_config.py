# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for DR-config helpers extracted from eval.py.

These require constrained_albc.envs.main.config to import. If that boots
Isaac Sim, this test module is skipped entirely (the extraction is structural-only).
"""

from __future__ import annotations

import os
import sys

import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)

dr_config = pytest.importorskip("dr_config")


def test_build_dr_config_none_is_nominal():
    """scale=0.0 -> all tuple fields collapsed to nominal single-point distribution."""
    cfg = dr_config.build_dr_config(0.0)
    assert cfg is not None
    # At scale=0 each tuple field must be a point (lo == hi == nominal).
    # Check a well-known nominal: payload_mass should be (0.0, 0.0).
    lo, hi = cfg.payload_mass_range
    assert lo == pytest.approx(0.0)
    assert hi == pytest.approx(0.0)


def test_build_dr_config_scale_one_matches_hard_dr():
    """scale=1.0 (no DORAEMON loaded) -> fields match the hard DomainRandomizationCfg."""
    from constrained_albc.envs.main.config import DomainRandomizationCfg

    hard = DomainRandomizationCfg()
    cfg = dr_config.build_dr_config(1.0)
    # payload_mass_range should match hard DR at scale=1.0
    assert cfg.payload_mass_range == pytest.approx(hard.payload_mass_range)


def test_collapse_dr_to_midpoint_idempotent_on_point():
    """A point-distribution (lo==hi) must be unchanged by collapse."""
    cfg = dr_config.build_dr_config(0.0)
    dr_config._collapse_dr_to_midpoint(cfg)
    lo, hi = cfg.payload_mass_range
    assert lo == pytest.approx(0.0)
    assert hi == pytest.approx(0.0)


def test_get_hard_dr_config_returns_independent_copy():
    """get_hard_dr_config must NOT hand out the shared _DORAEMON_FULL_DR object.

    Regression for the ood->hard leak: build_ood_dr_config does
    cfg = get_hard_dr_config(); setattr(cfg, "cob_offset_x", ood_bounds). If that
    cfg IS the global _DORAEMON_FULL_DR, the override silently corrupts the hard
    anchor every later caller reads. Two calls must return distinct objects, and
    mutating one must not touch the global.
    """
    from constrained_albc.envs.main.config import DomainRandomizationCfg

    # Simulate a loaded DORAEMON distribution (the leak only bites when it's set).
    saved = dr_config._DORAEMON_FULL_DR
    try:
        full = DomainRandomizationCfg()
        full.cob_offset_x = (-0.0181, 0.0181)  # the clean hard anchor
        dr_config._DORAEMON_FULL_DR = full

        a = dr_config.get_hard_dr_config()
        b = dr_config.get_hard_dr_config()
        assert a is not b, "two calls returned the same object (shared reference)"
        assert a is not full, "returned the global _DORAEMON_FULL_DR itself"

        # Mutating the returned cfg must leave the global untouched.
        a.cob_offset_x = (-0.0272, 0.0272)  # what build_ood_dr_config writes
        assert full.cob_offset_x == pytest.approx((-0.0181, 0.0181)), (
            "mutating get_hard_dr_config() result leaked into the global _DORAEMON_FULL_DR"
        )
    finally:
        dr_config._DORAEMON_FULL_DR = saved


def test_build_ood_dr_config_does_not_corrupt_hard_anchor():
    """build_ood_dr_config (ood level) must not mutate the shared hard anchor.

    End-to-end of the leak: after building the ood cfg, a freshly built hard cfg
    (build_dr_config(1.0)) must still see the clean DORAEMON cob/cog, NOT the
    1.5x-widened OOD magnitude bounds.
    """
    from constrained_albc.envs.main.config import DomainRandomizationCfg

    saved_full = dr_config._DORAEMON_FULL_DR
    saved_raw = dr_config._DORAEMON_RAW
    try:
        full = DomainRandomizationCfg()
        full.cob_offset_x = (-0.0181, 0.0181)
        dr_config._DORAEMON_FULL_DR = full
        # raw drives the OOD magnitude ceiling (mean + 2*std) * 1.5.
        dr_config._DORAEMON_RAW = {
            "cob_offset_x": (0.0, 0.0091), "cog_offset_x": (0.0, 0.0091),
            "cob_offset_y": (0.0, 0.0091), "cog_offset_y": (0.0, 0.0091),
            "cob_offset_z": (0.0, 0.0181), "cog_offset_z": (0.0, 0.0181),
        }

        ood = dr_config.build_ood_dr_config(dr_config._DORAEMON_RAW)
        # OOD cob_offset_x = (|0| + 2*0.0091) * 1.5 = 0.0273 -> the widened bound.
        assert ood.cob_offset_x[1] == pytest.approx(0.0273, abs=1e-3)

        # The clean hard anchor must be UNCHANGED by building the ood cfg.
        hard = dr_config.build_dr_config(1.0)
        assert hard.cob_offset_x[1] == pytest.approx(0.0181, abs=1e-3), (
            "hard cob_offset_x picked up the OOD-widened value -> shared-ref leak"
        )
    finally:
        dr_config._DORAEMON_FULL_DR = saved_full
        dr_config._DORAEMON_RAW = saved_raw


def test_payload_cog_offset_xy_u_range_sweeps_with_dr_level():
    """payload_cog_offset_xy_u_range is DORAEMON-managed during training.

    Eval must scale this range with DR level so none/soft/medium/hard match
    the training curriculum. Nominal=(0,0) (no XY offset), hard=(0,1) (full radius).
    """
    lo0, hi0 = dr_config.build_dr_config(0.0).payload_cog_offset_xy_u_range
    lo1, hi1 = dr_config.build_dr_config(1.0).payload_cog_offset_xy_u_range

    # Nominal (scale=0.0): collapse to (0,0) -- no XY offset
    assert lo0 == pytest.approx(0.0)
    assert hi0 == pytest.approx(0.0)

    # Hard (scale=1.0): should reach toward (0,1) -- full radius sweep
    assert lo1 == pytest.approx(0.0)
    assert hi1 > 0.9


def test_obs_noise_scale_range_sweeps_with_dr_level():
    """obs_noise_scale_range is DORAEMON-managed; eval must sweep it 0->1 by DR level."""
    from constrained_albc.analysis import dr_config
    lo0, hi0 = dr_config.build_dr_config(0.0).obs_noise_scale_range
    lo1, hi1 = dr_config.build_dr_config(1.0).obs_noise_scale_range
    assert (lo0, hi0) == (0.0, 0.0)      # nominal: no extra noise
    assert lo1 == 0.0 and hi1 > 0.9      # hard: sweeps toward full extra std
