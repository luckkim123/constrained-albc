# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Teacher policy network: MLP Encoder + MLP Actor + MLP Critic + optional Cost Critic.

Architecture (HORA-style normalization):
    Encoder: p_t (privileged) -> normalize -> MLP -> softsign -> z (latent)
    Actor:   cat([normalize(o_t), z]) -> MLP -> actions (Gaussian policy)
    Critic:  cat([o_t, p_t]) -> MLP -> value (asymmetric, no encoder gradient)

    critic_uses_z=True variant (asymmetric with encoder gradient):
    Critic:  cat([o_t, z, p_t]) -> MLP -> value
    Value loss gradient flows through z to encoder, providing learning signal
    from both actor (surrogate loss) and critic (value loss).

    Cost Critic (when num_constraints > 0):
    Cost Critic: cat([o_t, z, p_t]) -> MLP -> K (multi-head, one per constraint)
    Named "cost_critic" so ConstraintTRPO classifies it as a value parameter.

    o_t is unified: current proprioception (20D) + temporal history (46D) + integral (3D) = 69D.

    Encoder input normalization modes:
      - Static min-max (HORA-style): (2*x - upper - lower) / (upper - lower) -> [-1, 1]
        Deterministic, no running stats, no z drift. Preferred.
      - EmpiricalNormalization: Running mean/std (legacy, causes z drift -> KL spike).
      - None: Raw p_t input.

    Actor normalization: o_t via EmpiricalNorm.
    z is kept raw since softsign already bounds it to (-1, 1).
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import torch
import torch.nn as nn
import torch.nn.functional as F
from rsl_rl.networks import MLP, EmpiricalNormalization

from ._policy_base import PolicyBase
from ._z_ablation import apply_z_ablation, validate_ablation_mode

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from tensordict import TensorDict


