"""Student-in-the-loop wrapper for eval_dr_fulldof.

Usage from a separate eval script:
    from constrained_albc.envs.constrained_full_albc.student.eval import (
        build_student_policy_fn,
    )

    policy_fn = build_student_policy_fn(
        teacher_ckpt="logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/model_4999.pt",
        student_ckpt="logs/rsl_rl/student_policy/.../models/student_999.pt",
        encoder_type="tcn",
        num_envs=64,
        device="cuda:0",
    )
    # policy_fn(obs_td) -> action (B, 8)
"""
from __future__ import annotations

import os

import torch

from .config import StudentCfg
from .models import make_student_encoder
from .teacher import FrozenTeacher


class StudentInLoopPolicy:
    """Callable policy that uses student encoder + teacher actor at inference time.

    Carries:
        - TCN: ring buffer of (num_envs, H, 87)
        - GRU: hidden state (num_layers, num_envs, hidden)

    Reset on `done` must be signaled via reset(env_ids).
    """

    def __init__(self, cfg: StudentCfg, student_ckpt: str, num_envs: int, device: torch.device) -> None:
        self.cfg = cfg
        self.device = device
        self.num_envs = num_envs

        self.teacher = FrozenTeacher(cfg, device=device)
        # Auto-infer architecture from checkpoint to avoid eval cfg mismatch
        # when students are trained with non-default architecture. Training
        # saves `cfg=vars(self.cfg)`; restore relevant fields for model build.
        blob = torch.load(student_ckpt, map_location=device, weights_only=False)
        sd = blob["student_state_dict"]
        saved_cfg = blob.get("cfg", {})
        if cfg.encoder_type == "gru":
            if "gru.weight_ih_l0" in sd:
                cfg.gru_hidden = sd["gru.weight_ih_l0"].shape[0] // 3
            # head.0.weight shape: (head_hidden, gru_hidden) for deep head,
            # (latent_dim, gru_hidden) for shallow head.
            if "head.0.weight" in sd:
                out_dim = sd["head.0.weight"].shape[0]
                cfg.gru_head_hidden = out_dim if out_dim != cfg.latent_dim else 0
        elif cfg.encoder_type == "tcn":
            for field in ("tcn_history", "tcn_input_channels", "tcn_conv_channels",
                           "tcn_conv_kernels", "tcn_conv_strides", "tcn_head_hidden"):
                if field in saved_cfg:
                    setattr(cfg, field, saved_cfg[field])
        self.student = make_student_encoder(cfg).to(device)
        # Load student weights
        self.student.load_state_dict(sd)
        self.student.eval()

        # Both TCN and GRU are trained on obs normalized by teacher's
        # actor_obs_normalizer; eval applies the same normalization for
        # train/eval consistency. TCN checkpoints predating this change
        # (trained on raw obs) are incompatible with this eval path.
        self.obs_normalizer = self.teacher.policy.actor_obs_normalizer

        if cfg.encoder_type == "tcn":
            self.ring = torch.zeros(num_envs, cfg.tcn_history, cfg.policy_obs_dim, device=device)
            self.hidden = None
        else:
            self.ring = None
            self.hidden = self.student.init_hidden(num_envs, device)

    def reset(self, env_ids: torch.Tensor | None = None) -> None:
        """Clear history/hidden for the given envs (or all if None).

        Accepts either: (1) None to reset all, (2) a long index tensor (N,), or
        (3) a bool mask of shape (num_envs,) or (num_envs, 1) -- the latter is
        what eval_dr_fulldof passes via `dones`.
        """
        if env_ids is not None:
            if env_ids.dtype == torch.bool:
                if env_ids.dim() > 1:
                    env_ids = env_ids.squeeze(-1)
                if not env_ids.any():
                    return
                env_ids = torch.nonzero(env_ids, as_tuple=False).squeeze(-1)

        if self.cfg.encoder_type == "tcn":
            assert self.ring is not None
            if env_ids is None:
                self.ring.zero_()
            else:
                self.ring[env_ids] = 0.0
        else:
            assert self.hidden is not None
            if env_ids is None:
                self.hidden.zero_()
            else:
                self.hidden[:, env_ids] = 0.0

    @torch.no_grad()
    def __call__(self, obs_td) -> torch.Tensor:
        """obs_td: tensordict with 'policy' key of shape (B, 87). Returns (B, 8).

        Time ordering (TCN): training window is [oldest @ idx 0, ..., newest @ idx H-1].
        The ring buffer MUST match this so Conv1d filters see the same temporal
        direction at train and eval. Previous version had newest at idx 0 — fixed.
        """
        obs = obs_td["policy"]
        if self.cfg.encoder_type == "tcn":
            assert self.ring is not None
            # Shift LEFT (drop oldest at idx 0) so newest obs lands at idx H-1.
            # Before: [o_{t-H+1}, o_{t-H+2}, ..., o_{t-1}, o_t]
            # After roll(shifts=-1): [o_{t-H+2}, ..., o_{t-1}, o_t, o_{t-H+1}]
            # Then ring[:, -1] = o_{t+1}: [o_{t-H+2}, ..., o_t, o_{t+1}]
            self.ring = torch.roll(self.ring, shifts=-1, dims=1)
            self.ring[:, -1] = obs
            # Normalize ring per-step to match training (runner._compute_loss_tcn).
            B, H, D = self.ring.shape
            ring_n = self.obs_normalizer(self.ring.reshape(B * H, D)).reshape(B, H, D)
            l_hat = self.student(ring_n)
        else:
            # Single-step forward. Normalize obs to match training distribution.
            obs_for_student = self.obs_normalizer(obs)
            obs_seq = obs_for_student.unsqueeze(1)  # (B, 1, 87)
            l_hat_seq, self.hidden = self.student(obs_seq, hidden=self.hidden)
            l_hat = l_hat_seq[:, -1]    # (B, 9)

        obs_normed = self.teacher.normalize_obs(obs)
        return self.teacher.actor_forward(obs_normed, l_hat)


def build_student_policy_fn(
    teacher_ckpt: str,
    student_ckpt: str,
    encoder_type: str,
    num_envs: int,
    device: str = "cuda:0",
) -> StudentInLoopPolicy:
    """Factory returning a callable policy."""
    cfg = StudentCfg()
    cfg.encoder_type = encoder_type
    cfg.teacher_run_dir = os.path.dirname(teacher_ckpt)
    cfg.teacher_checkpoint = os.path.basename(teacher_ckpt)
    return StudentInLoopPolicy(cfg, student_ckpt=student_ckpt, num_envs=num_envs, device=torch.device(device))
