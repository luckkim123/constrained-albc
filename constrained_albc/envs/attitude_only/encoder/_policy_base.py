# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared base class for constrained actor-critic policies (with or without encoder).

Handles: obs_groups parsing, dim validation, critic + cost_critic init,
log_std / Gaussian distribution, and shared API (evaluate, evaluate_costs, properties).
Subclasses implement: actor init, _get_actor_obs, _get_critic_obs, act, act_inference,
update_normalization, load_state_dict.
"""

from __future__ import annotations

import logging
import math
from typing import TYPE_CHECKING, Any, NoReturn

import torch
import torch.nn as nn
from rsl_rl.networks import MLP, EmpiricalNormalization
from torch.distributions import Normal

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tensordict import TensorDict


class PolicyBase(nn.Module):
    """Base class for constrained actor-critic policies.

    Provides shared infrastructure for ActorCriticEncoder and
    ActorCriticAsymConstrained: obs group parsing, critic/cost_critic
    construction, Gaussian distribution management, and evaluate API.
    """

    is_recurrent: bool = False

    def _init_base(
        self,
        obs: TensorDict,
        obs_groups: dict[str, list[str]],
        num_actions: int,
        policy_obs_dim: int,
        privileged_dim: int,
        num_critic_obs: int,
        # Critic
        critic_obs_normalization: bool,
        critic_hidden_dims: list[int] | tuple[int, ...],
        activation: str,
        # Cost critic
        num_constraints: int,
        cost_critic_hidden_dims: list[int] | tuple[int, ...],
        # Noise
        init_noise_std: float,
        # State-conditioned action std (Phase 2: falsification track).
        # OFF (default) = byte-identical baseline: std is a single state-independent
        # log_std Parameter. ON = the actor emits 2*num_actions (mean + log_std head);
        # std becomes a function of state, clamped to [min_std, max_std] in-policy.
        state_dependent_std: bool = False,
        min_std: float = 0.05,
        max_std: float = 2.0,
    ) -> None:
        """Initialize shared components. Called from subclass __init__."""
        # Store dimensions
        self.num_actions = num_actions
        self.state_dependent_std = state_dependent_std
        # Clamp bounds for the state-conditioned log_std head (log-space).
        # Mirrors ConstraintTRPO's post-step sigma clamp so the per-state std is
        # bounded the same way the global log_std would be.
        self._log_min_std = math.log(min_std)
        self._log_max_std = math.log(max_std)
        self.obs_groups = obs_groups
        self.policy_obs_dim = policy_obs_dim
        self.privileged_dim = privileged_dim

        # Parse obs_groups: require [policy_obs, privileged]
        policy_groups = obs_groups["policy"]
        if len(policy_groups) < 2:
            raise ValueError(
                f"{type(self).__name__} requires at least 2 obs groups in 'policy' "
                f"[policy_obs, privileged], got {len(policy_groups)}: {policy_groups}"
            )
        self._policy_obs_key = policy_groups[0]
        self._privileged_key = policy_groups[1]

        # Verify dimensions
        if obs[self._policy_obs_key].shape[-1] != policy_obs_dim:
            raise ValueError(f"Policy obs dim {obs[self._policy_obs_key].shape[-1]} != expected {policy_obs_dim}")
        if obs[self._privileged_key].shape[-1] != privileged_dim:
            raise ValueError(f"Privileged dim {obs[self._privileged_key].shape[-1]} != expected {privileged_dim}")

        # Asymmetric critic
        self.num_critic_obs = num_critic_obs
        self.critic_obs_normalization = critic_obs_normalization
        self.critic_obs_normalizer = (
            EmpiricalNormalization(num_critic_obs) if critic_obs_normalization else nn.Identity()
        )
        self.critic = MLP(num_critic_obs, 1, list(critic_hidden_dims), activation)

        # Cost critic (multi-head): same input as reward critic -> K outputs.
        self.num_constraints = num_constraints
        if num_constraints > 0:
            self.cost_critic = MLP(num_critic_obs, num_constraints, list(cost_critic_hidden_dims), activation)
        else:
            self.cost_critic = None

        # Action noise (Gaussian policy, log_std parameterization).
        # ALWAYS created, even when state_dependent_std=True. When ON it is unused for
        # action sampling (the per-state log_std head supplies std), but it MUST remain a
        # live nn.Parameter so ConstraintTRPO's post-step clamp (constraint_trpo.py:488-491
        # `self.policy.log_std.data.clamp_(...)`) never AttributeErrors. It rides in the
        # TRPO param set harmlessly (its KL gradient is ~0 when it does not feed the
        # distribution), and the per-state std is bounded by the in-policy clamp below.
        self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
        self.distribution: Normal | None = None
        Normal.set_default_validate_args(False)

    # --- No-op / error methods ---

    def reset(self, _dones: torch.Tensor | None = None) -> None:
        """No-op for non-recurrent networks."""
        pass

    def forward(self) -> NoReturn:
        raise NotImplementedError("Use act(), act_inference(), or evaluate().")

    # --- Properties ---

    @property
    def action_mean(self) -> torch.Tensor:
        assert self.distribution is not None
        return self.distribution.mean

    @property
    def action_std(self) -> torch.Tensor:
        assert self.distribution is not None
        return self.distribution.stddev

    @property
    def entropy(self) -> torch.Tensor:
        assert self.distribution is not None
        return self.distribution.entropy().sum(dim=-1)

    # --- Distribution ---

    def _update_distribution(self, actor_out: torch.Tensor) -> None:
        """Build the Gaussian policy distribution from the raw actor output.

        state_dependent_std OFF (default, byte-identical baseline):
            actor_out is the mean (num_actions). std = exp(global log_std), broadcast
            to all states (state-INDEPENDENT).

        state_dependent_std ON:
            actor_out is cat([mean, log_std]) (2*num_actions). std = exp(log_std head),
            clamped in log-space to [min_std, max_std] so the per-state std stays in the
            same range ConstraintTRPO would otherwise enforce on the global log_std.
        """
        if self.state_dependent_std:
            mean, log_std = torch.split(actor_out, self.num_actions, dim=-1)
            log_std = log_std.clamp(min=self._log_min_std, max=self._log_max_std)
            std = torch.exp(log_std)
        else:
            mean = actor_out
            std = torch.exp(self.log_std).expand_as(mean)
        self.distribution = Normal(mean, std)

    def get_actions_log_prob(self, actions: torch.Tensor) -> torch.Tensor:
        """Log probability of actions under current distribution."""
        assert self.distribution is not None
        return self.distribution.log_prob(actions).sum(dim=-1)

    # --- Critic API (shared) ---

    def _get_critic_obs(self, obs: TensorDict) -> torch.Tensor:
        """Build critic observation. Override in subclass for z-augmented critic."""
        raise NotImplementedError

    def evaluate(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Evaluate value function (asymmetric critic)."""
        critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
        return self.critic(critic_obs)

    def evaluate_costs(self, obs: TensorDict) -> torch.Tensor:
        """Evaluate per-constraint cost values via multi-head cost critic."""
        if self.cost_critic is None:
            raise RuntimeError("evaluate_costs() called but num_constraints=0 (no cost critic)")
        critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
        return self.cost_critic(critic_obs)
