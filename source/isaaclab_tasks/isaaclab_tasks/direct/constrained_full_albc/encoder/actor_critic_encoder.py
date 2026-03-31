# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Teacher policy network: MLP Encoder + MLP Actor + MLP Critic + optional Cost Critic.

Two modes of operation:
    Separate (default): Encoder, Actor, and Critic are independent MLPs.
    Shared backbone (HORA-style): Actor and Critic share an MLP backbone with
        linear heads, enabling value gradient flow to the encoder.

Architecture (separate mode, HORA-style normalization):
    Encoder: p_t (privileged) -> normalize -> MLP -> softsign -> z (latent)
    Actor:   cat([normalize(o_t), z]) -> MLP -> actions (Gaussian policy)
    Critic:  cat([o_t, p_t]) -> MLP -> value (asymmetric, no encoder gradient)

    critic_uses_z=True variant (asymmetric with encoder gradient):
    Critic:  cat([o_t, z, p_t]) -> MLP -> value
    Value loss gradient flows through z to encoder, providing learning signal
    from both actor (surrogate loss) and critic (value loss).

    Cost Critic (when num_constraints > 0, separate mode only):
    Cost Critic: cat([o_t, z, p_t]) -> MLP -> K (multi-head, one per constraint)
    Shares the same input as the reward critic. Named "cost_critic" so that
    ConstraintTRPO classifies it as a value parameter (Adam, not TRPO).

    o_t is unified: current proprioception (26D) + temporal history (55D) = 81D.
    History is merged into o_t by the environment, not handled separately.

    Encoder input normalization modes:
      - Static min-max (HORA-style): (2*x - upper - lower) / (upper - lower) -> [-1, 1]
        Deterministic, no running stats, no z drift. Preferred.
      - EmpiricalNormalization: Running mean/std (legacy, causes z drift -> KL spike).
      - None: Raw p_t input.

    Actor normalization: o_t via EmpiricalNorm.
    z is kept raw since softsign already bounds it to (-1, 1).

Architecture (shared backbone mode):
    Encoder: p_t (privileged) -> normalize -> MLP -> softsign -> z (latent)
    Backbone: cat([normalize(o_t), z]) -> shared MLP -> features
    Action head: features -> Linear -> actions
    Value head:  features -> Linear -> value
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any, NoReturn

import torch
import torch.nn as nn
import torch.nn.functional as F
from rsl_rl.networks import MLP, EmpiricalNormalization
from torch.distributions import Normal

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tensordict import TensorDict


