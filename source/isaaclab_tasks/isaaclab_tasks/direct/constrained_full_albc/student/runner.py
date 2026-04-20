# source/isaaclab_tasks/isaaclab_tasks/direct/constrained_full_albc/student/runner.py
"""Supervised training loop for the student encoder.

Each iteration:
    1. Collect n_steps rollout (teacher drives env; record (obs, priv, l_t, a_t, dones)).
    2. Compute l_hat via student encoder (TCN window or GRU sequence).
    3. Compute a_hat via frozen teacher actor(normalize(obs_t), l_hat).
    4. Loss = ||a_hat - a_t||^2 + lambda * ||l_hat - l_t||^2.
    5. Adam step on student params only.

Logging: TensorBoard + optional WandB. Checkpoints every save_interval iters.
"""
from __future__ import annotations

import logging
import os
import time

import torch
import torch.nn.functional as F
from torch.utils.tensorboard import SummaryWriter

from .collector import RolloutBuffer
from .config import StudentCfg
from .models import make_student_encoder
from .teacher import FrozenTeacher

logger = logging.getLogger(__name__)

try:
    import wandb
    _HAS_WANDB = True
except ImportError:
    _HAS_WANDB = False


def configure_env_for_student(env) -> None:
    """Disable DORAEMON and force HardDR on the env before learning starts.

    Per spec section 4: student training uses r14 aggressive HardDR uniformly
    and disables DORAEMON's Beta curriculum.
    """
    env_cfg = env.unwrapped.cfg
    doraemon_cfg = getattr(env_cfg, "doraemon", None)
    if doraemon_cfg is not None and getattr(doraemon_cfg, "enable", False):
        doraemon_cfg.enable = False
        logger.info("[Student] DORAEMON disabled for supervised training.")

    # Replace randomization cfg with HardDomainRandomizationCfg instance
    from isaaclab_tasks.direct.constrained_full_albc.config import HardDomainRandomizationCfg
    hard = HardDomainRandomizationCfg()
    env_cfg.randomization = hard
    logger.info("[Student] Randomization forced to HardDomainRandomizationCfg.")

    # Re-initialize env internals that cache randomization ranges.
    if hasattr(env.unwrapped, "_reload_randomization"):
        env.unwrapped._reload_randomization()
    else:
        # Fallback: full env re-init happens on next reset. The existing DR sampler
        # reads env_cfg.randomization at reset time, so a reset is sufficient.
        pass


