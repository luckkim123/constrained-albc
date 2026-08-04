# constrained_albc/envs/_core/student/models.py
"""Student encoder architectures: window-based TCN and streaming GRU.

Both output 9D latent in (-1, 1) via softsign, matching r13_A teacher's
privileged encoder output range so latent L2 loss is well-scaled.
"""
from __future__ import annotations

import torch
import torch.nn as nn
import torch.nn.functional as F

from .config import StudentCfg

# Single source of truth for the obs-dict key the env publishes the 4 extra sensor
# channels under. Producer (envs/main/albc_env.py) and consumers (this package's
# runner.py, analysis/student_policy.py) all import this instead of repeating the
# string literal -- a rename in one place used to be caught by nothing (fix-wave
# 2026-08-03, minor item 7).
STUDENT_EXTRA_OBS_KEY = "student_extra"

# Width of the extra-channel block the gen-2 env folds at the policy_obs TAIL
# (apply_extra_policy_obs, envs/main/config.py): IMU specific force 3D + heave rate 1D.
# The env always emits exactly 4; train_student.py's cross-check states the same fact.
POLICY_TAIL_N = 4


def split_policy_tail(
    *, obs_raw: torch.Tensor, obs_n: torch.Tensor, n_tail: int
) -> tuple[torch.Tensor, torch.Tensor]:
    """Recover the gen-1 (normalized core, RAW extra) pair from a gen-2 policy_obs.

    X1-tailsplit: the gen-2 env appends the extra channels at the TAIL of policy_obs,
    and the teacher's actor_obs_normalizer is elementwise, so slicing the normalized
    stream at -n_tail equals normalizing the core alone. The tail is taken from the RAW
    obs so student_input applies the gen-1 static per-channel scale instead of the
    teacher's z-score statistics -- that normalization mode is the ONE experimental
    variable X1 isolates. Feed the result to student_input; the input layout stays
    defined in exactly one place. Shapes: obs_raw/obs_n (..., D) -> ((..., D-n), (..., n)).
    Keyword-only: the two tensor args have identical shapes, so a positional swap would
    silently return a z-scored tail -- the exact convention this helper exists to avoid.
    """
    return obs_n[..., :-n_tail], obs_raw[..., -n_tail:]


def student_input(
    obs_n: torch.Tensor, extra: torch.Tensor | None, scale: torch.Tensor | None
) -> torch.Tensor:
    """THE definition of the student encoder's input layout: [obs_n, extra / scale].

    Every encoder forward in the codebase -- DAgger collection, training loss,
    end-of-rollout hidden recompute, and eval in-loop inference -- calls this. Do not
    inline the concat at a call site: an eval-side copy of a training-side forward is
    exactly how 38d979e silently invalidated every in-loop verdict for two months.
    Shapes: obs_n (..., D), extra (..., E), scale (E,) -> (..., D + E).
    """
    if scale is None:
        return obs_n
    if extra is None:
        raise ValueError("student_input: extra_obs_dim > 0 but extra is None")
    return torch.cat([obs_n, extra / scale], dim=-1)


def extra_scale_tensor(cfg, device) -> torch.Tensor | None:
    """Per-channel scale tensor for the extra sensor channels, or None when off.

    One definition shared by the runner and by eval's StudentInLoopPolicy -- the same
    reason student_input exists. The length check turns a silent truncation into a
    named error: a short extra_obs_scale would otherwise slice quietly and surface as
    an opaque broadcast failure at the first forward.
    """
    n = getattr(cfg, "extra_obs_dim", 0)
    tail = getattr(cfg, "extra_obs_from_policy_tail", False)
    if n > 0 and tail:
        raise ValueError(
            "extra_obs_dim > 0 and extra_obs_from_policy_tail are mutually exclusive "
            "delivery conventions (gen-1 side channel vs X1 policy-tail split)"
        )
    if tail:
        n = POLICY_TAIL_N
    if n <= 0:
        return None
    scale = cfg.extra_obs_scale
    if len(scale) < n:
        raise ValueError(
            f"extra_obs_scale has {len(scale)} entries but extra_obs_dim is {n}"
        )
    return torch.tensor(scale[:n], device=device)


class StudentEncoderTCN(nn.Module):
    """Window-based temporal conv encoder.

    Input:  (B, H, D) where H=tcn_history (9), D=policy_obs_dim (69 main / 87 full_dof)
    Output: (B, latent_dim) in (-1, 1)
    """

    def __init__(self, cfg: StudentCfg) -> None:
        super().__init__()
        self.cfg = cfg
        self.history_len = cfg.tcn_history

        # Per-step channel transform: maps raw policy-obs features -> tcn_input_channels
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
        extra = getattr(cfg, "extra_obs_dim", 0)
        self.gru = nn.GRU(
            input_size=cfg.policy_obs_dim + extra,
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
    if getattr(cfg, "extra_obs_dim", 0) > 0 and cfg.encoder_type != "gru":
        raise ValueError(
            "extra_obs_dim > 0 is implemented for the GRU student only "
            "(TCN flat-buf/ring were deliberately not widened -- see StudentCfg)"
        )
    if getattr(cfg, "extra_obs_from_policy_tail", False) and cfg.encoder_type != "gru":
        raise ValueError(
            "extra_obs_from_policy_tail is implemented for the GRU student only "
            "(the TCN forward never routes through student_input, so tail mode "
            "would be a silent no-op there -- see test_student_extra_parity.py)"
        )
    if cfg.encoder_type == "tcn":
        return StudentEncoderTCN(cfg)
    if cfg.encoder_type == "gru":
        return StudentEncoderGRU(cfg)
    raise ValueError(f"Unknown encoder_type: {cfg.encoder_type}")
