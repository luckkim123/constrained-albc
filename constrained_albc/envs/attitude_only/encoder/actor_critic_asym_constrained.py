# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Asymmetric actor-critic without encoder (NoEncoder ablation for Full-DOF ALBC).

This is a baseline for Isaac-ConstrainedALBC-TRPO-v0 that removes only the encoder while
keeping the TRPO + IPO algorithm, DR, reward, and constraint configuration
identical. The actor receives only the 87D policy observation (current proprio
+ temporal history), while the critic and cost critic receive the full
asymmetric observation cat([o_t(87D), p_t(24D)]) = 111D.

Architecture:
    Actor:       o_t(87D) -> MLP[256,128,64] -> 8D (Gaussian mean)
    Critic:      cat(o_t(87D), p_t(24D)) = 111D -> MLP[512,256,128] -> 1D
    Cost Critic: cat(o_t(87D), p_t(24D)) = 111D -> MLP[512,256,128] -> K (multi-head)
    log_std:     nn.Parameter(num_actions)

Parameter naming matches ActorCriticEncoder's value_prefixes contract for
ConstraintTRPO classification:
    - "actor." -> policy params (TRPO natural gradient)
    - "critic." / "cost_critic." -> value params (Adam optimizer)
    - "log_std" -> policy params (TRPO natural gradient)
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import torch
from rsl_rl.networks import MLP, EmpiricalNormalization

from ._policy_base import PolicyBase

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tensordict import TensorDict


class ActorCriticAsymConstrained(PolicyBase):
    """Asymmetric actor-critic with cost critic (no encoder).

    Actor uses policy obs only (o_t). Critic and cost critic use asymmetric
    input cat([o_t, p_t]). ConstraintTRPO auto-detects the absence of encoder
    parameters and skips encoder-specific logging/decomposition.
    """

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

        num_critic_obs = policy_obs_dim + privileged_dim

        # Initialize shared base (obs_groups, critic, cost_critic, log_std)
        self._init_base(
            obs=obs,
            obs_groups=obs_groups,
            num_actions=num_actions,
            policy_obs_dim=policy_obs_dim,
            privileged_dim=privileged_dim,
            num_critic_obs=num_critic_obs,
            critic_obs_normalization=critic_obs_normalization,
            critic_hidden_dims=critic_hidden_dims,
            activation=activation,
            num_constraints=num_constraints,
            cost_critic_hidden_dims=cost_critic_hidden_dims,
            init_noise_std=init_noise_std,
        )

        # --- Actor (policy obs only) ---
        self.actor_obs_normalization = actor_obs_normalization
        self.actor_obs_normalizer = (
            EmpiricalNormalization(policy_obs_dim) if actor_obs_normalization else torch.nn.Identity()
        )
        self.actor = MLP(policy_obs_dim, num_actions, list(actor_hidden_dims), activation)
        logger.info("Actor: %dD (policy obs only) -> %s -> %dD", policy_obs_dim, actor_hidden_dims, num_actions)
        logger.info("Critic [asymmetric]: %dD -> %s -> 1D", num_critic_obs, critic_hidden_dims)
        if num_constraints > 0:
            logger.info(
                "Cost critic [multi-head]: %dD -> %s -> %dD",
                num_critic_obs,
                cost_critic_hidden_dims,
                num_constraints,
            )

    # --- Observation processing ---

    def _get_actor_obs(self, obs: TensorDict) -> torch.Tensor:
        """Actor observation: normalize(o_t) only."""
        return self.actor_obs_normalizer(obs[self._policy_obs_key])

    def _get_critic_obs(self, obs: TensorDict) -> torch.Tensor:
        """Critic observation: cat([o_t, p_t]) (asymmetric)."""
        return torch.cat([obs[self._policy_obs_key], obs[self._privileged_key]], dim=-1)

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
