# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free tests for the state_dependent_std toggle on ActorCriticEncoder.

Phase 2 of the attitude_only campaign (state-conditioned action std, framed as a
falsification of the "richer action representation helps" hypothesis). The toggle
adds a state-conditioned log_std head: the actor emits 2*num_actions (mean + log_std)
when ON, while keeping actuation authority unchanged (mean still drives the same
[:, :2]/[:, 2:] actuator slices).

CRITICAL CONTRACT (verified against constraint_trpo.py FVP, base baseline-260608b-attitude-only):
- Toggle OFF (default) MUST be byte-identical to the Phase-1 baseline: the global
  `log_std` nn.Parameter is present and used; std is state-INDEPENDENT (same across
  states); the actor emits num_actions (8D) only.
- Toggle ON: actor emits 2*num_actions (16D), split into mean(8) + log_std(8); std is
  state-CONDITIONED (differs across distinct obs batches); mean is still 8D. The global
  `log_std` Parameter is STILL present (kept so the algorithm's post-TRPO clamp at
  constraint_trpo.py:488-491 operates on a live Parameter harmlessly, never AttributeErrors).

These tests construct the REAL ActorCriticEncoder with REAL rsl_rl MLP/EmpiricalNormalization
(forward passes are needed to check output shapes + per-state std), path-loaded via importlib
to bypass constrained_albc.__init__ (which pulls isaaclab.sim / carb). Mirrors the loader
idiom in tests/test_z_ablation.py.
"""

from __future__ import annotations

import importlib.util
import math
import sys
import types
from pathlib import Path

import pytest
import torch
from tensordict import TensorDict

# ---------------------------------------------------------------------------
# Path-load the attitude_only encoder modules with REAL rsl_rl (no Isaac Sim).
# Unlike test_z_ablation.py we do NOT mock MLP/EmpiricalNormalization: these tests
# run forward passes, so the real networks are required.
# ---------------------------------------------------------------------------
_ENC_DIR = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc"
    / "envs"
    / "attitude_only"
    / "encoder"
)
_ENC_PKG = "constrained_albc.envs.attitude_only.encoder"

for _pkg in [
    "constrained_albc",
    "constrained_albc.envs",
    "constrained_albc.envs.attitude_only",
    _ENC_PKG,
]:
    sys.modules.setdefault(_pkg, types.ModuleType(_pkg))


def _load(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(f"{_ENC_PKG}.{name}", _ENC_DIR / filename)
    assert spec is not None and spec.loader is not None, f"cannot load {filename}"
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = _ENC_PKG
    sys.modules[f"{_ENC_PKG}.{name}"] = mod
    spec.loader.exec_module(mod)
    return mod


_load("_policy_base", "_policy_base.py")
_load("_z_ablation", "_z_ablation.py")
_ace_mod = _load("actor_critic_encoder", "actor_critic_encoder.py")
ActorCriticEncoder = _ace_mod.ActorCriticEncoder

# ---------------------------------------------------------------------------
# Fixtures: minimal real obs + policy builder
# ---------------------------------------------------------------------------
_POLICY_DIM = 69
_PRIV_DIM = 27
_NUM_ACTIONS = 8
_OBS_GROUPS = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
# Sigma clamp range reused from the agent cfg (min_std=0.05, max_std=2.0).
_MIN_STD = 0.05
_MAX_STD = 2.0


def _make_obs(seed: int, batch: int = 16) -> TensorDict:
    """A deterministic real TensorDict obs with the attitude_only dims."""
    g = torch.Generator().manual_seed(seed)
    return TensorDict(
        {
            "policy": torch.randn(batch, _POLICY_DIM, generator=g),
            "privileged": torch.randn(batch, _PRIV_DIM, generator=g),
        },
        batch_size=[batch],
    )


def _make_policy(state_dependent_std: bool) -> ActorCriticEncoder:
    obs = _make_obs(seed=0)
    torch.manual_seed(0)
    return ActorCriticEncoder(
        obs=obs,
        obs_groups=_OBS_GROUPS,
        num_actions=_NUM_ACTIONS,
        policy_obs_dim=_POLICY_DIM,
        privileged_dim=_PRIV_DIM,
        encoder_latent_dim=9,
        critic_uses_z=True,
        encoder_output_norm=True,
        num_constraints=0,
        init_noise_std=0.7,
        min_std=_MIN_STD,
        max_std=_MAX_STD,
        state_dependent_std=state_dependent_std,
    )


# ---------------------------------------------------------------------------
# Toggle OFF (default): byte-identical to Phase-1 baseline
# ---------------------------------------------------------------------------


def test_default_is_state_independent_global_logstd():
    """Default (toggle off): global log_std Parameter present, 8D mean, state-INDEPENDENT std."""
    policy = _make_policy(state_dependent_std=False)

    # Global log_std nn.Parameter must still exist (the FVP/clamp contract).
    assert isinstance(policy.log_std, torch.nn.Parameter)
    assert policy.log_std.shape == (_NUM_ACTIONS,)

    # act_inference returns the deterministic 8D mean (no std channels).
    obs = _make_obs(seed=1)
    mean = policy.act_inference(obs)
    assert mean.shape[-1] == _NUM_ACTIONS

    # std must be IDENTICAL across two distinct obs batches (state-independent).
    obs_a, obs_b = _make_obs(seed=10), _make_obs(seed=20)
    policy.act(obs_a)
    std_a = policy.action_std.clone()
    policy.act(obs_b)
    std_b = policy.action_std.clone()
    assert torch.allclose(std_a[0], std_b[0]), "toggle-off std must be state-independent"
    # And it must equal exp(global log_std).
    assert torch.allclose(std_a[0], policy.log_std.exp(), atol=1e-6)


def test_default_actor_emits_num_actions():
    """Default: actor MLP output width is num_actions (8), not 2*num_actions."""
    policy = _make_policy(state_dependent_std=False)
    obs = _make_obs(seed=2)
    actor_out = policy.actor(policy._get_actor_obs(obs))
    assert actor_out.shape[-1] == _NUM_ACTIONS


# ---------------------------------------------------------------------------
# Toggle ON: state-conditioned std head
# ---------------------------------------------------------------------------


def test_toggle_on_actor_emits_double_width():
    """Toggle on: actor MLP emits 2*num_actions (mean8 + log_std8)."""
    policy = _make_policy(state_dependent_std=True)
    obs = _make_obs(seed=3)
    actor_out = policy.actor(policy._get_actor_obs(obs))
    assert actor_out.shape[-1] == 2 * _NUM_ACTIONS


def test_toggle_on_mean_still_num_actions():
    """Toggle on: the policy mean (action authority) is still 8D."""
    policy = _make_policy(state_dependent_std=True)
    obs = _make_obs(seed=4)
    mean = policy.act_inference(obs)
    assert mean.shape[-1] == _NUM_ACTIONS


def test_toggle_on_std_is_state_conditioned():
    """Toggle on: std DIFFERS across two distinct obs batches (state-conditioned)."""
    policy = _make_policy(state_dependent_std=True)
    obs_a, obs_b = _make_obs(seed=30), _make_obs(seed=40)
    policy.act(obs_a)
    std_a = policy.action_std.clone()
    policy.act(obs_b)
    std_b = policy.action_std.clone()
    assert std_a.shape[-1] == _NUM_ACTIONS
    assert not torch.allclose(std_a, std_b), "toggle-on std must be state-conditioned"


def test_toggle_on_std_clamped_to_range():
    """Toggle on: per-state std stays within [min_std, max_std] (in-policy clamp)."""
    policy = _make_policy(state_dependent_std=True)
    # Drive extreme obs to push the head toward the clamp boundaries.
    obs = _make_obs(seed=50)
    obs["policy"] = obs["policy"] * 50.0
    obs["privileged"] = obs["privileged"] * 50.0
    policy.act(obs)
    std = policy.action_std
    assert torch.all(std >= _MIN_STD - 1e-5), f"std below min: {std.min().item()}"
    assert torch.all(std <= _MAX_STD + 1e-5), f"std above max: {std.max().item()}"


def test_toggle_on_global_logstd_still_present():
    """Toggle on: the global log_std Parameter is STILL present so the algorithm's
    post-TRPO clamp (constraint_trpo.py:488-491 self.policy.log_std.data) never
    AttributeErrors. It is unused for action sampling but must remain a live Parameter."""
    policy = _make_policy(state_dependent_std=True)
    assert isinstance(policy.log_std, torch.nn.Parameter)
    assert policy.log_std.shape == (_NUM_ACTIONS,)
    # The clamp the algorithm runs must be a no-error no-op on this live Parameter.
    log_max = math.log(_MAX_STD)
    policy.log_std.data.clamp_(min=math.log(_MIN_STD), max=log_max)  # must not raise


# ---------------------------------------------------------------------------
# TRPO FVP integration: the global log_std is unused-but-present when ON.
# Regression for the GPU-smoke crash "One of the differentiated Tensors appears
# to not have been used in the graph" — ConstraintTRPO's autograd.grad over
# _policy_params must tolerate the unused global log_std (allow_unused + zero-fill).
# This reproduces the exact grad pattern sim-free (no ConstraintTRPO, no Isaac Sim).
# ---------------------------------------------------------------------------


def _gaussian_kl(mu, sigma, old_mu, old_sigma):
    """Mean KL(old || new) for a diagonal Gaussian (mirrors ConstraintTRPO._gaussian_kl)."""
    kl = (
        torch.log((sigma / old_sigma).clamp(min=1e-5))
        + (old_sigma.pow(2) + (old_mu - mu).pow(2)) / (2.0 * sigma.pow(2))
        - 0.5
    )
    return kl.sum(dim=-1).mean()


def _policy_params(policy):
    """The TRPO param set: all named params except critic/cost_critic (mirrors :160-182)."""
    value_prefixes = ("critic.", "cost_critic.", "value_backbone.", "reward_head.", "cost_head.")
    return [p for n, p in policy.named_parameters() if not any(n.startswith(v) for v in value_prefixes)]


def test_fvp_grad_tolerates_unused_global_logstd_when_on():
    """Toggle ON: the global log_std is in _policy_params but does NOT feed the KL
    (the per-state head supplies std). The FVP's strict autograd.grad would raise
    'differentiated Tensor not used'. The fix is allow_unused=True + zero-fill, which
    yields an EXACT zero Fisher block for the unused Parameter. Assert: (1) strict grad
    raises (documents the bug), (2) allow_unused grad succeeds with a None for log_std."""
    policy = _make_policy(state_dependent_std=True)
    params = _policy_params(policy)
    # log_std must be one of the policy params (rides in the TRPO set).
    assert any(p is policy.log_std for p in params)

    obs = _make_obs(seed=60)
    policy.act(obs)
    old_mu = policy.action_mean.detach()
    old_sigma = policy.action_std.detach()
    # Re-run act to build a fresh grad-enabled graph (act() sampled above).
    policy.act(obs)
    kl = _gaussian_kl(policy.action_mean, policy.action_std, old_mu, old_sigma)

    # (1) strict grad (the pre-fix behavior) raises because log_std is unused.
    with pytest.raises(RuntimeError, match="not have been used"):
        torch.autograd.grad(kl, params, create_graph=True, allow_unused=False)

    # (2) the fix: allow_unused=True returns None for the unused log_std; zero-fill is exact.
    grads = torch.autograd.grad(kl, params, create_graph=True, allow_unused=True)
    logstd_idx = next(i for i, p in enumerate(params) if p is policy.log_std)
    assert grads[logstd_idx] is None, "global log_std must be unused (None grad) when toggle ON"
    # The actor head weights (which carry the per-state log_std) MUST have a real grad.
    assert any(g is not None for i, g in enumerate(grads) if i != logstd_idx)


def test_fvp_grad_uses_global_logstd_when_off():
    """Toggle OFF (baseline): the global log_std FEEDS the KL, so its grad is NOT None.
    Proves the allow_unused change is a no-op for the byte-identical baseline path."""
    policy = _make_policy(state_dependent_std=False)
    params = _policy_params(policy)
    obs = _make_obs(seed=61)
    policy.act(obs)
    old_mu = policy.action_mean.detach()
    old_sigma = policy.action_std.detach()
    policy.act(obs)
    kl = _gaussian_kl(policy.action_mean, policy.action_std, old_mu, old_sigma)

    # Strict grad must SUCCEED off-toggle (log_std is used) -> the original code path is intact.
    grads = torch.autograd.grad(kl, params, create_graph=True, allow_unused=False)
    logstd_idx = next(i for i, p in enumerate(params) if p is policy.log_std)
    assert grads[logstd_idx] is not None, "global log_std must be USED (real grad) when toggle OFF"