class StudentRunner:
    """Drives rollout collection + supervised optimization."""

    def __init__(self, env, cfg: StudentCfg, log_dir: str, device: torch.device) -> None:
        self.env = env
        self.cfg = cfg
        self.log_dir = log_dir
        self.device = device

        # Configure env before any rollout: HardDR on, DORAEMON off.
        configure_env_for_student(env)

        self.teacher = FrozenTeacher(cfg, device=device)
        self.student = make_student_encoder(cfg).to(device)

        self.optimizer = torch.optim.Adam(self.student.parameters(), lr=cfg.lr)

        self.buffer = RolloutBuffer(cfg, device=device)

        self.writer = SummaryWriter(log_dir=log_dir)
        self.use_wandb = cfg.logger == "wandb" and _HAS_WANDB
        if self.use_wandb:
            wandb.init(
                project=cfg.wandb_project,
                name=os.path.basename(log_dir),
                config=vars(cfg),
                dir=log_dir,
            )

        # GRU hidden state carried across rollout steps
        if cfg.encoder_type == "gru":
            self.gru_hidden = self.student.init_hidden(cfg.num_envs, device)
        else:
            self.gru_hidden = None

        os.makedirs(os.path.join(log_dir, "models"), exist_ok=True)
        logger.info("StudentRunner initialized: encoder=%s log_dir=%s", cfg.encoder_type, log_dir)

    def _collect_rollout(self, obs: torch.Tensor, privileged: torch.Tensor) -> tuple[torch.Tensor, torch.Tensor]:
        """Run n_steps env steps with teacher actions, filling the buffer.

        Returns the final (obs, privileged) so the caller can carry state.
        """
        self.buffer.reset()
        for _ in range(self.cfg.n_steps_per_rollout):
            # Teacher acts from current obs+privileged
            a_t, l_t = self.teacher.act(obs, privileged)

            # Step env with teacher action
            obs_next, _rew, dones, extras = self.env.step(a_t)
            privileged_next = obs_next["privileged"]
            obs_next_policy = obs_next["policy"]

            # Record at the step AFTER dones/reset processing. The "dones" indicate
            # which envs were reset between previous step and this new obs.
            self.buffer.add(obs_next_policy, privileged_next, l_t.detach(), a_t.detach(), dones.to(torch.bool))

            # GRU hidden state: zero out for reset envs so the next forward pass
            # starts fresh for them.
            if self.gru_hidden is not None and dones.any():
                reset_ids = torch.nonzero(dones).squeeze(-1)
                self.gru_hidden[:, reset_ids] = 0.0

            obs = obs_next_policy
            privileged = privileged_next

        return obs, privileged

    def _compute_loss_tcn(self, batch) -> dict[str, torch.Tensor]:
        l_hat = self.student(batch.obs_window)           # (M, 9)
        obs_normed = self.teacher.normalize_obs(batch.obs_t)
        a_hat = self.teacher.actor_forward(obs_normed, l_hat)  # (M, 8)
        loss_action = F.mse_loss(a_hat, batch.a_t)
        loss_latent = F.mse_loss(l_hat, batch.l_t)
        total = loss_action + self.cfg.lambda_latent * loss_latent
        return {"loss_total": total, "loss_action": loss_action, "loss_latent": loss_latent}

    def _compute_loss_gru(self, batch) -> dict[str, torch.Tensor]:
        # Forward over sequence; ignore hidden state from training chunks (we
        # treat each chunk as an independent BPTT unit for simplicity).
        l_hat_seq, _ = self.student(batch.obs_seq, hidden=None)         # (envs, T, 9)
        M = l_hat_seq.shape[0] * l_hat_seq.shape[1]
        l_hat = l_hat_seq.reshape(M, -1)
        obs_normed = self.teacher.normalize_obs(batch.obs_t)
        a_hat = self.teacher.actor_forward(obs_normed, l_hat)
        loss_action = F.mse_loss(a_hat, batch.a_t)
        loss_latent = F.mse_loss(l_hat, batch.l_t)
        total = loss_action + self.cfg.lambda_latent * loss_latent
        return {"loss_total": total, "loss_action": loss_action, "loss_latent": loss_latent}

    def _log(self, iter_idx: int, metrics: dict[str, float]) -> None:
        for k, v in metrics.items():
            self.writer.add_scalar(k, v, iter_idx)
        if self.use_wandb:
            wandb.log(metrics, step=iter_idx)

    def _save_checkpoint(self, iter_idx: int) -> None:
        path = os.path.join(self.log_dir, "models", f"student_{iter_idx}.pt")
        torch.save({"iter": iter_idx, "student_state_dict": self.student.state_dict(), "cfg": vars(self.cfg)}, path)
        logger.info("Saved student checkpoint: %s", path)

    def learn(self) -> None:
        # Reset env once at the start
        obs_td, _extras = self.env.reset()
        obs = obs_td["policy"]
        privileged = obs_td["privileged"]

        t_start = time.time()
        for it in range(self.cfg.max_iterations):
            # Collect
            t0 = time.time()
            obs, privileged = self._collect_rollout(obs, privileged)
            t_collect = time.time() - t0

            # Train
            t0 = time.time()
            epoch_totals = {"loss_total": 0.0, "loss_action": 0.0, "loss_latent": 0.0, "grad_norm": 0.0}
            n_updates = 0
            for _ in range(self.cfg.n_epochs):
                if self.cfg.encoder_type == "tcn":
                    batches = self.buffer.iter_minibatches_tcn()
                else:
                    batches = self.buffer.iter_minibatches_gru()
                for batch in batches:
                    if self.cfg.encoder_type == "tcn":
                        losses = self._compute_loss_tcn(batch)
                    else:
                        losses = self._compute_loss_gru(batch)
                    self.optimizer.zero_grad()
                    losses["loss_total"].backward()
                    grad_norm = torch.nn.utils.clip_grad_norm_(
                        self.student.parameters(), self.cfg.grad_clip_norm
                    )
                    self.optimizer.step()
                    for k in ("loss_total", "loss_action", "loss_latent"):
                        epoch_totals[k] += losses[k].item()
                    epoch_totals["grad_norm"] += float(grad_norm)
                    n_updates += 1
            for k in epoch_totals:
                epoch_totals[k] /= max(1, n_updates)
            t_train = time.time() - t0

            # Log
            metrics = {
                "student/loss_total": epoch_totals["loss_total"],
                "student/loss_action": epoch_totals["loss_action"],
                "student/loss_latent": epoch_totals["loss_latent"],
                "student/grad_norm": epoch_totals["grad_norm"],
                "student/time_collect": t_collect,
                "student/time_train": t_train,
                "student/iter": it,
            }
            self._log(it, metrics)

            if it % 10 == 0:
                logger.info(
                    "iter=%d total=%.4f action=%.4f latent=%.4f grad=%.3f t_c=%.2fs t_t=%.2fs",
                    it,
                    metrics["student/loss_total"],
                    metrics["student/loss_action"],
                    metrics["student/loss_latent"],
                    metrics["student/grad_norm"],
                    t_collect,
                    t_train,
                )

            if (it + 1) % self.cfg.save_interval == 0 or it == self.cfg.max_iterations - 1:
                self._save_checkpoint(it)

        logger.info("Training done. Total time: %.1f min.", (time.time() - t_start) / 60.0)
        if self.use_wandb:
            wandb.finish()
        self.writer.close()
