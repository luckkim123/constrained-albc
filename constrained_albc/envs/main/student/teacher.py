# constrained_albc/envs/main/student/teacher.py
"""FrozenTeacher: loads r13_A checkpoint, exposes frozen encoder + actor + normalizer.

Uses ALBCActorCriticEncoder from the teacher's training registry so the
state_dict loads without modification. All parameters have requires_grad=False.
Autograd still flows through for student training (gradients to student encoder
only; teacher weights are never updated).
"""
from __future__ import annotations

import logging
import os

import torch
import torch.nn as nn

from .config import StudentCfg

logger = logging.getLogger(__name__)


class FrozenTeacher(nn.Module):
    """Wraps r13_A's ActorCriticEncoder; exposes encode(), normalize_obs(), actor_forward().

    Attributes:
        latent_dim: 9
        obs_dim: 69 (policy obs)
        privileged_dim: 27
    """

    def __init__(self, cfg: StudentCfg, device: torch.device) -> None:
        super().__init__()
        self.cfg = cfg
        self.device = device

        # Build a teacher policy with the same arch as r13_A. We use the registry
        # class rather than instantiating ActorCriticEncoder directly to ensure
        # the exact arch (e.g. ALBCActorCriticEncoder overrides).
        from constrained_albc.envs.main.encoder import (
            ActorCriticEncoder,
        )
        from constrained_albc.envs.main.agents.rsl_rl_ppo_cfg import (
            _PRIV_OBS_LOWER,
            _PRIV_OBS_UPPER,
        )

        # We don't have the real TensorDict here; instead we build bypassing obs_groups
        # by calling nn.Module construction of the components directly.
        # Easiest path: reuse ActorCriticEncoder via a minimal dummy obs dict.
        from tensordict import TensorDict

        dummy_obs = TensorDict(
            {
                "policy": torch.zeros(1, cfg.policy_obs_dim),
                "privileged": torch.zeros(1, cfg.privileged_dim),
            },
            batch_size=[1],
        )
        obs_groups = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
        self.policy = ActorCriticEncoder(
            obs=dummy_obs,
            obs_groups=obs_groups,
            num_actions=8,
            policy_obs_dim=cfg.policy_obs_dim,
            privileged_dim=cfg.privileged_dim,
            encoder_hidden_dims=(256, 128, 64),
            encoder_latent_dim=cfg.latent_dim,
            encoder_activation="elu",
            encoder_obs_normalization=False,
            encoder_obs_lower=_PRIV_OBS_LOWER,
            encoder_obs_upper=_PRIV_OBS_UPPER,
            encoder_output_norm=True,
            actor_obs_normalization=True,
            critic_obs_normalization=False,
            actor_hidden_dims=(256, 128, 64),
            critic_hidden_dims=(512, 256, 128),
            activation="elu",
            init_noise_std=0.7,
            critic_uses_z=True,
            num_constraints=10,
            cost_critic_hidden_dims=(512, 256, 128),
        )
        self.policy.to(device)

        # Load r13_A state dict.
        # Note: ActorCriticEncoder.load_state_dict() is overridden to return bool
        # (RSL-RL API contract). We call nn.Module.load_state_dict directly to
        # get the standard (missing_keys, unexpected_keys) NamedTuple.
        ckpt_path = os.path.join(cfg.teacher_run_dir, cfg.teacher_checkpoint)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        result = nn.Module.load_state_dict(self.policy, ckpt["model_state_dict"], strict=False)
        missing = result.missing_keys
        unexpected = result.unexpected_keys
        logger.info(
            "Loaded teacher from %s (iter=%s). Missing: %d, Unexpected: %d",
            ckpt_path,
            ckpt.get("iter", "?"),
            len(missing),
            len(unexpected),
        )
        if missing:
            logger.debug("Missing keys: %s", missing)
        if unexpected:
            logger.debug("Unexpected keys: %s", unexpected)

        # Freeze all teacher parameters
        for p in self.policy.parameters():
            p.requires_grad_(False)
        self.policy.eval()

        self.latent_dim = cfg.latent_dim
        self.obs_dim = cfg.policy_obs_dim
        self.privileged_dim = cfg.privileged_dim

    @torch.no_grad()
    def encode_privileged(self, privileged: torch.Tensor) -> torch.Tensor:
        """Ground-truth latent from privileged obs: (B, 27) -> (B, 9)."""
        from tensordict import TensorDict
        dummy = TensorDict(
            {
                "policy": torch.zeros(privileged.shape[0], self.obs_dim, device=privileged.device),
                "privileged": privileged,
            },
            batch_size=[privileged.shape[0]],
        )
        return self.policy._encode(dummy)

    def normalize_obs(self, obs: torch.Tensor) -> torch.Tensor:
        """Apply teacher's actor_obs_normalizer (frozen EmpiricalNorm)."""
        return self.policy.actor_obs_normalizer(obs)

    def actor_forward(self, obs_normed: torch.Tensor, latent: torch.Tensor) -> torch.Tensor:
        """Teacher actor forward: cat([normed obs, latent]) -> action.

        obs_normed: (B, 69) already through actor_obs_normalizer
        latent: (B, 9) -- either ground-truth l_t or student's l_hat
        Returns: (B, 8)
        """
        actor_in = torch.cat([obs_normed, latent], dim=-1)
        return self.policy.actor(actor_in)

    @torch.no_grad()
    def act(self, obs: torch.Tensor, privileged: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Produce teacher action + ground-truth latent (for env stepping + targets).

        Returns:
            a_t: (B, 8) teacher deterministic action
            l_t: (B, 9) teacher's ground-truth latent
        """
        from tensordict import TensorDict
        dummy = TensorDict({"policy": obs, "privileged": privileged}, batch_size=[obs.shape[0]])
        a_t = self.policy.act_inference(dummy)
        l_t = self.policy._encode(dummy)
        return a_t, l_t
