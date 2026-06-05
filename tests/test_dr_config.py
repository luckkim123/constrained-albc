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
    """scale=1.0 (no DORAEMON loaded) -> fields match HardDomainRandomizationCfg."""
    from constrained_albc.envs.main.config import HardDomainRandomizationCfg

    hard = HardDomainRandomizationCfg()
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
