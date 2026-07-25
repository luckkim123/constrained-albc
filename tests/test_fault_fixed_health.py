# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Guard for the deterministic per-thruster health override (FTC-m4 eval instrument).

Two contracts, both on pure torch (no Isaac Sim):
  1. faults.sample_thruster_health returns the FIXED vector for every env when
     cfg.thruster_fixed_health is set, and falls through to the Bernoulli path
     (byte-identical) when it is None / absent (getattr-guarded).
  2. Through the REAL marinelab ThrusterModel.compute_wrench: health[m4]=0 zeroes
     thruster m4's contribution to the body wrench, so the delta between healthy
     and m4-dead equals exactly that one column's wrench. Mirrors
     tests/test_max_thrust_identity.py: "the mask did nothing" and "the mask was
     never applied" are different answers, so the bite must be shown, not assumed.

Run headless: python3 -m pytest tests/test_fault_fixed_health.py
"""
from __future__ import annotations

import importlib.util as _importlib_util
import os
import sys
import types
from pathlib import Path

import pytest
import torch

_MDP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "constrained_albc",
    "envs",
    "main",
    "mdp",
)
if _MDP not in sys.path:
    sys.path.insert(0, _MDP)
import faults  # noqa: E402

THRUSTER_PY = Path("/workspace/marinelab/marinelab/core/thruster.py")

# Live ALBC TAM (reordered), so the wrench check exercises the real geometry.
# From constrained_albc/envs/main/config.py _reorder_columns(_BASE, _ESC_ORDER).
_ALBC_TAM = (
    (0.0, 0.707, -0.707, 0.0, -0.707, 0.707),
    (0.0, 0.707, 0.707, 0.0, -0.707, -0.707),
    (1.0, 0.0, 0.0, 1.0, 0.0, 0.0),
    (0.0, 0.007, -0.007, 0.0, -0.007, 0.007),
    (0.145, -0.007, -0.007, -0.145, 0.007, 0.007),
    (0.0, -0.144, 0.144, 0.0, -0.144, 0.144),
)


class _FaultCfg:
    """Minimal stand-in for FaultInjectionCfg (no isaaclab configclass import)."""

    thruster_fail_prob = 0.10
    thruster_health_range = (0.0, 0.5)
    thruster_fixed_health = None


# ---- contract 1: fixed-health override at the sampler level -------------------


def test_fixed_health_returns_exact_vector_for_all_envs():
    cfg = _FaultCfg()
    cfg.thruster_fixed_health = (1.0, 1.0, 1.0, 1.0, 0.0, 1.0)  # m4 dead
    out = faults.sample_thruster_health(num_envs=1000, num_thrusters=6, cfg=cfg, device="cpu")
    assert out.shape == (1000, 6)
    expected = torch.tensor([1.0, 1.0, 1.0, 1.0, 0.0, 1.0])
    assert torch.equal(out, expected.unsqueeze(0).expand(1000, 6))


def test_none_fixed_health_falls_through_to_bernoulli_byte_identical():
    # prob 0 -> every thruster healthy (1.0); proves the Bernoulli path is untouched
    # by the override when the field is None.
    cfg = _FaultCfg()
    cfg.thruster_fixed_health = None
    cfg.thruster_fail_prob = 0.0
    out = faults.sample_thruster_health(num_envs=256, num_thrusters=6, cfg=cfg, device="cpu")
    assert torch.equal(out, torch.ones(256, 6))


def test_missing_field_is_getattr_guarded():
    # A cfg predating the field must still sample via Bernoulli, not crash.
    class _OldCfg:
        thruster_fail_prob = 0.0
        thruster_health_range = (0.0, 0.5)

    out = faults.sample_thruster_health(num_envs=8, num_thrusters=6, cfg=_OldCfg(), device="cpu")
    assert torch.equal(out, torch.ones(8, 6))


def test_wrong_length_fixed_health_raises():
    cfg = _FaultCfg()
    cfg.thruster_fixed_health = (1.0, 0.0)  # only 2 for 6 thrusters
    with pytest.raises(ValueError):
        faults.sample_thruster_health(num_envs=4, num_thrusters=6, cfg=cfg, device="cpu")


# ---- contract 2: the m4-dead health actually zeroes m4's wrench ---------------


def _load_thruster_module():
    if not THRUSTER_PY.is_file():
        pytest.skip(f"marinelab thruster source not found at {THRUSTER_PY}")
    if "marinelab.assets" not in sys.modules:
        pkg = sys.modules.setdefault("marinelab", types.ModuleType("marinelab"))
        pkg.__path__ = []
        assets = types.ModuleType("marinelab.assets")
        assets.ThrusterCfg = type("ThrusterCfg", (), {})
        sys.modules["marinelab.assets"] = assets
        pkg.assets = assets
    spec = _importlib_util.spec_from_file_location("_ftc_thruster", THRUSTER_PY)
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class _ThrusterCfg:
    num_thrusters = 6
    max_thrust = 50.0
    thrust_coefficient = 40.0
    time_constant_up = 0.1
    time_constant_down = 0.05
    allocation_matrix = _ALBC_TAM


def test_m4_dead_health_zeroes_m4_wrench_contribution():
    mod = _load_thruster_module()
    n = 4
    model = mod.ThrusterModel(_ThrusterCfg(), num_envs=n, device="cpu", enable_fault=True)
    # Drive every thruster to +1 so all six contribute a nonzero column.
    model._state = torch.ones(n, 6)

    fh, th = model.compute_wrench()
    healthy_wrench = torch.cat([fh, th], dim=-1).clone()

    # Kill m4 (index 4) in all envs.
    model.set_thruster_health(torch.arange(n), torch.tensor([[1.0, 1.0, 1.0, 1.0, 0.0, 1.0]]).expand(n, 6).clone())
    ff, tf = model.compute_wrench()
    faulted_wrench = torch.cat([ff, tf], dim=-1)

    # Expected delta = exactly m4's column * clamped thrust magnitude (state=1 -> 40 N < 50 clamp).
    tam = torch.tensor(_ALBC_TAM)
    m4_col_wrench = tam[:, 4] * 40.0
    delta = (healthy_wrench - faulted_wrench)[0]
    assert torch.allclose(delta, m4_col_wrench, atol=1e-4), (delta, m4_col_wrench)
    # And m4-dead must genuinely differ from healthy (the injector bites).
    assert not torch.allclose(healthy_wrench, faulted_wrench)
