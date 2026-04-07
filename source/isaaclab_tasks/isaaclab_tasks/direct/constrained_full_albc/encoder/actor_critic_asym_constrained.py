# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Asymmetric actor-critic without encoder (NoEncoder ablation for Full-DOF ALBC).

This is a baseline for Isaac-FullDOF-TRPO-v0 that removes only the encoder while
keeping the TRPO + IPO algorithm, DR, reward, and constraint configuration
identical. The actor receives only the 81D policy observation (current proprio
+ temporal history), while the critic and cost critic receive the full
asymmetric observation cat([o_t(81D), p_t(24D)]) = 105D.

Architecture:
    Actor:       o_t(81D) -> MLP[256,128,64] -> 8D (Gaussian mean)
    Critic:      cat(o_t(81D), p_t(24D)) = 105D -> MLP[512,256,128] -> 1D
    Cost Critic: cat(o_t(81D), p_t(24D)) = 105D -> MLP[512,256,128] -> K (multi-head)
    log_std:     nn.Parameter(num_actions)

Parameter naming matches ActorCriticEncoder's value_prefixes contract for
ConstraintTRPO classification:
    - "actor." -> policy params (TRPO natural gradient)
    - "critic." / "cost_critic." -> value params (Adam optimizer)
    - "log_std" -> sigma optimizer (decoupled Adam)

Compared to ActorCriticEncoder(critic_uses_z=False), this class omits the
encoder module and the z latent concatenation in the actor path. The critic
path is identical to ActorCriticEncoder(critic_uses_z=False) which already
uses cat([o_t, p_t]).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NoReturn

import torch
import torch.nn as nn
from rsl_rl.networks import MLP, EmpiricalNormalization
from torch.distributions import Normal

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tensordict import TensorDict


