# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""ConstraintTRPO parameter-group wiring (no Isaac Sim required).

Pins the critic_uses_z encoder-gradient contract: the value MSE backprops
through z into the encoder, and TRPO reads policy grads functionally via
``autograd.grad`` -- so unless Adam owns the encoder params, the critic-side
encoder gradient is computed and then applied by NO optimizer (the silent
failure fixed 2026-07-12). Asserts membership both ways and that one value
step actually moves encoder weights iff ``critic_uses_z``.
"""

# ---------------------------------------------------------------------------
# Load the encoder + algorithm modules directly via importlib, bypassing
# constrained_albc.__init__ (which imports albc_env -> isaaclab.sim, requiring
# a full Isaac Sim runtime). The whole chain only needs torch / rsl_rl /
# tensordict.
# ---------------------------------------------------------------------------
import importlib.util
import sys
import types
from pathlib import Path

import pytest
import torch
from tensordict import TensorDict

_CORE = Path(__file__).resolve().parents[1] / "constrained_albc" / "envs" / "_core"


def _load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


_pkg = types.ModuleType("_enc_pkg")
_pkg.__path__ = [str(_CORE / "encoder")]
sys.modules["_enc_pkg"] = _pkg
_load("_enc_pkg._z_ablation", _CORE / "encoder" / "_z_ablation.py")
_load("_enc_pkg._policy_base", _CORE / "encoder" / "_policy_base.py")
_ace = _load("_enc_pkg.actor_critic_encoder", _CORE / "encoder" / "actor_critic_encoder.py")
ActorCriticEncoder = _ace.ActorCriticEncoder
ConstraintTRPO = _load("_alg_constraint_trpo", _CORE / "algorithms" / "constraint_trpo.py").ConstraintTRPO


def _build(critic_uses_z: bool):
    obs = TensorDict(
        {"policy": torch.zeros(4, 69), "privileged": torch.zeros(4, 28)}, batch_size=[4]
    )
    obs_groups = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
    policy = ActorCriticEncoder(
        obs,
        obs_groups,
        num_actions=8,
        privileged_dim=28,
        critic_uses_z=critic_uses_z,
        num_constraints=10,
    )
    alg = ConstraintTRPO(
        policy, num_constraints=10, constraint_budgets=tuple([0.1] * 10), device="cpu"
    )
    return obs, policy, alg


@pytest.mark.parametrize("critic_uses_z", [False, True])
def test_encoder_in_value_optimizer_iff_critic_uses_z(critic_uses_z):
    _, policy, alg = _build(critic_uses_z)
    enc_params = [p for n, p in policy.named_parameters() if n.startswith("encoder")]
    assert enc_params

    opt_ids = {id(p) for g in alg.value_optimizer.param_groups for p in g["params"]}
    in_opt = [id(p) in opt_ids for p in enc_params]
    if critic_uses_z:
        assert all(in_opt), "critic-side encoder grads applied by NO optimizer (M1 regression)"
    else:
        assert not any(in_opt)

    # Encoder must stay in the TRPO policy vector in BOTH modes (decoupling
    # failed: actor->z path alone drops enc_grad -85%).
    trpo_ids = {id(p) for p in alg._policy_params}
    assert all(id(p) in trpo_ids for p in enc_params)


@pytest.mark.parametrize("critic_uses_z", [False, True])
def test_value_step_moves_encoder_iff_critic_uses_z(critic_uses_z):
    obs, policy, alg = _build(critic_uses_z)
    enc_params = [p for n, p in policy.named_parameters() if n.startswith("encoder")]

    before = torch.cat([p.detach().flatten().clone() for p in enc_params])
    loss = policy.evaluate(obs).pow(2).mean() + policy.evaluate_costs(obs).pow(2).mean()
    alg.value_optimizer.zero_grad()
    loss.backward()
    alg.value_optimizer.step()
    after = torch.cat([p.detach().flatten() for p in enc_params])

    assert (not torch.allclose(before, after)) == critic_uses_z
