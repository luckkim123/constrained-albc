"""Online rollout collection for student training.

Memory-compact design:
    - One flat buffer (H + n_steps, num_envs, D) is the only "history" storage.
      Old design stored an (n_steps, num_envs, H, D) window snapshot per rollout
      step, which duplicated each obs up to H times and allocated 1.7 GB at
      num_envs=4096 (killing training on 8 GB GPUs).
    - TCN windows are materialized lazily at minibatch time via gather.
    - GRU path does not need the flat_buf at all, so it is only allocated when
      encoder_type == "tcn".

Episode reset handling: when env e is done at step t, we zero flat_buf[0:H+t, e]
so windows for this step (and the next H-1 steps) do not mix pre- and post-reset
observations.
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
    # GRU-only: env indices for this minibatch, used to slice the persisted
    # hidden state at rollout start. None for TCN batches.
    env_idx: torch.Tensor | None = None


class RolloutBuffer:
    """Stores one iteration of rollout data.

    TCN path: keeps a flat (H + n_steps, num_envs, D) buffer; builds windows on
              demand at minibatch time via advanced indexing.
    GRU path: only the flat per-step tensors; no flat_buf needed.
    """

    def __init__(self, cfg: StudentCfg, device: torch.device) -> None:
        self.cfg = cfg
        self.device = device
        self.num_envs = cfg.num_envs
        self.n_steps = cfg.n_steps_per_rollout
        self.H = cfg.tcn_history
        self.D = cfg.policy_obs_dim
        self._is_tcn = cfg.encoder_type == "tcn"

        # TCN-only flat buffer: H pre-rollout slots + n_steps rollout slots.
        # Layout: flat_buf[0:H] = pre-rollout history, flat_buf[H+t] = obs at rollout step t.
        # Window for rollout step t is flat_buf[t+1 : t+1+H], shape (H, num_envs, D).
        if self._is_tcn:
            self.flat_buf: torch.Tensor | None = torch.zeros(
                self.H + self.n_steps, self.num_envs, self.D, device=device
            )
        else:
            self.flat_buf = None

        # Per-step compact tensors (both TCN and GRU)
        self.obs_flat = torch.zeros(self.n_steps, self.num_envs, self.D, device=device)
        self.priv_flat = torch.zeros(self.n_steps, self.num_envs, cfg.privileged_dim, device=device)
        self.l_gt_flat = torch.zeros(self.n_steps, self.num_envs, cfg.latent_dim, device=device)
        self.a_gt_flat = torch.zeros(self.n_steps, self.num_envs, 8, device=device)
        self.done_flat = torch.zeros(self.n_steps, self.num_envs, dtype=torch.bool, device=device)

        self.step_idx = 0

    def add(
        self,
        obs: torch.Tensor,          # (num_envs, D)
        privileged: torch.Tensor,   # (num_envs, priv_dim)
        l_t: torch.Tensor,          # (num_envs, latent_dim)
        a_t: torch.Tensor,          # (num_envs, 8)
        dones: torch.Tensor,        # (num_envs,) bool, from the PREVIOUS env step
    ) -> None:
        """Add one timestep.

        For TCN: write obs to flat_buf[H + step_idx]; zero flat_buf[:H+step_idx]
        for any env that just reset so its window stops at the new episode boundary.
        """
        if self._is_tcn and self.flat_buf is not None:
            if dones.any():
                reset_ids = torch.nonzero(dones).squeeze(-1)
                # Zero all past positions for reset envs.
                self.flat_buf[: self.H + self.step_idx, reset_ids] = 0.0
            self.flat_buf[self.H + self.step_idx] = obs

        self.obs_flat[self.step_idx] = obs
        self.priv_flat[self.step_idx] = privileged
        self.l_gt_flat[self.step_idx] = l_t
        self.a_gt_flat[self.step_idx] = a_t
        self.done_flat[self.step_idx] = dones
        self.step_idx += 1

    def carry_over_history(self) -> None:
        """Slide the last H rollout slots into the pre-rollout region.

        Called at the end of an iteration so the next rollout's first windows
        contain real history (not zeros). TCN only.
        """
        if self._is_tcn and self.flat_buf is not None:
            self.flat_buf[: self.H] = self.flat_buf[-self.H :].clone()

    def reset(self) -> None:
        """Reset the rollout step counter; call between iterations."""
        self.step_idx = 0

    def iter_minibatches_tcn(self) -> list[RolloutBatch]:
        """Shuffle (t, env) pairs and yield minibatches with lazy window materialization.

        Memory per batch: minibatch_size * H * D floats (~143 MB for 8192*50*87*4B).
        """
        assert self._is_tcn and self.flat_buf is not None, "iter_minibatches_tcn called on non-TCN buffer"

        T = self.step_idx
        E = self.num_envs
        H = self.H

        obs_flat = self.obs_flat[:T].reshape(-1, self.D)
        l_flat = self.l_gt_flat[:T].reshape(-1, self.cfg.latent_dim)
        a_flat = self.a_gt_flat[:T].reshape(-1, 8)

        N = T * E
        perm = torch.randperm(N, device=self.device)

        offsets = torch.arange(H, device=self.device)  # (H,)

        batches: list[RolloutBatch] = []
        for start in range(0, N, self.cfg.minibatch_size):
            idx = perm[start : start + self.cfg.minibatch_size]  # (M,)
            t_idx = idx // E  # rollout step per sample, (M,)
            e_idx = idx % E   # env per sample, (M,)
            # Window positions: flat_buf[t+1 : t+1+H, env] -> (M, H, D)
            pos = t_idx.unsqueeze(-1) + 1 + offsets.unsqueeze(0)  # (M, H)
            e_expanded = e_idx.unsqueeze(-1).expand(-1, H)        # (M, H)
            obs_window = self.flat_buf[pos, e_expanded]           # (M, H, D) gather

            batches.append(
                RolloutBatch(
                    obs_window=obs_window,
                    obs_seq=None,
                    dones_seq=None,
                    obs_t=obs_flat[idx],
                    l_t=l_flat[idx],
                    a_t=a_flat[idx],
                )
            )
        return batches

    def iter_minibatches_gru(self) -> list[RolloutBatch]:
        """Sequential chunks per env for BPTT.

        Layout: slice envs into groups of size M_envs = minibatch_size // n_steps,
        yielding (M_envs, T) sequences with their done mask.
        """
        T = self.step_idx
        E = self.num_envs
        envs_per_batch = max(1, self.cfg.minibatch_size // T)
        perm = torch.randperm(E, device=self.device)
        batches: list[RolloutBatch] = []
        for start in range(0, E, envs_per_batch):
            idx = perm[start : start + envs_per_batch]
            batches.append(
                RolloutBatch(
                    obs_window=None,
                    obs_seq=self.obs_flat[:T, idx].transpose(0, 1),      # (envs, T, D)
                    dones_seq=self.done_flat[:T, idx].transpose(0, 1),   # (envs, T)
                    obs_t=self.obs_flat[:T, idx].reshape(-1, self.D),
                    l_t=self.l_gt_flat[:T, idx].reshape(-1, self.cfg.latent_dim),
                    a_t=self.a_gt_flat[:T, idx].reshape(-1, 8),
                    env_idx=idx,
                )
            )
        return batches
