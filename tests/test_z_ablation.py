# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Unit tests for ActorCriticEncoder z-ablation toggle (no Isaac Sim required).

The ablation branch lives in _encode(). Instantiating the full ActorCriticEncoder
pulls in rsl_rl networks + a TensorDict obs + obs_groups, which is heavy for a unit
test. Instead we test the ablation arithmetic directly against the pure helper.

This pins: zero -> all zeros same shape/device/dtype; mean -> cached value expanded;
None -> identity passthrough; invalid mode and mean-without-nominal -> ValueError.

Loaded via importlib to bypass constrained_albc.__init__ (which pulls in
isaaclab.sim). _z_ablation.py only needs torch.
"""

import importlib.util
import sys
from pathlib import Path

import pytest
import torch

# ---------------------------------------------------------------------------
# Load _z_ablation.py directly without triggering constrained_albc.__init__
# ---------------------------------------------------------------------------
_MODULE_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc"
    / "envs"
    / "main"
    / "encoder"
    / "_z_ablation.py"
)
_spec = importlib.util.spec_from_file_location("_z_ablation", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_MODULE_PATH}"
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_z_ablation"] = _mod
_spec.loader.exec_module(_mod)

apply_z_ablation = _mod.apply_z_ablation
validate_ablation_mode = _mod.validate_ablation_mode


def test_ablation_none_is_identity():
    z = torch.randn(4, 9)
    out = apply_z_ablation(z, mode=None, cached=None)
    assert torch.equal(out, z)


def test_ablation_zero_returns_zeros():
    z = torch.randn(4, 9)
    out = apply_z_ablation(z, mode="zero", cached=None)
    assert out.shape == z.shape
    assert out.dtype == z.dtype
    assert torch.count_nonzero(out) == 0


def test_ablation_mean_returns_cached_expanded():
    z = torch.randn(4, 9)
    cached = torch.arange(9, dtype=torch.float32).reshape(1, 9)
    out = apply_z_ablation(z, mode="mean", cached=cached)
    assert out.shape == z.shape
    for row in range(4):
        assert torch.equal(out[row], cached.squeeze(0))


def test_ablation_mean_without_cache_raises():
    z = torch.randn(4, 9)
    with pytest.raises(ValueError, match=r"mean.*(nominal|cache)"):
        apply_z_ablation(z, mode="mean", cached=None)


def test_validate_mode_rejects_unknown():
    with pytest.raises(ValueError, match="z_ablation"):
        validate_ablation_mode("garbage")


def test_validate_mode_accepts_known():
    for m in (None, "zero", "mean"):
        validate_ablation_mode(m)  # no raise
