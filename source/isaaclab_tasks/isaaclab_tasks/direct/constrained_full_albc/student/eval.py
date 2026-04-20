"""Student-in-the-loop wrapper for eval_dr_fulldof.

Usage from a separate eval script:
    from isaaclab_tasks.direct.constrained_full_albc.student.eval import (
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
        self.student = make_student_encoder(cfg).to(device)
        # Load student weights
        blob = torch.load(student_ckpt, map_location=device, weights_only=False)
        self.student.load_state_dict(blob["student_state_dict"])
        self.student.eval()

        if cfg.encoder_type == "tcn":
            self.ring = torch.zeros(num_envs, cfg.tcn_history, cfg.policy_obs_dim, device=device)
            self.hidden = None
        else:
            self.ring = None
            self.hidden = self.student.init_hidden(num_envs, device)

    def reset(self, env_ids: torch.Tensor | None = None) -> None:
        """Clear history/hidden for the given envs (or all if None)."""
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
        """obs_td: tensordict with 'policy' key of shape (B, 87). Returns (B, 8)."""
        obs = obs_td["policy"]
        if self.cfg.encoder_type == "tcn":
            assert self.ring is not None
            # Push new obs onto ring
            self.ring = torch.roll(self.ring, shifts=1, dims=1)
            self.ring[:, 0] = obs
            l_hat = self.student(self.ring)
        else:
            # Single-step forward
            obs_seq = obs.unsqueeze(1)  # (B, 1, 87)
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