class ActorCriticEncoder(nn.Module):
    """Teacher policy with encoder for privileged-to-latent compression.

    Supports two architectures:
        shared_backbone=False (default): Separate actor/critic MLPs. Critic uses
            privileged info directly (asymmetric). Encoder gradient comes only
            from actor loss.
        shared_backbone=True (HORA-style): Single backbone MLP with linear heads
            for action and value. Both actor and critic losses flow gradient
            through the encoder, providing a stronger learning signal.
    """

    is_recurrent: bool = False

    def __init__(
        self,
        obs: TensorDict,
        obs_groups: dict[str, list[str]],
        num_actions: int,
        # Encoder
        policy_obs_dim: int = 81,
        privileged_dim: int = 23,
        encoder_hidden_dims: list[int] | tuple[int, ...] = (256, 128, 64),
        encoder_latent_dim: int = 9,
        encoder_activation: str = "elu",
        encoder_obs_normalization: bool = False,
        encoder_obs_lower: list[float] | None = None,
        encoder_obs_upper: list[float] | None = None,
        encoder_output_norm: bool = False,
        encoder_obs_indices: list[int] | None = None,
        # Actor-Critic
        actor_obs_normalization: bool = False,
        critic_obs_normalization: bool = False,
        actor_hidden_dims: list[int] | tuple[int, ...] = (256, 128, 64),
        critic_hidden_dims: list[int] | tuple[int, ...] = (512, 256, 128),
        activation: str = "elu",
        init_noise_std: float = 1.0,
        # Shared backbone (HORA-style): actor+critic share MLP, value gradient to encoder
        shared_backbone: bool = False,
        # Asymmetric critic with z: cat([o_t, z, p_t]), value gradient to encoder
        critic_uses_z: bool = False,
        # Cost critic (IPO constraints, separate mode only)
        num_constraints: int = 0,
        cost_critic_hidden_dims: list[int] | tuple[int, ...] = (512, 256, 128),
        **kwargs: Any,
    ) -> None:
        if kwargs:
            logger.warning("ActorCriticEncoder ignoring unexpected kwargs: %s", list(kwargs.keys()))
        super().__init__()

        # Store dimensions
        self.obs_groups = obs_groups
        self.policy_obs_dim = policy_obs_dim
        self.privileged_dim = privileged_dim
        self.encoder_latent_dim = encoder_latent_dim
        self.shared_backbone_mode = shared_backbone
        self._critic_uses_z = critic_uses_z

        # Parse obs_groups: require [policy_obs, privileged]
        policy_groups = obs_groups["policy"]
        if len(policy_groups) < 2:
            raise ValueError(
                f"ActorCriticEncoder requires at least 2 obs groups in 'policy' "
                f"[policy_obs, privileged], got {len(policy_groups)}: {policy_groups}"
            )
        self._policy_obs_key = policy_groups[0]
        self._privileged_key = policy_groups[1]

        # Verify dimensions
        if obs[self._policy_obs_key].shape[-1] != policy_obs_dim:
            raise ValueError(f"Policy obs dim {obs[self._policy_obs_key].shape[-1]} != expected {policy_obs_dim}")
        if obs[self._privileged_key].shape[-1] != privileged_dim:
            raise ValueError(f"Privileged dim {obs[self._privileged_key].shape[-1]} != expected {privileged_dim}")

        # --- Encoder input selection: optionally use a subset of privileged dims ---
        if encoder_obs_indices is not None:
            self.register_buffer("_enc_obs_indices", torch.tensor(encoder_obs_indices, dtype=torch.long))
            encoder_input_dim = len(encoder_obs_indices)
            logger.info(
                "Encoder input selection: %d/%d dims %s",
                encoder_input_dim,
                privileged_dim,
                encoder_obs_indices,
            )
        else:
            self._enc_obs_indices = None
            encoder_input_dim = privileged_dim

        # --- Encoder: p_t -> [select] -> normalize -> MLP -> softsign -> z ---
        self._has_static_enc_norm = encoder_obs_lower is not None and encoder_obs_upper is not None
        if self._has_static_enc_norm:
            # Static min-max normalization (HORA-style): deterministic, no running stats
            lower = torch.tensor(encoder_obs_lower, dtype=torch.float32)
            upper = torch.tensor(encoder_obs_upper, dtype=torch.float32)
            if lower.shape[0] != encoder_input_dim or upper.shape[0] != encoder_input_dim:
                raise ValueError(
                    f"encoder_obs_lower/upper dim {lower.shape[0]}/{upper.shape[0]} "
                    f"!= encoder_input_dim {encoder_input_dim}"
                )
            self.register_buffer("_enc_obs_lower", lower)
            self.register_buffer("_enc_obs_upper", upper)
            self.encoder_obs_normalizer = nn.Identity()
            self.encoder_obs_normalization = False
            logger.info("Encoder normalization: static min-max (HORA-style) -> [-1, 1]")
        else:
            self.encoder_obs_normalization = encoder_obs_normalization
            self.encoder_obs_normalizer = (
                EmpiricalNormalization(encoder_input_dim) if encoder_obs_normalization else nn.Identity()
            )
            logger.info("Encoder normalization: %s", "EmpiricalNorm" if encoder_obs_normalization else "none")
        self.encoder = MLP(encoder_input_dim, encoder_latent_dim, list(encoder_hidden_dims), encoder_activation)
        # Pre-softsign LayerNorm: prevents weight growth from causing activation saturation.
        # LayerNorm normalizes MLP output to ~N(0,1), keeping softsign in its responsive range.
        self._encoder_output_norm = nn.LayerNorm(encoder_latent_dim) if encoder_output_norm else nn.Identity()
        norm_str = " -> LayerNorm" if encoder_output_norm else ""
        logger.info(
            "Encoder: %dD -> %s%s -> softsign -> %dD",
            privileged_dim,
            encoder_hidden_dims,
            norm_str,
            encoder_latent_dim,
        )

        # Actor input dimension (shared between modes)
        num_actor_obs = policy_obs_dim + encoder_latent_dim
        # Normalizer covers only o_t (excludes z which is already bounded by softsign).
        # HORA-style: normalize observations, keep encoder latent raw.
        num_actor_obs_norm = policy_obs_dim
        self._num_actor_obs_norm = num_actor_obs_norm

        if shared_backbone:
            # --- Shared backbone: cat([normalize(o_t, hist), z]) -> backbone -> features -> heads ---
            # Cost critic not supported in shared backbone mode (use ActorCriticEncoderConstrained).
            self.num_constraints = 0
            self.cost_critic = None
            bb_dims = list(critic_hidden_dims)
            feature_dim = bb_dims[-1]
            self.actor_obs_normalization = actor_obs_normalization
            self.actor_obs_normalizer = (
                EmpiricalNormalization(num_actor_obs_norm) if actor_obs_normalization else nn.Identity()
            )
            self.backbone = MLP(num_actor_obs, feature_dim, bb_dims[:-1], activation, last_activation=activation)
            self.action_head = nn.Linear(feature_dim, num_actions)
            self.value_head = nn.Linear(feature_dim, 1)
            nn.init.zeros_(self.action_head.bias)
            nn.init.zeros_(self.value_head.bias)
            logger.info(
                "Shared backbone: %dD -> %s -> %dD features -> action(%dD) + value(1D)",
                num_actor_obs,
                bb_dims,
                feature_dim,
                num_actions,
            )
            # Compatibility attrs
            self.num_critic_obs = num_actor_obs
            self.critic_obs_normalization = False
        else:
            # --- Separate actor and critic (original mode) ---
            self.actor_obs_normalization = actor_obs_normalization
            self.actor_obs_normalizer = (
                EmpiricalNormalization(num_actor_obs_norm) if actor_obs_normalization else nn.Identity()
            )
            self.actor = MLP(num_actor_obs, num_actions, list(actor_hidden_dims), activation)
            logger.info(
                "Actor: %dD (obs=%d+z=%d) -> %s -> %dD",
                num_actor_obs,
                policy_obs_dim,
                encoder_latent_dim,
                actor_hidden_dims,
                num_actions,
            )

            # Asymmetric critic
            num_critic_obs = policy_obs_dim + privileged_dim
            if critic_uses_z:
                # cat([o_t, hist, z, p_t]): value gradient flows to encoder via z
                num_critic_obs += encoder_latent_dim
            self.num_critic_obs = num_critic_obs
            self.critic_obs_normalization = critic_obs_normalization
            self.critic_obs_normalizer = (
                EmpiricalNormalization(num_critic_obs) if critic_obs_normalization else nn.Identity()
            )
            self.critic = MLP(num_critic_obs, 1, list(critic_hidden_dims), activation)
            critic_desc = "asymmetric+z" if critic_uses_z else "asymmetric"
            logger.info("Critic [%s]: %dD -> %s -> 1D", critic_desc, num_critic_obs, critic_hidden_dims)

            # Cost critic (multi-head): same input as reward critic -> K outputs.
            # Named "cost_critic" so ConstraintTRPO classifies it as value param.
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

    def _encode(self, obs: TensorDict) -> torch.Tensor:
        """Encode privileged info into latent z: p_t -> [select] -> normalize -> MLP -> [LayerNorm] -> softsign -> z."""
        p_t = obs[self._privileged_key]
        if self._enc_obs_indices is not None:
            p_t = p_t[:, self._enc_obs_indices]
        if self._has_static_enc_norm:
            # Static min-max: [lower, upper] -> [-1, 1] (HORA-style, deterministic)
            p_t = (2.0 * p_t - self._enc_obs_upper - self._enc_obs_lower) / (self._enc_obs_upper - self._enc_obs_lower)
        else:
            p_t = self.encoder_obs_normalizer(p_t)
        return F.softsign(self._encoder_output_norm(self.encoder(p_t)))

    def _get_actor_obs(self, obs: TensorDict) -> torch.Tensor:
        """Actor observation: cat([normalize(o_t), z_raw]).

        HORA-style: only o_t is normalized via EmpiricalNorm.
        z is kept raw since softsign already bounds it to (-1, 1), and normalizing
        non-stationary encoder output with running stats causes KL instability.
        """
        o_t = obs[self._policy_obs_key]
        z = self._encode(obs)
        obs_normed = self.actor_obs_normalizer(o_t)
        return torch.cat([obs_normed, z], dim=-1)

    def _get_critic_obs(self, obs: TensorDict) -> torch.Tensor:
        """Critic observation (separate mode).

        critic_uses_z=False: cat([o_t, p_t]) -- no encoder gradient from value loss.
        critic_uses_z=True:  cat([o_t, z, p_t]) -- value gradient flows to encoder via z.
        """
        parts = [obs[self._policy_obs_key]]
        if self._critic_uses_z:
            parts.append(self._encode(obs))
        parts.append(obs[self._privileged_key])
        return torch.cat(parts, dim=-1)

    # --- Action distribution ---

    def _update_distribution(self, mean: torch.Tensor) -> None:
        std = torch.exp(self.log_std).expand_as(mean)
        self.distribution = Normal(mean, std)

    # --- Core API ---

    def act(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Sample action from Gaussian policy (no action clamping)."""
        actor_obs = self._get_actor_obs(obs)
        if self.shared_backbone_mode:
            features = self.backbone(actor_obs)
            mean = self.action_head(features)
        else:
            mean = self.actor(actor_obs)
        self._update_distribution(mean)
        assert self.distribution is not None
        return self.distribution.sample()

    def act_inference(self, obs: TensorDict) -> torch.Tensor:
        """Deterministic action (mean, no clamping)."""
        actor_obs = self._get_actor_obs(obs)
        if self.shared_backbone_mode:
            features = self.backbone(actor_obs)
            return self.action_head(features)
        return self.actor(actor_obs)

    def evaluate(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Evaluate value function.

        In shared backbone mode, value gradient flows through encoder (HORA-style).
        In separate mode with critic_uses_z, value gradient flows to encoder via z.
        In separate mode without critic_uses_z, critic uses privileged info only.
        """
        if self.shared_backbone_mode:
            # Backbone uses cat([o_t, z]) -- encoder gradient from value loss
            actor_obs = self._get_actor_obs(obs)
            features = self.backbone(actor_obs)
            return self.value_head(features)
        else:
            critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
            return self.critic(critic_obs)

    def evaluate_costs(self, obs: TensorDict) -> torch.Tensor:
        """Evaluate per-constraint cost values via separate cost critic MLP.

        Uses the same input as the reward critic (asymmetric obs).
        Multi-head output: one value per constraint.

        Returns:
            Cost value predictions. Shape: (batch, K).
        """
        if self.cost_critic is None:
            raise RuntimeError("evaluate_costs() called but num_constraints=0 (no cost critic)")
        critic_obs = self.critic_obs_normalizer(self._get_critic_obs(obs))
        return self.cost_critic(critic_obs)

    def get_actions_log_prob(self, actions: torch.Tensor) -> torch.Tensor:
        """Log probability of actions under current distribution."""
        assert self.distribution is not None
        return self.distribution.log_prob(actions).sum(dim=-1)

    def update_normalization(self, obs: TensorDict) -> None:
        """Update observation normalization running statistics.

        Static min-max encoder normalization has no running stats (no-op).
        Actor normalizer updates on o_t dimensions, excluding z.
        """
        if self.encoder_obs_normalization and not self._has_static_enc_norm:
            self.encoder_obs_normalizer.update(obs[self._privileged_key])
        if self.actor_obs_normalization:
            self.actor_obs_normalizer.update(obs[self._policy_obs_key])
        if not self.shared_backbone_mode and self.critic_obs_normalization:
            self.critic_obs_normalizer.update(self._get_critic_obs(obs))

    def load_state_dict(self, state_dict: dict, strict: bool = True) -> bool:
        """Load model parameters. Returns True (RSL-RL API contract)."""
        if self.encoder_obs_normalization and not self._has_static_enc_norm:
            prefix = "encoder_obs_normalizer."
            if not any(k.startswith(prefix) for k in state_dict):
                logger.info("Checkpoint missing encoder_obs_normalizer; injecting defaults.")
                for k, v in self.encoder_obs_normalizer.state_dict().items():
                    state_dict[prefix + k] = v
        # Migrate actor_obs_normalizer from old (full o_t+z) to new (o_t only) dimension
        if self.actor_obs_normalization:
            norm_prefix = "actor_obs_normalizer."
            mean_key = norm_prefix + "_mean"
            if mean_key in state_dict:
                old_dim = state_dict[mean_key].shape[-1]
                new_dim = self._num_actor_obs_norm
                if old_dim != new_dim:
                    logger.info(
                        "Actor obs normalizer dim mismatch (%d -> %d); resetting to defaults.",
                        old_dim,
                        new_dim,
                    )
                    for k, v in self.actor_obs_normalizer.state_dict().items():
                        state_dict[norm_prefix + k] = v
        # Inject cost_critic defaults if loading checkpoint without cost critic
        if self.cost_critic is not None:
            cc_prefix = "cost_critic."
            if not any(k.startswith(cc_prefix) for k in state_dict):
                logger.info("Checkpoint lacks cost_critic; using random initialization.")
                for k, v in self.cost_critic.state_dict().items():
                    state_dict[cc_prefix + k] = v
        super().load_state_dict(state_dict, strict=False)
        return True
