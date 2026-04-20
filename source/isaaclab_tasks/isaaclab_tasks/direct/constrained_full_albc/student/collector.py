"""Online rollout collection for student training.

During an iteration we:
    1. Run N env steps with teacher actions (so data distribution matches r13_A's).
    2. Record (obs_t, privileged_t, l_t, a_t) plus, for the TCN student, a sliding
       H-step window of obs; for the GRU student, (obs_t, done_t) and carry hidden.
    3. Flatten (num_envs, N) -> (num_envs*N,) minibatches for SGD.

Buffer memory is proportional to num_envs * n_steps * obs_dim and is released
after each iteration.
"""
from __future__ import annotations

from dataclasses import dataclass

import torch

from .config import StudentCfg


@dataclass
class RolloutBatch:
    """Flat minibatch of training samples."""
    obs_window: torch.Tensor | None   # (M, H, 87) for TCN, None for GRU
    obs_seq: torch.Tensor | None      # (M_envs, T, 87) for GRU chunks, None for TCN
    dones_seq: torch.Tensor | None    # (M_envs, T) for GRU chunks
    obs_t: torch.Tensor               # (M, 87) -- the "current" obs used by teacher actor
    l_t: torch.Tensor                 # (M, 9)
    a_t: torch.Tensor                 # (M, 8)


class RolloutBuffer:
    """Stores one iteration of rollout data.

    For TCN: keeps a per-env ring buffer of H past obs + flat tensors of current step.
    For GRU: keeps sequential (obs, done) per env across the rollout.
    """

    def __init__(self, cfg: StudentCfg, device: torch.device) -> None:
        self.cfg = cfg
        self.device = device
        self.num_envs = cfg.num_envs
        self.n_steps = cfg.n_steps_per_rollout

        # Per-env ring buffer for TCN windowing. Zero-padded at episode reset.
        self.ring = torch.zeros(self.num_envs, cfg.tcn_history, cfg.policy_obs_dim, device=device)
        self.ring_idx = 0  # newest slot index (wraps)

        # Flat tensors filled during rollout
        self.obs_flat = torch.zeros(self.n_steps, self.num_envs, cfg.policy_obs_dim, device=device)
        self.obs_window_flat = torch.zeros(
            self.n_steps, self.num_envs, cfg.tcn_history, cfg.policy_obs_dim, device=device
        )
        self.priv_flat = torch.zeros(self.n_steps, self.num_envs, cfg.privileged_dim, device=device)
        self.l_gt_flat = torch.zeros(self.n_steps, self.num_envs, cfg.latent_dim, device=device)
        self.a_gt_flat = torch.zeros(self.n_steps, self.num_envs, 8, device=device)
        self.done_flat = torch.zeros(self.n_steps, self.num_envs, dtype=torch.bool, device=device)

        self.ptr = 0

    def reset_env(self, env_ids: torch.Tensor) -> None:
        """Clear ring buffer for reset envs (zero-padding)."""
        self.ring[env_ids] = 0.0

    def add(
        self,
        obs: torch.Tensor,          # (num_envs, 87)
        privileged: torch.Tensor,   # (num_envs, 24)
        l_t: torch.Tensor,          # (num_envs, 9)
        a_t: torch.Tensor,          # (num_envs, 8)
        dones: torch.Tensor,        # (num_envs,) bool, from the PREVIOUS env step
    ) -> None:
        """Add one timestep and update the windowed ring buffer.

        Ordering:
            1. If dones from previous step, zero-out those envs' ring (pre-step reset).
            2. Push new obs onto ring.
            3. Snapshot the full window into obs_window_flat[ptr].
        """
        # Zero out resetted envs' ring first
        if dones.any():
            self.reset_env(torch.nonzero(dones).squeeze(-1))

        # Shift ring and insert newest obs at position 0.
        # Ring layout: ring[:, 0] = most recent, ring[:, H-1] = oldest.
        self.ring = torch.roll(self.ring, shifts=1, dims=1)
        self.ring[:, 0] = obs

        # Snapshot
        self.obs_flat[self.ptr] = obs
        self.obs_window_flat[self.ptr] = self.ring.clone()
        self.priv_flat[self.ptr] = privileged
        self.l_gt_flat[self.ptr] = l_t
        self.a_gt_flat[self.ptr] = a_t
        self.done_flat[self.ptr] = dones
        self.ptr += 1

    def iter_minibatches_tcn(self) -> list[RolloutBatch]:
        """Flatten (T, E, ...) -> (T*E, ...) and shuffle into minibatches for TCN."""
        obs_flat = self.obs_flat[: self.ptr].reshape(-1, self.cfg.policy_obs_dim)
        win_flat = self.obs_window_flat[: self.ptr].reshape(
            -1, self.cfg.tcn_history, self.cfg.policy_obs_dim
        )
        l_flat = self.l_gt_flat[: self.ptr].reshape(-1, self.cfg.latent_dim)
        a_flat = self.a_gt_flat[: self.ptr].reshape(-1, 8)

        N = obs_flat.shape[0]
        perm = torch.randperm(N, device=self.device)
        batches = []
        for start in range(0, N, self.cfg.minibatch_size):
            idx = perm[start : start + self.cfg.minibatch_size]
            batches.append(
                RolloutBatch(
                    obs_window=win_flat[idx],
                    obs_seq=None,
                    dones_seq=None,
                    obs_t=obs_flat[idx],
                    l_t=l_flat[idx],
                    a_t=a_flat[idx],
                )
            )
        return batches

    def iter_minibatches_gru(self) -> list[RolloutBatch]:
        """For GRU we keep sequential chunks to enable BPTT.

        Layout: slice envs into groups of size M_envs = minibatch_size // n_steps,
        yielding (M_envs, T) sequences with their done mask.
        """
        T = self.ptr
        E = self.num_envs
        envs_per_batch = max(1, self.cfg.minibatch_size // T)
        perm = torch.randperm(E, device=self.device)
        batches = []
        for start in range(0, E, envs_per_batch):
            idx = perm[start : start + envs_per_batch]
            batches.append(
                RolloutBatch(
                    obs_window=None,
                    obs_seq=self.obs_flat[:T, idx].transpose(0, 1),      # (envs, T, 87)
                    dones_seq=self.done_flat[:T, idx].transpose(0, 1),   # (envs, T)
                    obs_t=self.obs_flat[:T, idx].reshape(-1, self.cfg.policy_obs_dim),
                    l_t=self.l_gt_flat[:T, idx].reshape(-1, self.cfg.latent_dim),
                    a_t=self.a_gt_flat[:T, idx].reshape(-1, 8),
                )
            )
        return batches

    def reset(self) -> None:
        self.ptr = 0
