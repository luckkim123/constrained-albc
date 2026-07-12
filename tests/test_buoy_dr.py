# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Buoy-specific volume/mass DR wiring guards (union p_t layout, 2026-07-12).

Two code paths, exercised independently:
  (a) Volume: _randomize_hydro_model takes a ``volume_key`` param; the buoy
      call passes "buoy_volume_scale" so its volume decorrelates from the
      main body's "volume_scale". Exercised on the real HydrodynamicsModel
      (marinelab.core, pure torch -- no Isaac Sim boot needed); skipped when
      marinelab cannot be resolved.
  (b) Mass: randomize_body_mass overwrites the buoy's mass row with
      buoy_body_mass_scale after the shared body_mass_scale broadcast.
      A minimal SimpleNamespace fake robot (get_masses/set_masses backed by
      a plain tensor) exercises the pure tensor-indexing logic; the real
      PhysX/Articulation wiring remains GPU-integration-only.

The collapse guard (buoy scale == main scale reproduces the correlated
baseline) is the toggle-off byte-identical property the consolidation relies on.
"""

from __future__ import annotations

import importlib.util as _importlib_util
import sys
import types
from pathlib import Path as _Path

import pytest
import torch

pytestmark = pytest.mark.filterwarnings("ignore::UserWarning")


def _skip_if_no_marinelab():
    """Skip unless the REAL marinelab.core is importable.

    Other test modules in this suite install lightweight ``_MockModule``
    stand-ins into ``sys.modules["marinelab.assets"]`` at import time
    (module-level, no teardown), which leaks across the whole pytest session
    once collected. Evict any non-genuine marinelab* submodules first so this
    test always resolves the real package (or cleanly skips), independent of
    test execution order.
    """
    for name in list(sys.modules):
        if name == "marinelab" or name.startswith("marinelab."):
            mod = sys.modules[name]
            if not getattr(mod, "__file__", None):
                del sys.modules[name]
    pytest.importorskip("marinelab.core", reason="marinelab requires Isaac Sim to import")


def _make_model(cfg_cls):
    marinelab_core = pytest.importorskip("marinelab.core", reason="marinelab requires Isaac Sim to import")
    HydrodynamicsModel = marinelab_core.HydrodynamicsModel
    cfg = cfg_cls()
    model = HydrodynamicsModel(num_envs=8, device="cpu", cfg=cfg)
    return model, cfg


def _load_events_standalone():
    """Load events.py directly via importlib, bypassing constrained_albc.envs.main
    .__init__ (which eagerly imports albc_env, unavailable without Isaac Sim).
    events.py's own top-level imports are only logging/typing/torch (marinelab/
    albc_env are TYPE_CHECKING-only), so it loads standalone.
    """
    events_path = (
        _Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "mdp" / "events.py"
    )
    spec = _importlib_util.spec_from_file_location("_events_standalone", events_path)
    assert spec is not None and spec.loader is not None
    mod = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _make_dr_cfg(**overrides):
    """Minimal DomainRandomizationCfg stand-in exposing only the fields
    _randomize_hydro_model / randomize_body_mass read via ``dr.cfg``.
    """
    base = dict(
        added_mass_scale=(1.0, 1.0),
        linear_damping_scale=(1.0, 1.0),
        quadratic_damping_scale=(1.0, 1.0),
        yaw_damping_scale=(1.0, 1.0),
        volume_scale=(1.0, 1.0),
        buoy_volume_scale=(1.0, 1.0),
        water_density_range=(998.0, 998.0),
        cob_offset_x=(0.0, 0.0),
        cob_offset_y=(0.0, 0.0),
        cob_offset_z=(0.0, 0.0),
        cog_offset_x=(0.0, 0.0),
        cog_offset_y=(0.0, 0.0),
        cog_offset_z=(0.0, 0.0),
        inertia_scale=(1.0, 1.0),
        body_mass_scale=(1.0, 1.0),
        buoy_body_mass_scale=(1.0, 1.0),
    )
    base.update(overrides)
    return types.SimpleNamespace(**base)


# ---------------------------------------------------------------------------
# (a) Volume: volume_key wiring on the real HydrodynamicsModel
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "main_s,buoy_s",
    [
        (1.05, 1.05),  # collapse-onto-main: equal scales reproduce the correlated baseline
        (0.9, 1.1),  # decorrelation: buoy uses its own scale, main its own
    ],
)
def test_buoy_volume_key_wiring(main_s, buoy_s):
    """Main volume scales by volume_scale, buoy volume by buoy_volume_scale."""
    _skip_if_no_marinelab()
    from marinelab.assets.albc.albc import ALBCBuoyHydrodynamicsCfg, ALBCHydrodynamicsCfg

    events_mod = _load_events_standalone()
    DRSampler, _randomize_hydro_model = events_mod.DRSampler, events_mod._randomize_hydro_model

    main_model, _ = _make_model(ALBCHydrodynamicsCfg)
    buoy_model, _ = _make_model(ALBCBuoyHydrodynamicsCfg)
    env_ids = torch.arange(8)
    main_model.reset(env_ids)
    buoy_model.reset(env_ids)

    dr = DRSampler(cfg=main_model.cfg.__class__(), num_envs=8, device="cpu")
    dr.cfg = _make_dr_cfg()

    sampled = {
        "volume_scale": torch.full((8,), main_s),
        "buoy_volume_scale": torch.full((8,), buoy_s),
    }

    _randomize_hydro_model(main_model, env_ids, dr, sampled)
    _randomize_hydro_model(buoy_model, env_ids, dr, sampled, volume_key="buoy_volume_scale")

    base_main_volume = ALBCHydrodynamicsCfg().volume
    base_buoy_volume = ALBCBuoyHydrodynamicsCfg().volume
    assert torch.allclose(main_model.volume, torch.full((8,), base_main_volume * main_s), atol=1e-9)
    assert torch.allclose(buoy_model.volume, torch.full((8,), base_buoy_volume * buoy_s), atol=1e-9)


# ---------------------------------------------------------------------------
# (b) Mass: buoy-row overwrite in randomize_body_mass
# ---------------------------------------------------------------------------


class _FakePhysxView:
    """Minimal root_physx_view stand-in: get_masses/set_masses over a plain tensor."""

    def __init__(self, masses: torch.Tensor) -> None:
        self._masses = masses.clone()

    def get_masses(self) -> torch.Tensor:
        return self._masses.clone()

    def set_masses(self, masses: torch.Tensor, env_ids: torch.Tensor) -> None:
        self._masses[env_ids] = masses[env_ids]


def _make_fake_mass_env(default_mass_row: list[float], buoy_idx: int, body_idx: int = 0):
    """Minimal fake env for randomize_body_mass: only the attributes it reads."""
    num_envs = 8
    num_bodies = len(default_mass_row)
    default_mass = torch.tensor(default_mass_row).unsqueeze(0).expand(num_envs, num_bodies).clone()

    class _HydroStub:
        def __init__(self) -> None:
            self.body_mass = torch.zeros(num_envs)

    robot_data = types.SimpleNamespace(default_mass=default_mass)
    robot = types.SimpleNamespace(
        root_physx_view=_FakePhysxView(default_mass.clone()),
        data=robot_data,
    )
    env = types.SimpleNamespace(
        _robot=robot,
        _body_id=[body_idx],
        _buoy_body_id=[buoy_idx],
        _hydro=_HydroStub(),
        _buoy_hydro=_HydroStub(),
        device="cpu",
    )
    return env


@pytest.mark.parametrize(
    "main_s,buoy_s",
    [
        (1.05, 1.05),  # collapse-onto-main: equal scales reproduce the correlated baseline
        (0.9, 1.1),  # decorrelation: buoy row overwritten with its own scale
    ],
)
def test_buoy_mass_row_overwrite(main_s, buoy_s):
    """Main mass scales by body_mass_scale, buoy row by buoy_body_mass_scale."""
    events_mod = _load_events_standalone()
    DRSampler, randomize_body_mass = events_mod.DRSampler, events_mod.randomize_body_mass

    default_mass_row = [9.18, 0.93]  # [main (body_idx=0), buoy (buoy_idx=1)]
    env = _make_fake_mass_env(default_mass_row, buoy_idx=1, body_idx=0)
    env_ids = torch.arange(8)

    dr = DRSampler(cfg=_make_dr_cfg(), num_envs=8, device="cpu")

    sampled = {
        "body_mass_scale": torch.full((8,), main_s),
        "buoy_body_mass_scale": torch.full((8,), buoy_s),
    }

    randomize_body_mass(env, env_ids, dr, sampled)

    assert torch.allclose(env._hydro.body_mass, torch.full((8,), 9.18 * main_s), atol=1e-6)
    assert torch.allclose(env._buoy_hydro.body_mass, torch.full((8,), 0.93 * buoy_s), atol=1e-6)


# ---------------------------------------------------------------------------
# DORAEMON registration: buoy dims present in _PARAM_DEFS
# ---------------------------------------------------------------------------


def test_doraemon_param_defs_include_buoy_dims():
    """The 2 buoy dims are registered right after body_mass_scale (NDIMS grew by 2)."""
    doraemon_path = (
        _Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "doraemon.py"
    )
    source = doraemon_path.read_text()
    names = []
    for line in source.splitlines():
        stripped = line.strip()
        if stripped.startswith('("') and stripped.count('"') >= 4:
            names.append(stripped.split('"')[1])
    assert "buoy_volume_scale" in names
    assert "buoy_body_mass_scale" in names
    i = names.index("body_mass_scale")
    assert names[i + 1 : i + 3] == ["buoy_volume_scale", "buoy_body_mass_scale"]
