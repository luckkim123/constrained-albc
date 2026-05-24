# constrained_albc/envs/constrained_full_albc/student/models.py
"""Student encoder architectures: window-based TCN and streaming GRU.

Both output 9D latent in (-1, 1) via softsign, matching r13_A teacher's
privileged encoder output range so latent L2 loss is well-scaled.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import StudentCfg


class StudentEncoderTCN(nn.Module):
    """Window-based temporal conv encoder.

    Input:  (B, H, D) where H=50, D=87
    Output: (B, latent_dim) in (-1, 1)
    """

    def __init__(self, cfg: StudentCfg) -> None:
        super().__init__()
        self.cfg = cfg
        self.history_len = cfg.tcn_history

        # Per-step channel transform: maps raw 87D features -> tcn_input_channels
        self.channel_transform = nn.Sequential(
            nn.Linear(cfg.policy_obs_dim, cfg.tcn_input_channels),
            nn.ELU(),
        )

        # 1D conv stack.
        in_ch = cfg.tcn_input_channels
        convs: list[nn.Module] = []
        seq_len = cfg.tcn_history
        for out_ch, k, s in zip(cfg.tcn_conv_channels, cfg.tcn_conv_kernels, cfg.tcn_conv_strides):
            convs.append(nn.Conv1d(in_ch, out_ch, kernel_size=k, stride=s))
            convs.append(nn.ELU())
            seq_len = (seq_len - k) // s + 1
            in_ch = out_ch
        self.conv = nn.Sequential(*convs)
        self.flatten_dim = in_ch * seq_len

        # Head
        self.head = nn.Sequential(
            nn.Linear(self.flatten_dim, cfg.tcn_head_hidden),
            nn.ELU(),
            nn.LayerNorm(cfg.tcn_head_hidden),
            nn.Linear(cfg.tcn_head_hidden, cfg.latent_dim),
        )

    def forward(self, obs_window: torch.Tensor) -> torch.Tensor:
        """obs_window: (B, H, D) -> l_hat: (B, latent_dim)."""
        b, h, d = obs_window.shape
        # Apply channel transform per timestep: (B, H, D) -> (B, H, C)
        x = self.channel_transform(obs_window.reshape(b * h, d)).reshape(b, h, -1)
        # Transpose for Conv1d: (B, H, C) -> (B, C, H)
        x = x.transpose(1, 2)
        x = self.conv(x)
        # Flatten time + channels
        x = x.reshape(b, -1)
        z = self.head(x)
        return F.softsign(z)


class StudentEncoderGRU(nn.Module):
    """Streaming GRU encoder.

    Uses GRU (not GRUCell) for efficient training over temporal chunks.
    For single-step inference, pass (B, 1, D) and carry hidden across calls.
    """

    def __init__(self, cfg: StudentCfg) -> None:
        super().__init__()
        self.cfg = cfg
        self.gru = nn.GRU(
            input_size=cfg.policy_obs_dim,
            hidden_size=cfg.gru_hidden,
            num_layers=cfg.gru_layers,
            batch_first=True,
        )
        # Deeper head optional (matches teacher's 128->64->9 pattern). When
        # gru_head_hidden == 0, fall back to the original shallow head.
        # No LN on the 9D output: verified diagnostic showed per-sample LN(9)
        # collapses student std to 0.001-0.03 vs teacher 0.17-0.48, while TCN
        # (no output LN) matches teacher std range.
        head_h = getattr(cfg, "gru_head_hidden", 0)
        if head_h and head_h > 0:
            self.head = nn.Sequential(
                nn.Linear(cfg.gru_hidden, head_h),
                nn.ELU(),
                nn.LayerNorm(head_h),
                nn.Linear(head_h, cfg.latent_dim),
            )
        else:
            self.head = nn.Sequential(
                nn.Linear(cfg.gru_hidden, cfg.latent_dim),
            )

    def forward(
        self,
        obs_seq: torch.Tensor,
        hidden: torch.Tensor | None = None,
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """obs_seq: (B, T, D), hidden: (num_layers, B, gru_hidden) or None.

        Returns:
            l_hat: (B, T, latent_dim) -- all timesteps
            hidden: (num_layers, B, gru_hidden) -- final hidden state
        """
        out, hidden_out = self.gru(obs_seq, hidden)
        z = self.head(out)
        return F.softsign(z), hidden_out

    def init_hidden(self, batch_size: int, device: torch.device) -> torch.Tensor:
        return torch.zeros(self.cfg.gru_layers, batch_size, self.cfg.gru_hidden, device=device)


def make_student_encoder(cfg: StudentCfg) -> nn.Module:
    """Factory."""
    if cfg.encoder_type == "tcn":
        return StudentEncoderTCN(cfg)
    if cfg.encoder_type == "gru":
        return StudentEncoderGRU(cfg)
    raise ValueError(f"Unknown encoder_type: {cfg.encoder_type}")
