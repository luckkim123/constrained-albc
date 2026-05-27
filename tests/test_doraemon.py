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

# doraemon.py is now a re-export shim over marinelab.algorithms.doraemon. Install a bare
# `marinelab` package (real __path__, so marinelab/__init__.py -- which pulls Isaac Sim --
# never runs) before loading the shim, mirroring the package-shim pattern used by
# marinelab's own conftest.
_MARINELAB_ROOT = Path("/workspace/marinelab/marinelab")
if "marinelab" not in sys.modules:
    _marinelab = types.ModuleType("marinelab")
    _marinelab.__path__ = [str(_MARINELAB_ROOT)]
    sys.modules["marinelab"] = _marinelab
    _ml_algorithms = types.ModuleType("marinelab.algorithms")
    _ml_algorithms.__path__ = [str(_MARINELAB_ROOT / "algorithms")]
    sys.modules["marinelab.algorithms"] = _ml_algorithms

# Import doraemon.py directly by path (avoids importing the full env package,
# which would pull in Isaac Sim).
import importlib.util

_DORAEMON_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc"
    / "envs"
    / "main"
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
    specs = build_param_specs(_FakeDRCfg(), doraemon._PARAM_DEFS, doraemon._NOMINAL_OVERRIDES)
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


def _make_buffer(capacity, ndims=1):
    return EpisodeBuffer(capacity=capacity, ndims=ndims, device=torch.device("cpu"))


def _add_n(buf, start, n, ndims=1):
    """Add n episodes whose returns are start, start+1, ... (so we can track identity)."""
    vals = torch.arange(start, start + n, dtype=torch.float32)
    xi = vals.unsqueeze(-1).repeat(1, ndims)
    return buf.add(xi, returns=vals, success=torch.zeros(n), log_probs=torch.zeros(n))


def test_episode_buffer_caps_at_capacity():
    """get_all() never returns more than `capacity` rows (the IS estimate window)."""
    buf = _make_buffer(capacity=3)
    _add_n(buf, 0, 10)
    _, returns, _, _ = buf.get_all()
    assert returns.shape[0] == 3


def test_episode_buffer_exact_fill_preserved():
    """Filling exactly to capacity keeps all rows, in order."""
    buf = _make_buffer(capacity=4)
    _add_n(buf, 10, 4)  # returns 10,11,12,13
    _, returns, _, _ = buf.get_all()
    assert torch.equal(returns, torch.tensor([10.0, 11.0, 12.0, 13.0]))


def test_episode_buffer_evicts_oldest_on_wrap():
    """After overflow, only the most-recent `capacity` episodes survive (FIFO)."""
    buf = _make_buffer(capacity=3)
    _add_n(buf, 0, 3)   # fill: 0,1,2
    _add_n(buf, 3, 2)   # overflow by 2: writes 3,4 over slots 0,1 -> retained {2,3,4}
    _, returns, _, _ = buf.get_all()
    assert set(returns.tolist()) == {2.0, 3.0, 4.0}  # oldest (0,1) evicted
    assert 0.0 not in returns.tolist() and 1.0 not in returns.tolist()


def test_episode_buffer_clear_empties():
    buf = _make_buffer(capacity=3)
    _add_n(buf, 0, 3)
    buf.clear()
    _, returns, _, _ = buf.get_all()
    assert returns.shape[0] == 0


def test_episode_buffer_single_add_over_capacity_keeps_tail():
    """A single batch larger than capacity keeps only its most-recent rows."""
    buf = _make_buffer(capacity=3)
    _add_n(buf, 0, 5)  # one batch of 5 into capacity-3 buffer
    _, returns, _, _ = buf.get_all()
    assert returns.shape[0] == 3
    assert set(returns.tolist()) == {2.0, 3.0, 4.0}  # tail kept, head dropped


# ---------------------------------------------------------------------------
# Per-axis success floor (SUCCESS_AXIS_* defs + the env's success computation)
# ---------------------------------------------------------------------------


def test_success_axis_defs_shape_and_roll_separated():
    """The ALBC per-axis defs separate roll from pitch and stay 4-channel."""
    assert doraemon.SUCCESS_AXIS_LABELS == ["roll", "pitch", "lin_vel", "yaw_vel"]
    assert len(doraemon.SUCCESS_AXIS_ERR_THRESHOLDS) == 4
    assert len(doraemon.SUCCESS_AXIS_ALPHA) == 4
    # roll is separated from pitch (the whole point) and has a (slightly) looser error budget
    # than pitch because roll is the weak axis.
    roll_thr = dict(doraemon.SUCCESS_AXIS_DEFS)["roll"]
    pitch_thr = dict(doraemon.SUCCESS_AXIS_DEFS)["pitch"]
    assert roll_thr >= pitch_thr > 0.0
    # alpha is the uniform 0.5 floor
    assert all(a == 0.5 for a in doraemon.SUCCESS_AXIS_ALPHA)


def test_per_axis_success_computation_low_error_is_success():
    """Replicates the env's _log_and_reset_rewards per-axis success: mean-abs-err <= threshold.

    Direction check: LOW error -> success=1 (opposite sense from the global return>=thr). A roll
    episode with error above its threshold fails roll even if every other axis passes.
    """
    thr = torch.tensor(doraemon.SUCCESS_AXIS_ERR_THRESHOLDS)  # [roll, pitch, lin_vel, yaw]
    # episode A: all axes well within threshold -> all success
    mean_err_a = thr * 0.5
    succ_a = (mean_err_a <= thr).float()
    assert succ_a.tolist() == [1.0, 1.0, 1.0, 1.0]
    # episode B: roll error 2x over threshold, others fine -> only roll fails
    mean_err_b = thr.clone()
    mean_err_b[0] = thr[0] * 2.0
    succ_b = (mean_err_b <= thr).float()
    assert succ_b.tolist() == [0.0, 1.0, 1.0, 1.0]


# NOTE: engine instantiation with per_axis_alpha (A=4 switch, set_axis_labels) is covered by
# marinelab/tests/test_doraemon.py, which applies a dataclass-capable configclass shim. This
# albc test module's configclass mock is a plain identity passthrough (DoraemonCfg has no
# generated __init__), so the engine-instantiation assertion lives there, not here. Here we pin
# only the ALBC-owned shim defs + the success-computation direction.