class ActorCriticAsymConstrained(nn.Module):
    """Asymmetric actor-critic with cost critic (no encoder).

    Actor uses policy obs only (o_t). Critic and cost critic use asymmetric
    input cat([o_t, p_t]). ConstraintTRPO auto-detects the absence of encoder
    parameters and skips encoder-specific logging/decomposition.
    """

    is_recurrent: bool = False

    def __init__(
        self,
        obs: TensorDict,
        obs_groups: dict[str, list[str]],
        num_actions: int,
        # Observation dimensions
        policy_obs_dim: int = 81,
        privileged_dim: int = 24,
        # Actor-Critic
        actor_obs_normalization: bool = False,
        critic_obs_normalization: bool = False,
        actor_hidden_dims: list[int] | tuple[int, ...] = (256, 128, 64),
        critic_hidden_dims: list[int] | tuple[int, ...] = (512, 256, 128),
        activation: str = "elu",
        init_noise_std: float = 1.0,
        # Cost critic (IPO constraints)
        num_constraints: int = 0,
        cost_critic_hidden_dims: list[int] | tuple[int, ...] = (512, 256, 128),
        **kwargs: Any,
    ) -> None:
        if kwargs:
            logger.warning("ActorCriticAsymConstrained ignoring unexpected kwargs: %s", list(kwargs.keys()))
        super().__init__()

        # Store dimensions
        self.obs_groups = obs_groups
        self.policy_obs_dim = policy_obs_dim
        self.privileged_dim = privileged_dim

        # Parse obs_groups: require [policy_obs, privileged]
        policy_groups = obs_groups["policy"]
        if len(policy_groups) < 2:
            raise ValueError(
                f"ActorCriticAsymConstrained requires at least 2 obs groups in 'policy' "
                f"[policy_obs, privileged], got {len(policy_groups)}: {policy_groups}"
            )
        self._policy_obs_key = policy_groups[0]
        self._privileged_key = policy_groups[1]

        # Verify dimensions
        if obs[self._policy_obs_key].shape[-1] != policy_obs_dim:
            raise ValueError(f"Policy obs dim {obs[self._policy_obs_key].shape[-1]} != expected {policy_obs_dim}")
        if obs[self._privileged_key].shape[-1] != privileged_dim:
            raise ValueError(f"Privileged dim {obs[self._privileged_key].shape[-1]} != expected {privileged_dim}")

        # --- Actor (policy obs only) ---
        self.actor_obs_normalization = actor_obs_normalization
        self.actor_obs_normalizer = EmpiricalNormalization(policy_obs_dim) if actor_obs_normalization else nn.Identity()
        self.actor = MLP(policy_obs_dim, num_actions, list(actor_hidden_dims), activation)
        logger.info("Actor: %dD (policy obs only) -> %s -> %dD", policy_obs_dim, actor_hidden_dims, num_actions)

        # --- Asymmetric critic: cat([o_t, p_t]) ---
        num_critic_obs = policy_obs_dim + privileged_dim
        self.num_critic_obs = num_critic_obs
        self.critic_obs_normalization = critic_obs_normalization
        self.critic_obs_normalizer = (
            EmpiricalNormalization(num_critic_obs) if critic_obs_normalization else nn.Identity()
        )
        self.critic = MLP(num_critic_obs, 1, list(critic_hidden_dims), activation)
        logger.info("Critic [asymmetric]: %dD -> %s -> 1D", num_critic_obs, critic_hidden_dims)

        # --- Cost critic (multi-head): same input as reward critic ---
        self.num_constraints = num_constraints
        if num_constraints > 0:
            self.cost_critic = MLP(num_critic_obs, num_constraints, list(cost_critic_hidden_dims), activation)
            logger.info(
                "Cost critic [multi-head]: %dD -> %s -> %dD",
                num_critic_obs,
                cost_critic_hidden_dims,
                num_constraints,
            )
        else:
            self.cost_critic = None

        # Action noise (Gaussian policy, log_std parameterization)
        self.log_std = nn.Parameter(torch.log(init_noise_std * torch.ones(num_actions)))
        self.distribution: Normal | None = None
        Normal.set_default_validate_args(False)

    def reset(self, _dones: torch.Tensor | None = None) -> None:
        """No-op for non-recurrent networks."""
        pass

    def forward(self) -> NoReturn:
        raise NotImplementedError("Use act(), act_inference(), or evaluate().")

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

    # --- Observation processing ---

    def _get_actor_obs(self, obs: TensorDict) -> torch.Tensor:
        """Actor observation: normalize(o_t) only."""
        return self.actor_obs_normalizer(obs[self._policy_obs_key])

    def _get_critic_obs(self, obs: TensorDict) -> torch.Tensor:
        """Critic observation: cat([o_t, p_t]) (asymmetric)."""
        return torch.cat([obs[self._policy_obs_key], obs[self._privileged_key]], dim=-1)

    # --- Action distribution ---

    def _update_distribution(self, mean: torch.Tensor) -> None:
        std = torch.exp(self.log_std).expand_as(mean)
        self.distribution = Normal(mean, std)

    # --- Core API ---

    def act(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Sample action from Gaussian policy (no action clamping)."""
        mean = self.actor(self._get_actor_obs(obs))
        self._update_distribution(mean)
        assert self.distribution is not None
        return self.distribution.sample()

    def act_inference(self, obs: TensorDict) -> torch.Tensor:
        """Deterministic action (mean, no clamping)."""
        return self.actor(self._get_actor_obs(obs))

    def evaluate(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Evaluate value function using asymmetric critic input cat([o_t, p_t])."""
        critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
        return self.critic(critic_obs)

    def evaluate_costs(self, obs: TensorDict) -> torch.Tensor:
        """Evaluate per-constraint cost values via multi-head cost critic."""
        if self.cost_critic is None:
            raise RuntimeError("evaluate_costs() called but num_constraints=0 (no cost critic)")
        critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
        return self.cost_critic(critic_obs)

    def get_actions_log_prob(self, actions: torch.Tensor) -> torch.Tensor:
        """Log probability of actions under current distribution."""
        assert self.distribution is not None
        return self.distribution.log_prob(actions).sum(dim=-1)

    def update_normalization(self, obs: TensorDict) -> None:
        """Update observation normalization running statistics."""
        if self.actor_obs_normalization:
            self.actor_obs_normalizer.update(obs[self._policy_obs_key])
        if self.critic_obs_normalization:
            self.critic_obs_normalizer.update(self._get_critic_obs(obs))

    def load_state_dict(self, state_dict: dict, strict: bool = True) -> bool:
        """Load model parameters. Returns True (RSL-RL API contract)."""
        # Inject cost_critic defaults if loading checkpoint without cost critic
        if self.cost_critic is not None:
            cc_prefix = "cost_critic."
            if not any(k.startswith(cc_prefix) for k in state_dict):
                logger.info("Checkpoint lacks cost_critic; using random initialization.")
                for k, v in self.cost_critic.state_dict().items():
                    state_dict[cc_prefix + k] = v
        super().load_state_dict(state_dict, strict=False)
        return True
