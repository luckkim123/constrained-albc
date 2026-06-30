# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for DR-derived privileged-obs normalization bounds.

Isaac-free: the pure function derive_priv_obs_bounds_from_dr is imported
DIRECTLY from its module file (not via the package __init__, which would pull
torch/Isaac through utils/logging.py). DR/thruster/hydro inputs are lightweight
stand-in objects carrying only the attributes the function reads, so the test
never touches Isaac Sim or marinelab.

A separate test exercises the real HardDomainRandomizationCfg inheritance path
but is skipped automatically if importing that cfg boots Isaac Sim.

Spec: docs/plans/2026-06-30-dr-derived-priv-obs-normalization-bounds.md (section 3 table).
"""

from __future__ import annotations

import importlib.util
import os
import types

import pytest

# Import the pure module directly by file path -> Isaac-free.
_MODULE_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "constrained_albc",
    "envs",
    "main",
    "utils",
    "priv_obs_bounds.py",
)
_spec = importlib.util.spec_from_file_location("_priv_obs_bounds", _MODULE_PATH)
priv_obs_bounds = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(priv_obs_bounds)
derive = priv_obs_bounds.derive_priv_obs_bounds_from_dr


# ---------------------------------------------------------------------------
# Lightweight stand-in cfgs (only the attributes the function reads).
# Values mirror HardDomainRandomizationCfg + ALBCHydrodynamicsCfg + ALBCThrusterCfg.
# ---------------------------------------------------------------------------


def _hard_dr():
    """Stand-in HardDomainRandomizationCfg instance (Isaac-free)."""
    return types.SimpleNamespace(
        volume_scale=(0.75, 1.25),
        cog_offset_x=(-0.02, 0.02),
        cog_offset_y=(-0.02, 0.02),
        cog_offset_z=(-0.04, 0.04),
        cob_offset_x=(-0.02, 0.02),
        cob_offset_y=(-0.02, 0.02),
        cob_offset_z=(-0.04, 0.04),
        inertia_scale=(0.4, 2.0),
        linear_damping_scale=(0.4, 1.7),
        quadratic_damping_scale=(0.4, 1.7),
        body_mass_scale=(0.75, 1.25),
        added_mass_scale=(0.5, 1.5),
        payload_mass_range=(0.0, 3.0),
        payload_cog_offset_xy_radius=0.08,
        payload_cog_offset_z=(-0.05, 0.0),
        joint_stiffness_range=(30.0, 150.0),
        joint_damping_range=(0.3, 7.0),
        thrust_coefficient_scale=(0.7, 1.3),
        time_constant_scale=(0.7, 1.3),
        # inherited from base DomainRandomizationCfg (not redeclared in Hard):
        water_density_range=(995.0, 1025.0),
        ocean_current_strength_range=(0.0, 1.0),
    )


def _hydro():
    """Stand-in ALBCHydrodynamicsCfg (base physical values)."""
    return types.SimpleNamespace(
        volume=0.009,
        center_of_gravity=(0.0, 0.0, -0.05),
        center_of_buoyancy=(0.0, 0.0, 0.0),
        rigid_body_inertia=(0.0994, 0.0994, 0.0372),
        linear_damping=(2.0, 2.0, 1.5, 0.3, 0.3, 0.15),
        quadratic_damping=(39.0, 39.0, 15.0, 1.0, 1.0, 0.5),
        body_mass=9.18,
        added_mass=(8.0, 8.0, 1.0, 0.09, 0.09, 0.035),
    )


def _thruster():
    return types.SimpleNamespace(thrust_coefficient=40.0, time_constant_up=0.1)


_OCEAN_MAX = (0.5, 0.5, 0.25, 0.0, 0.0, 0.0)


def _derive():
    return derive(_hard_dr(), _OCEAN_MAX, _thruster(), hydro_cfg=_hydro())


# Spec section 3 derived column: [lower, upper] for all 27 dims.
_EXPECTED = [
    (0.00675, 0.01125),  # 0 volume
    (-0.02, 0.02),  # 1 CoG x
    (-0.02, 0.02),  # 2 CoG y
    (-0.09, -0.01),  # 3 CoG z (base -0.05)
    (-0.02, 0.02),  # 4 CoB x
    (-0.02, 0.02),  # 5 CoB y
    (-0.04, 0.04),  # 6 CoB z
    (0.03976, 0.1988),  # 7 Ixx
    (0.12, 0.51),  # 8 lin damp roll
    (0.4, 1.7),  # 9 quad damp roll
    (6.885, 11.475),  # 10 body mass
    (4.0, 12.0),  # 11 added mass surge
    (0.0, 3.0),  # 12 payload mass (MAJOR BUG fix)
    (-0.08, 0.08),  # 13 payload cog x (stale radius fix)
    (-0.08, 0.08),  # 14 payload cog y
    (-0.05, 0.0),  # 15 payload cog z
    (30.0, 150.0),  # 16 joint Kp
    (0.3, 7.0),  # 17 joint Kd
    (28.0, 52.0),  # 18 thrust coeff
    (0.07, 0.13),  # 19 time const up
    (995.0, 1025.0),  # 20 water density (direct absolute)
    (-0.5, 0.5),  # 21 ocean x
    (-0.5, 0.5),  # 22 ocean y
    (-0.25, 0.25),  # 23 ocean z
    (-1.0, 1.0),  # 24 measured u
    (-1.0, 1.0),  # 25 measured v
    (-1.0, 1.0),  # 26 measured w
]


def test_returns_27_dims():
    lower, upper = _derive()
    assert len(lower) == 27
    assert len(upper) == 27


@pytest.mark.parametrize("idx", range(27))
def test_each_dim_matches_spec(idx):
    lower, upper = _derive()
    exp_lo, exp_hi = _EXPECTED[idx]
    assert lower[idx] == pytest.approx(exp_lo), f"idx{idx} lower"
    assert upper[idx] == pytest.approx(exp_hi), f"idx{idx} upper"


def test_major_bug_payload_mass_overflow_fixed():
    """idx12: hardcoded was [-0.1, 2.2] (3 kg overflowed > 1). Now [0, 3]."""
    lower, upper = _derive()
    assert lower[12] == pytest.approx(0.0)
    assert upper[12] == pytest.approx(3.0)


def test_major_bug_payload_cog_radius_fixed():
    """idx13: hardcoded was +/-0.17 (stale 0.15 m radius). Now +/-0.08."""
    lower, upper = _derive()
    assert lower[13] == pytest.approx(-0.08)
    assert upper[13] == pytest.approx(0.08)
    # idx14 shares the same scalar radius.
    assert lower[14] == pytest.approx(-0.08)
    assert upper[14] == pytest.approx(0.08)


def test_cog_z_offset_to_negative_base():
    """idx3: offset onto base -0.05, NOT 0 -> [-0.09, -0.01]."""
    lower, upper = _derive()
    assert lower[3] == pytest.approx(-0.09)
    assert upper[3] == pytest.approx(-0.01)


def test_water_density_direct_not_scaled():
    """idx20: direct absolute range, must NOT be multiplied by base 998."""
    lower, upper = _derive()
    assert lower[20] == pytest.approx(995.0)
    assert upper[20] == pytest.approx(1025.0)


def test_measured_dims_fixed_pm1():
    """idx24-26: not DR-backed, fixed [-1, 1]."""
    lower, upper = _derive()
    assert lower[24:27] == [-1.0, -1.0, -1.0]
    assert upper[24:27] == [1.0, 1.0, 1.0]


def test_subset_assertion_raises_when_dr_out_of_range():
    """Mutating a DR range without re-deriving must trip the internal assertion.

    The function recomputes bounds FROM dr_cfg, so to simulate "bounds drifted
    from DR" we corrupt the derived list via the internal asserter directly:
    a lower above its upper, or a derived bound that no longer equals the DR
    range it claims to come from.
    """
    # A derived bound that does not match the DR range it derives from.
    lower = [0.0] * 27
    upper = [3.0] * 27
    lower[12] = 0.0
    upper[12] = 2.2  # claims DR [0, 3] but only spans to 2.2 -> mismatch
    with pytest.raises(AssertionError):
        priv_obs_bounds._assert_bounds_match_dr(
            lower,
            upper,
            scale_pairs={},
            offset_pairs={},
            direct_pairs={12: (0.0, 3.0)},
            radius_pairs={},
            symmetric_pairs={},
        )

    # lower > upper must also trip.
    bad_lo = [1.0] * 27
    bad_hi = [0.0] * 27
    with pytest.raises(AssertionError):
        priv_obs_bounds._assert_bounds_match_dr(
            bad_lo,
            bad_hi,
            scale_pairs={},
            offset_pairs={},
            direct_pairs={},
            radius_pairs={},
            symmetric_pairs={},
        )


def test_inherited_dr_fields_resolve_on_real_hard_cfg():
    """Real HardDomainRandomizationCfg: inherited water_density / ocean strength
    must resolve via getattr. Skipped if importing the cfg boots Isaac Sim."""
    try:
        from constrained_albc.envs.main.config import HardDomainRandomizationCfg
    except Exception as exc:  # pragma: no cover - environment dependent
        pytest.skip(f"cfg import requires Isaac Sim: {exc}")

    hard = HardDomainRandomizationCfg()
    # getattr must resolve inherited fields not redeclared in Hard.
    assert getattr(hard, "water_density_range") == pytest.approx((995.0, 1025.0))
    assert getattr(hard, "ocean_current_strength_range") == pytest.approx((0.0, 1.0))

    lower, upper = derive(hard, _OCEAN_MAX, _thruster(), hydro_cfg=_hydro())
    assert lower[20] == pytest.approx(995.0)
    assert upper[20] == pytest.approx(1025.0)
    assert upper[21] == pytest.approx(0.5)  # ocean x = max_velocity[0] * strength_hi(1.0)
