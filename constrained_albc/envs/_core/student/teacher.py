# constrained_albc/envs/_core/student/teacher.py
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


def _infer_num_constraints(state_dict: dict, default: int = 10) -> int:
    """Read the teacher's constraint count from its cost_critic output head.

    cost_critic is an MLP whose final Linear layer has one row per constraint, so
    its weight shape is (num_constraints, hidden). The count varies across teachers
    (baseline=10, joint1-constraint Arm A/B=11), so we read it from the checkpoint
    rather than hardcode it. Picks the highest-index cost_critic.*.weight key (the
    output layer). Falls back to `default` if no cost_critic key is present.
    """
    weight_keys = [
        k for k in state_dict if k.startswith("cost_critic.") and k.endswith(".weight")
    ]
    if not weight_keys:
        return default
    # Highest numeric layer index = the output head.
    output_key = max(weight_keys, key=lambda k: int(k.split(".")[1]))
    return state_dict[output_key].shape[0]


def infer_teacher_geometry(state_dict: dict) -> dict:
    """Read the teacher's obs / privileged / latent widths off the checkpoint tensors.

    Same reasoning as _infer_num_constraints, extended to the dims that also vary
    across campaigns: the attitude-only teacher is 69D, and the same env with
    `use_bias_ema_obs` is 72D, while StudentCfg's defaults are fixed. Building the
    teacher from those defaults instead of the checkpoint raises a shape mismatch on
    load (actor.0.weight 256x78 vs 256x81, normalizer 1x69 vs 1x72), which is how
    distillation against a 72D teacher failed. The checkpoint is the single source
    of truth -- read the dims straight from its tensor shapes.
    """
    return {
        "policy_obs_dim": state_dict["actor_obs_normalizer._mean"].shape[1],  # (1, obs)
        "privileged_dim": state_dict["encoder.0.weight"].shape[1],            # (256, priv)
        "latent_dim": state_dict["_encoder_output_norm.weight"].shape[0],     # (latent,)
    }


class FrozenTeacher(nn.Module):
    """Wraps r13_A's ActorCriticEncoder; exposes encode(), normalize_obs(), actor_forward().

    Attributes:
        latent_dim / obs_dim / privileged_dim: from cfg (main 9/69/28,
        full_dof 9/87/24)
    """

    def __init__(self, cfg: StudentCfg, device: torch.device) -> None:
        super().__init__()
        self.cfg = cfg
        self.device = device

        # Build a teacher policy with the same arch as r13_A. We use the registry
        # class rather than instantiating ActorCriticEncoder directly to ensure
        # the exact arch (e.g. ALBCActorCriticEncoder overrides).
        # We don't have the real TensorDict here; instead we build bypassing obs_groups
        # by calling nn.Module construction of the components directly.
        # Easiest path: reuse ActorCriticEncoder via a minimal dummy obs dict.
        # Construct-time fallback bounds come from the teacher's variant package
        # (cfg.variant_module); the checkpoint load below overwrites persisted ones.
        import importlib

        from tensordict import TensorDict

        from ..encoder.actor_critic_encoder import ActorCriticEncoder

        _bounds_mod = importlib.import_module(f"{cfg.variant_module}.agents.rsl_rl_ppo_cfg")
        _PRIV_OBS_LOWER = _bounds_mod._PRIV_OBS_LOWER
        _PRIV_OBS_UPPER = _bounds_mod._PRIV_OBS_UPPER

        # The teacher's cost_critic has one output head per constraint. The count is
        # not fixed across teachers: the joint1-constraint campaign added an 11th
        # constraint, so a baseline teacher has 10 heads and an Arm-A/B teacher 11.
        # Read it from the checkpoint so any N-constraint teacher loads without a
        # shape mismatch (cost_critic itself is unused by distillation, but its
        # keys must match for state_dict loading).
        ckpt_path = os.path.join(cfg.teacher_run_dir, cfg.teacher_checkpoint)
        ckpt = torch.load(ckpt_path, map_location=device, weights_only=False)
        num_constraints = _infer_num_constraints(ckpt["model_state_dict"], default=10)
        geom = infer_teacher_geometry(ckpt["model_state_dict"])
        if geom["policy_obs_dim"] != cfg.policy_obs_dim:
            logger.info(
                "Teacher geometry from checkpoint overrides cfg: policy_obs_dim %d -> %d",
                cfg.policy_obs_dim, geom["policy_obs_dim"],
            )

        dummy_obs = TensorDict(
            {
                "policy": torch.zeros(1, geom["policy_obs_dim"]),
                "privileged": torch.zeros(1, geom["privileged_dim"]),
            },
            batch_size=[1],
        )
        obs_groups = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
        self.policy = ActorCriticEncoder(
            obs=dummy_obs,
            obs_groups=obs_groups,
            num_actions=8,
            policy_obs_dim=geom["policy_obs_dim"],
            privileged_dim=geom["privileged_dim"],
            encoder_hidden_dims=(256, 128, 64),
            encoder_latent_dim=geom["latent_dim"],
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
            num_constraints=num_constraints,
            cost_critic_hidden_dims=(512, 256, 128),
        )
        self.policy.to(device)

        # Load the teacher state dict (ckpt was already read above to size cost_critic).
        # Note: ActorCriticEncoder.load_state_dict() is overridden to return bool
        # (RSL-RL API contract). We call nn.Module.load_state_dict directly to
        # get the standard (missing_keys, unexpected_keys) NamedTuple.
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

        # Expose the geometry actually built (checkpoint-derived), not the cfg
        # defaults -- StudentRunner reads these back to size the student.
        self.latent_dim = geom["latent_dim"]
        self.obs_dim = geom["policy_obs_dim"]
        self.privileged_dim = geom["privileged_dim"]

    @torch.no_grad()
    def encode_privileged(self, privileged: torch.Tensor) -> torch.Tensor:
        """Ground-truth latent from privileged obs: (B, privileged_dim) -> (B, latent_dim)."""
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

        obs_normed: (B, obs_dim) already through actor_obs_normalizer
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