class ActorCriticEncoder(PolicyBase):
    """Teacher policy with encoder for privileged-to-latent compression.

    Separate actor/critic MLPs. Critic uses privileged info directly (asymmetric).
    With critic_uses_z=True, value gradient also flows to encoder via z.
    """

    def __init__(
        self,
        obs: TensorDict,
        obs_groups: dict[str, list[str]],
        num_actions: int,
        # Encoder
        policy_obs_dim: int = 69,
        privileged_dim: int = 28,
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
        # Asymmetric critic with z: cat([o_t, z, p_t]), value gradient to encoder
        critic_uses_z: bool = False,
        # Cost critic (IPO constraints)
        num_constraints: int = 0,
        cost_critic_hidden_dims: list[int] | tuple[int, ...] = (512, 256, 128),
        **kwargs: Any,
    ) -> None:
        if kwargs:
            logger.warning("ActorCriticEncoder ignoring unexpected kwargs: %s", list(kwargs.keys()))
        super().__init__()

        self.encoder_latent_dim = encoder_latent_dim
        self._critic_uses_z = critic_uses_z

        # z-ablation (inference-time encoder diagnostic; None = disabled, training-safe)
        self._z_ablation: str | None = None
        self._z_ablation_value: torch.Tensor | None = None

        # Critic input dim depends on critic_uses_z
        num_critic_obs = policy_obs_dim + privileged_dim
        if critic_uses_z:
            num_critic_obs += encoder_latent_dim

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
            # Pre-compute for fast static min-max: (2*x - midpoint) / range.
            # Registered as buffers so module.to(device) moves them alongside inputs.
            self.register_buffer("_enc_obs_range", upper - lower)
            self.register_buffer("_enc_obs_midpoint", upper + lower)
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
        self._encoder_output_norm = nn.LayerNorm(encoder_latent_dim) if encoder_output_norm else nn.Identity()
        norm_str = " -> LayerNorm" if encoder_output_norm else ""
        logger.info(
            "Encoder: %dD -> %s%s -> softsign -> %dD",
            privileged_dim,
            encoder_hidden_dims,
            norm_str,
            encoder_latent_dim,
        )

        # Actor
        num_actor_obs = policy_obs_dim + encoder_latent_dim
        num_actor_obs_norm = policy_obs_dim  # normalize o_t only (z bounded by softsign)
        self._num_actor_obs_norm = num_actor_obs_norm
        self.actor_obs_normalization = actor_obs_normalization
        self.actor_obs_normalizer = (
            EmpiricalNormalization(num_actor_obs_norm) if actor_obs_normalization else nn.Identity()
        )
        self.actor = MLP(num_actor_obs, num_actions, list(actor_hidden_dims), activation)

        critic_desc = "asymmetric+z" if critic_uses_z else "asymmetric"
        logger.info(
            "Actor: %dD (obs=%d+z=%d) -> %s -> %dD | Critic [%s]: %dD -> %s -> 1D",
            num_actor_obs,
            policy_obs_dim,
            encoder_latent_dim,
            actor_hidden_dims,
            num_actions,
            critic_desc,
            num_critic_obs,
            critic_hidden_dims,
        )
        if num_constraints > 0:
            logger.info(
                "Cost critic [multi-head]: %dD -> %s -> %dD",
                num_critic_obs,
                cost_critic_hidden_dims,
                num_constraints,
            )

    # --- Observation processing ---

    def _encode(self, obs: TensorDict) -> torch.Tensor:
        """Encode privileged info into latent z: p_t -> [select] -> normalize -> MLP -> [LayerNorm] -> softsign -> z."""
        p_t = obs[self._privileged_key]
        if self._enc_obs_indices is not None:
            p_t = p_t[:, self._enc_obs_indices]
        if self._has_static_enc_norm:
            # Static min-max: [lower, upper] -> [-1, 1] (HORA-style, deterministic)
            p_t = (2.0 * p_t - self._enc_obs_midpoint) / self._enc_obs_range
        else:
            p_t = self.encoder_obs_normalizer(p_t)
        z = F.softsign(self._encoder_output_norm(self.encoder(p_t)))
        return apply_z_ablation(z, self._z_ablation, self._z_ablation_value)

    def set_z_ablation(
        self, mode: str | None, nominal_obs: TensorDict | None = None
    ) -> None:
        """Enable/disable inference-time z-ablation (encoder gap-#1 diagnostic).

        mode None  -> disabled (default; training/eval unchanged).
        mode "zero" -> _encode returns zeros (latent carries no information).
        mode "mean" -> _encode returns encode(nominal_obs), cached now.
        Invalid mode or "mean" without nominal_obs -> ValueError (loud-fail).
        """
        validate_ablation_mode(mode)
        if mode == "mean":
            if nominal_obs is None:
                raise ValueError("z_ablation 'mean' requires nominal_obs to build the cache")
            prev = self._z_ablation
            self._z_ablation = None  # force true encoder output for the cache
            try:
                with torch.no_grad():
                    self._z_ablation_value = (
                        self._encode(nominal_obs).mean(dim=0, keepdim=True).detach()
                    )
            finally:
                self._z_ablation = prev
        else:
            self._z_ablation_value = None
        self._z_ablation = mode

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
        """Critic observation.

        critic_uses_z=False: cat([o_t, p_t]) -- no encoder gradient from value loss.
        critic_uses_z=True:  cat([o_t, z, p_t]) -- value gradient flows to encoder via z.
        """
        parts = [obs[self._policy_obs_key]]
        if self._critic_uses_z:
            parts.append(self._encode(obs))
        parts.append(obs[self._privileged_key])
        return torch.cat(parts, dim=-1)

    # --- Core API ---

    def act(self, obs: TensorDict, **_kwargs: Any) -> torch.Tensor:
        """Sample action from Gaussian policy (no action clamping)."""
        actor_obs = self._get_actor_obs(obs)
        self._update_distribution(self.actor(actor_obs))
        assert self.distribution is not None
        return self.distribution.sample()

    def act_inference(self, obs: TensorDict) -> torch.Tensor:
        """Deterministic action (mean, no clamping)."""
        return self.actor(self._get_actor_obs(obs))

    def update_normalization(self, obs: TensorDict) -> None:
        """Update observation normalization running statistics.

        Static min-max encoder normalization has no running stats (no-op).
        Actor normalizer updates on o_t dimensions, excluding z.
        """
        if self.encoder_obs_normalization and not self._has_static_enc_norm:
            self.encoder_obs_normalizer.update(obs[self._privileged_key])
        if self.actor_obs_normalization:
            self.actor_obs_normalizer.update(obs[self._policy_obs_key])
        if self.critic_obs_normalization:
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
