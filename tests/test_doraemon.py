# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Smoke tests for the DORAEMON DR curriculum core (standalone, no Isaac Sim required).

DORAEMON is a curriculum tool with near-zero coupling to the research env (only
`isaaclab.utils.configclass` is mocked here). These tests pin its math so the
planned promotion to marinelab has a regression net:

    1. build_param_specs reads (lo, hi) from a DR cfg and sets nominal = midpoint
       (except for _NOMINAL_OVERRIDES).
    2. BetaDistribution preserves the nominal as its mean, samples within physical
       bounds, and has self-KL ~ 0.
    3. EpisodeBuffer behaves as a ring buffer (add / get_all / clear).
"""

import sys
import types
from pathlib import Path

import pytest
import torch

# ---------------------------------------------------------------------------
# Mock the single Isaac Sim dependency: isaaclab.utils.configclass is an
# identity decorator at runtime for these dataclasses, so a passthrough is faithful.
# ---------------------------------------------------------------------------
if "isaaclab" not in sys.modules:
    _isaaclab = types.ModuleType("isaaclab")
    _utils = types.ModuleType("isaaclab.utils")
    _utils.configclass = lambda cls: cls  # identity: @configclass just wraps a dataclass
    _isaaclab.utils = _utils
    sys.modules["isaaclab"] = _isaaclab
    sys.modules["isaaclab.utils"] = _utils

# Import doraemon.py directly by path (avoids importing the full env package,
# which would pull in Isaac Sim).
import importlib.util

_DORAEMON_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc"
    / "envs"
    / "constrained_full_albc"
    / "doraemon.py"
)
_spec = importlib.util.spec_from_file_location("doraemon", _DORAEMON_PATH)
doraemon = importlib.util.module_from_spec(_spec)
sys.modules["doraemon"] = doraemon
_spec.loader.exec_module(doraemon)

BetaDistribution = doraemon.BetaDistribution
EpisodeBuffer = doraemon.EpisodeBuffer
ParamSpec = doraemon.ParamSpec
build_param_specs = doraemon.build_param_specs

_CPU = torch.device("cpu")


# ---------------------------------------------------------------------------
# build_param_specs
# ---------------------------------------------------------------------------


class _FakeDRCfg:
    """Minimal stand-in exposing the DR fields build_param_specs reads via getattr."""

    payload_mass_range = (0.0, 2.0)
    added_mass_scale = (0.85, 1.15)
    linear_damping_scale = (0.5, 1.5)
    quadratic_damping_scale = (0.5, 1.5)
    water_density_range = (995.0, 1025.0)
    cog_offset_z = (-0.02, 0.02)
    cob_offset_z = (-0.02, 0.02)
    volume_scale = (0.9, 1.1)
    cob_offset_x = (-0.01, 0.01)
    cob_offset_y = (-0.01, 0.01)
    cog_offset_x = (-0.01, 0.01)
    cog_offset_y = (-0.01, 0.01)
    inertia_scale = (0.75, 1.3)
    body_mass_scale = (0.9, 1.1)
    payload_cog_offset_z = (-0.03, 0.0)
    ocean_current_strength_range = (0.0, 1.0)


def test_build_param_specs_reads_bounds_and_midpoint_nominal():
    specs = build_param_specs(_FakeDRCfg())
    assert len(specs) == doraemon.NDIMS
    by_name = {s.name: s for s in specs}

    # Bounds come straight from the cfg fields.
    assert by_name["payload_mass"].min_bound == 0.0
    assert by_name["payload_mass"].max_bound == 2.0
    # Nominal defaults to the midpoint...
    assert by_name["payload_mass"].nominal == pytest.approx(1.0)
    # ...except where overridden (ocean current starts at zero).
    assert by_name["ocean_current_strength"].nominal == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# BetaDistribution
# ---------------------------------------------------------------------------


def _make_dist(nominal=0.5, lo=0.0, hi=1.0):
    return BetaDistribution([ParamSpec("p", lo, hi, nominal)], _CPU)


def test_beta_samples_within_physical_bounds():
    dist = _make_dist(nominal=0.5, lo=-2.0, hi=3.0)
    xi, log_probs = dist.sample(256)
    assert xi.shape == (256, 1)
    assert log_probs.shape == (256,)
    assert torch.all(xi >= -2.0) and torch.all(xi <= 3.0)


def test_beta_self_kl_is_zero():
    dist = _make_dist(nominal=0.4)
    assert dist.kl_divergence(dist) == pytest.approx(0.0, abs=1e-6)


def test_beta_clone_is_independent():
    dist = _make_dist()
    clone = dist.clone()
    clone._a += 5.0
    assert not torch.allclose(dist._a, clone._a)  # mutating the clone must not touch the original


def test_beta_mean_preserves_nominal():
    # For a symmetric range with nominal=midpoint, the distribution mean (a/(a+b))
    # mapped back to physical space should equal the nominal.
    nominal, lo, hi = 0.7, 0.0, 1.0
    dist = _make_dist(nominal=nominal, lo=lo, hi=hi)
    stats = dist.get_stats()
    assert stats["mean/p"] == pytest.approx(nominal, abs=1e-3)


# ---------------------------------------------------------------------------
# EpisodeBuffer  (ring buffer invariant -- USER TO COMPLETE)
# ---------------------------------------------------------------------------


def test_episode_buffer_ring_behavior():
    """The buffer keeps at most `capacity` most-recent episodes (FIFO eviction).

    TODO(user): pick the invariant that matters most for the IS success-rate
    estimate downstream, and assert it. Candidates:
      - after adding > capacity episodes, get_all() returns exactly `capacity` rows
      - the retained rows are the *most recent* ones (oldest evicted first)
      - clear() empties the buffer
    Inspect EpisodeBuffer.add / get_all / clear signatures in doraemon.py first
    (the `add` signature takes xi, log_probs, returns, success-ish tensors --
    confirm the exact arg order before asserting).
    """
    pytest.skip("USER TODO: assert the ring-buffer invariant (see docstring)")
