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
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

# ---------------------------------------------------------------------------
# _MockModule: repo-standard stub (same idiom as test_tdc_controller.py)
# ---------------------------------------------------------------------------


class _MockModule(types.ModuleType):
    """Module mock that supports attribute access, calling, and string ops."""

    def __call__(self, *args, **kwargs):
        if args:
            return args[0]
        return self

    def __str__(self):
        return self.__name__

    def __format__(self, spec):
        return format(str(self), spec)

    def __getattr__(self, name):
        child = _MockModule(f"{self.__name__}.{name}")
        setattr(self, name, child)
        return child


# Stub rsl_rl so actor_critic_encoder.py and _policy_base.py can be path-loaded.
# MLP/EmpiricalNormalization are only referenced inside __init__ (never called by tests).
_rsl_rl_networks = _MockModule("rsl_rl.networks")
_rsl_rl_networks.MLP = _MockModule("rsl_rl.networks.MLP")
_rsl_rl_networks.EmpiricalNormalization = _MockModule("rsl_rl.networks.EmpiricalNormalization")
_rsl_rl_mod = _MockModule("rsl_rl")
_rsl_rl_mod.networks = _rsl_rl_networks
sys.modules.setdefault("rsl_rl", _rsl_rl_mod)
sys.modules.setdefault("rsl_rl.networks", _rsl_rl_networks)

# ---------------------------------------------------------------------------
# Load _z_ablation.py directly without triggering constrained_albc.__init__
# ---------------------------------------------------------------------------
_ENCODER_DIR = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc"
    / "envs"
    / "main"
    / "encoder"
)

_MODULE_PATH = _ENCODER_DIR / "_z_ablation.py"
_spec = importlib.util.spec_from_file_location("_z_ablation", _MODULE_PATH)
assert _spec is not None and _spec.loader is not None, f"cannot load {_MODULE_PATH}"
_mod = importlib.util.module_from_spec(_spec)
sys.modules["_z_ablation"] = _mod
_spec.loader.exec_module(_mod)

apply_z_ablation = _mod.apply_z_ablation
validate_ablation_mode = _mod.validate_ablation_mode

# ---------------------------------------------------------------------------
# Load ActorCriticEncoder via importlib direct-load (avoids constrained_albc.__init__)
# ---------------------------------------------------------------------------
_ENC_PKG = "constrained_albc.envs.main.encoder"

# Register package stubs so relative imports inside the encoder modules resolve.
for _pkg in ["constrained_albc", "constrained_albc.envs", "constrained_albc.envs.main", _ENC_PKG]:
    sys.modules.setdefault(_pkg, types.ModuleType(_pkg))

# Load _policy_base.py first (actor_critic_encoder.py imports `from ._policy_base import PolicyBase`).
_pb_spec = importlib.util.spec_from_file_location(
    f"{_ENC_PKG}._policy_base", _ENCODER_DIR / "_policy_base.py"
)
assert _pb_spec is not None and _pb_spec.loader is not None
_pb_mod = importlib.util.module_from_spec(_pb_spec)
_pb_mod.__package__ = _ENC_PKG
sys.modules[f"{_ENC_PKG}._policy_base"] = _pb_mod
_pb_spec.loader.exec_module(_pb_mod)

# Load _z_ablation under the encoder package name so `from ._z_ablation import ...` resolves.
sys.modules[f"{_ENC_PKG}._z_ablation"] = _mod

# Load actor_critic_encoder.py with correct package context.
_ace_spec = importlib.util.spec_from_file_location(
    f"{_ENC_PKG}.actor_critic_encoder", _ENCODER_DIR / "actor_critic_encoder.py"
)
assert _ace_spec is not None and _ace_spec.loader is not None
_ace_mod = importlib.util.module_from_spec(_ace_spec)
_ace_mod.__package__ = _ENC_PKG
sys.modules[f"{_ENC_PKG}.actor_critic_encoder"] = _ace_mod
_ace_spec.loader.exec_module(_ace_mod)

ActorCriticEncoder = _ace_mod.ActorCriticEncoder


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


# ---------------------------------------------------------------------------
# Setter tests: bind the REAL set_z_ablation method onto a stub (no full network)
# ---------------------------------------------------------------------------


def _stub_with_setter():
    stub = SimpleNamespace()
    stub._z_ablation = None
    stub._z_ablation_value = None
    stub.encoder_latent_dim = 9
    # fake _encode: ignores obs, returns a deterministic z (1,9)
    stub._encode = lambda obs: torch.arange(9, dtype=torch.float32).reshape(1, 9)
    stub.set_z_ablation = types.MethodType(ActorCriticEncoder.set_z_ablation, stub)
    return stub


def test_setter_none_clears_state():
    stub = _stub_with_setter()
    stub.set_z_ablation("zero")
    stub.set_z_ablation(None)
    assert stub._z_ablation is None
    assert stub._z_ablation_value is None


def test_setter_zero_sets_mode_no_cache():
    stub = _stub_with_setter()
    stub.set_z_ablation("zero")
    assert stub._z_ablation == "zero"
    assert stub._z_ablation_value is None


def test_setter_mean_builds_cache():
    stub = _stub_with_setter()
    stub.set_z_ablation("mean", nominal_obs={"dummy": True})
    assert stub._z_ablation == "mean"
    assert stub._z_ablation_value is not None
    assert stub._z_ablation_value.shape == (1, 9)
    assert torch.equal(
        stub._z_ablation_value.squeeze(0), torch.arange(9, dtype=torch.float32)
    )


def test_setter_mean_without_obs_raises():
    stub = _stub_with_setter()
    with pytest.raises(ValueError, match="mean.*nominal|nominal.*mean"):
        stub.set_z_ablation("mean", nominal_obs=None)


def test_setter_invalid_mode_raises():
    stub = _stub_with_setter()
    with pytest.raises(ValueError, match="z_ablation"):
        stub.set_z_ablation("garbage")
