# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Identity guard for the B0c per-env max_thrust ceiling (campaign B0c).

Exercises the REAL ``ThrusterModel.compute_wrench`` rather than re-deriving its
arithmetic. The pre-B0c code path is still reachable: with
``enable_randomization=False`` the model keeps ``_max_thrust = None`` and takes
the original scalar ``clamp(-cfg.max_thrust, cfg.max_thrust)`` branch. So the
guard is a direct A/B of old path vs new path at the identity setting.

This matters because a NULL B0c verdict is only interpretable if we know the
band was actually wired in. "The band did nothing" and "the band was never
applied" are different answers.

Loaded standalone via importlib so it does not need the Omniverse runtime --
unlike ``tests/test_dr_config.py``, which skips wholesale without a booted Kit
app. ``thruster.py`` needs torch plus a runtime ``from marinelab.assets import
ThrusterCfg``; that name is used only as an annotation (the module has
``from __future__ import annotations``, so it is never evaluated), which is why
a bare stub is sufficient and does not fake any physics. The cfg the test
actually passes is a real duck-typed object.
"""

from __future__ import annotations

import importlib.util as _importlib_util
import sys
import types
from pathlib import Path

import pytest
import torch

THRUSTER_PY = Path("/workspace/marinelab/marinelab/core/thruster.py")


def _load_thruster_module():
    if not THRUSTER_PY.is_file():
        pytest.skip(f"marinelab thruster source not found at {THRUSTER_PY}")

    # Stub ONLY the annotation-carrying import. Do not import the real
    # marinelab package: its __init__ pulls in tasks -> isaaclab, which needs
    # the sim runtime and would turn this into another skipped module.
    if "marinelab.assets" not in sys.modules:
        pkg = sys.modules.setdefault("marinelab", types.ModuleType("marinelab"))
        pkg.__path__ = []
        assets = types.ModuleType("marinelab.assets")
        assets.ThrusterCfg = type("ThrusterCfg", (), {})
        sys.modules["marinelab.assets"] = assets
        pkg.assets = assets

    spec = _importlib_util.spec_from_file_location("_b0c_thruster", THRUSTER_PY)
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _cfg():
    """Minimal duck-typed ThrusterCfg: the 6-thruster ALBC layout's shape."""
    return types.SimpleNamespace(
        num_thrusters=6,
        max_thrust=50.0,
        thrust_coefficient=40.0,
        time_constant_up=0.1,
        time_constant_down=0.05,
        allocation_matrix=tuple(
            tuple(float((i * 7 + j * 3) % 5 - 2) for j in range(6)) for i in range(6)
        ),
    )


def _wrench_for(model, state):
    model._state = state.clone()
    return model.compute_wrench()


def test_band_off_reproduces_the_prewb0c_scalar_clamp():
    """max_thrust_scale=(1.0, 1.0) must equal the fixed-ceiling model exactly."""
    thruster = _load_thruster_module()
    torch.manual_seed(0)
    n = 512
    # Commands past +-1 so the ceiling is genuinely the binding term for many envs.
    state = torch.randn(n, 6) * 2.0

    old = thruster.ThrusterModel(cfg=_cfg(), num_envs=n, device="cpu", enable_randomization=False)
    new = thruster.ThrusterModel(cfg=_cfg(), num_envs=n, device="cpu", enable_randomization=True)
    new.randomize_parameters(
        env_ids=torch.arange(n),
        thrust_coeff_scale=(1.0, 1.0),
        time_constant_scale=(1.0, 1.0),
        max_thrust_scale=(1.0, 1.0),
    )

    f_old, t_old = _wrench_for(old, state)
    f_new, t_new = _wrench_for(new, state)

    assert torch.equal(f_old, f_new), "forces diverge at the identity setting"
    assert torch.equal(t_old, t_new), "torques diverge at the identity setting"


def test_band_on_actually_changes_the_wrench():
    """Sanity: the axis must be live, or the identity test above proves nothing.

    A band that silently no-ops would pass the identity test AND produce a NULL
    B0c verdict -- indistinguishable from a real null. This is the other half.
    """
    thruster = _load_thruster_module()
    torch.manual_seed(0)
    n = 512
    state = torch.randn(n, 6) * 2.0

    ref = thruster.ThrusterModel(cfg=_cfg(), num_envs=n, device="cpu", enable_randomization=False)
    banded = thruster.ThrusterModel(cfg=_cfg(), num_envs=n, device="cpu", enable_randomization=True)
    banded.randomize_parameters(
        env_ids=torch.arange(n),
        thrust_coeff_scale=(1.0, 1.0),
        time_constant_scale=(1.0, 1.0),
        max_thrust_scale=(0.85, 1.15),
    )

    f_ref, _ = _wrench_for(ref, state)
    f_banded, _ = _wrench_for(banded, state)

    assert not torch.equal(f_ref, f_banded), "the +/-15% band produced no change -- axis is dead"

    # And the per-env ceilings must actually span the sourced band.
    ceilings = banded._max_thrust
    assert ceilings.min() >= 50.0 * 0.85 - 1e-6
    assert ceilings.max() <= 50.0 * 1.15 + 1e-6
    assert ceilings.std() > 0.0, "ceilings are constant -- randomisation did not vary per env"
