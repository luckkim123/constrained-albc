# constrained_albc/envs/_core/student/runner.py
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
from .config import StudentCfg, dagger_beta_at
from .models import make_student_encoder
from .teacher import FrozenTeacher

logger = logging.getLogger(__name__)

try:
    import wandb
    _HAS_WANDB = True
except ImportError:
    _HAS_WANDB = False


def configure_env_for_student(env) -> None:
    """Disable DORAEMON and force static hard DR on the env before learning starts.

    Student training uses the r13_A-era DomainRandomizationCfg (hard training
    ranges) uniformly and disables DORAEMON's Beta curriculum so the teacher is
    never queried outside the DR region it was trained on.
    """
    env_cfg = env.unwrapped.cfg
    doraemon_cfg = getattr(env_cfg, "doraemon", None)
    if doraemon_cfg is not None and getattr(doraemon_cfg, "enable", False):
        doraemon_cfg.enable = False
        logger.info("[Student] DORAEMON disabled for supervised training.")

    # Replace randomization cfg with a fresh hard DomainRandomizationCfg from
    # the env's OWN variant package -- the cfg being replaced must match the env.
    import importlib

    variant_pkg = type(env.unwrapped).__module__.rsplit(".", 1)[0]
    DomainRandomizationCfg = importlib.import_module(f"{variant_pkg}.config").DomainRandomizationCfg
    hard = DomainRandomizationCfg()
    env_cfg.randomization = hard
    logger.info("[Student] Randomization forced to static hard DomainRandomizationCfg.")

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

        # FrozenTeacher builds itself from its checkpoint's geometry, which can differ
        # from StudentCfg's fixed defaults (69D attitude-only vs 72D with
        # use_bias_ema_obs). Sync cfg to what was ACTUALLY built before the student,
        # collector, and buffer are sized from it, or they disagree with the
        # observations the teacher consumes.
        cfg.policy_obs_dim = self.teacher.obs_dim
        cfg.privileged_dim = self.teacher.privileged_dim
        cfg.latent_dim = self.teacher.latent_dim

        env_obs_dim = getattr(env.unwrapped.cfg, "observation_space", None)
        if env_obs_dim is not None and env_obs_dim != cfg.policy_obs_dim:
            raise ValueError(
                f"teacher was trained on {cfg.policy_obs_dim}D observations but this env "
                f"emits {env_obs_dim}D -- distilling across an obs-layout change is invalid."
            )

        self.student = make_student_encoder(cfg).to(device)

        # Reuse teacher's frozen actor_obs_normalizer as student's input normalizer.
        # Student saw plateau at loss_latent ~0.113 with raw 87D obs (scales
        # spanning 10^-2 to 10^2 across quat/omega/torque/action/integral).
        # Normalized input aligns distribution with teacher's actor convention
        # and restores useful gradient signal.
        self.obs_normalizer = self.teacher.policy.actor_obs_normalizer

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

        # GRU hidden state carried across rollout steps (collection-time). Fed forward
        # only when DAgger drives the rollout with the student action (beta<1); with the
        # default teacher-only recipe (beta==1) it stays unused. Training uses
        # self.train_hidden below, a separate persisted hidden.
        if cfg.encoder_type == "gru":
            self.gru_hidden = self.student.init_hidden(cfg.num_envs, device)
            # Training-time hidden persists across iterations so BPTT chunks
            # start from the last rollout's end-state, not zero. This is the
            # RMA-canonical truncated BPTT setup. Initialized to zero.
            self.train_hidden = self.student.init_hidden(cfg.num_envs, device)
        else:
            self.gru_hidden = None
            self.train_hidden = None

        # DAgger collection-time TCN history ring, mirroring StudentInLoopPolicy
        # (analysis/student_policy.py) so the on-policy action the student contributes to the
        # rollout is built from EXACTLY the same window construction as eval. Persists across
        # iterations (carries history over rollout boundaries), zeroed per-env on done.
        # Allocated at the teacher-synced obs width (cfg.policy_obs_dim was set above from
        # the teacher checkpoint). Only TCN needs it, and only when DAgger will actually drive
        # the rollout (beta dips below 1) -- a pure teacher-only run allocates nothing.
        dagger_active = cfg.dagger_beta_start < 1.0 or cfg.dagger_beta_end < 1.0
        if cfg.encoder_type == "tcn" and dagger_active:
            self.collect_ring: torch.Tensor | None = torch.zeros(
                cfg.num_envs, cfg.tcn_history, cfg.policy_obs_dim, device=device
            )
        else:
            self.collect_ring = None

        # dones from the last env.step of the previous rollout. Used to tag the
        # very first observation of the next rollout as "post-reset" when an env
        # terminated right at the rollout boundary. Initialized in learn().
        self.prev_dones: torch.Tensor | None = None

        os.makedirs(os.path.join(log_dir, "models"), exist_ok=True)
        logger.info("StudentRunner initialized: encoder=%s log_dir=%s", cfg.encoder_type, log_dir)

    def _collect_rollout(
        self, obs: torch.Tensor, privileged: torch.Tensor, beta: float
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Run n_steps env steps, filling the buffer with teacher-relabeled targets.

        The env is stepped with ``beta*a_teacher + (1-beta)*a_student`` (DAgger). At
        ``beta==1`` this is the original teacher-only off-policy rollout; at ``beta<1`` the
        student's own latent drives part of the action, so the states visited move toward the
        distribution the student induces at deploy time. The SUPERVISION targets recorded in
        the buffer are always the teacher's ``(l_t, a_t)`` at the visited state -- DAgger
        changes who drives, not what is labeled.

        Alignment (BC-critical):
            buffer[step_idx=s] stores (obs_s, priv_s, a_s, l_s) where a_s, l_s were
            computed from obs_s, priv_s. Student must learn l_hat(history_s) ~= l_s
            and teacher_actor(obs_s, l_hat) ~= a_s. Any time-shift between obs and
            (a, l) breaks the BC target and creates an unreachable loss floor.

        Returns the final (obs, privileged) so the caller can carry state.
        """
        self.buffer.reset()
        # Track dones from the PREVIOUS env.step so that "dones" stored at
        # step_idx=s correctly indicates whether obs_s is a fresh post-reset
        # observation. self.prev_dones persists across rollouts so an env that
        # terminated at the last step of the previous rollout is correctly
        # marked as "post-reset" at step_idx=0 of the next rollout.
        assert self.prev_dones is not None, "prev_dones must be initialized in learn()"
        prev_dones = self.prev_dones

        use_student = beta < 1.0
        if use_student:
            # Run the collection-time student in EVAL mode to match deploy inference exactly
            # (StudentInLoopPolicy calls .eval()): the DAgger premise is that the induced
            # rollout distribution equals the deploy distribution. Restored to train() below
            # before the optimization phase. The current encoder is LayerNorm-only so this is
            # a guard against a future mode-dependent layer, not a present-day numeric change.
            self.student.eval()
        for _ in range(self.cfg.n_steps_per_rollout):
            # Teacher acts from CURRENT (pre-step) obs+privileged
            a_t, l_t = self.teacher.act(obs, privileged)

            # Record PRE-STEP: (obs_s, priv_s, l_s, a_s, prev_dones). This is the BC
            # supervision target and is UNCHANGED by DAgger -- the teacher relabels the
            # visited state regardless of who drove the env there.
            # prev_dones says whether the current obs is a fresh post-reset obs.
            self.buffer.add(obs, privileged, l_t.detach(), a_t.detach(), prev_dones)

            # Step env with the DAgger-mixed action (== a_t when beta==1). The student
            # forward runs only when beta<1, so the default teacher-only recipe pays no cost.
            a_exec = self._dagger_action(obs, a_t, beta) if use_student else a_t
            obs_next, _rew, dones, extras = self.env.step(a_exec)

            # Zero the collection-time student history for reset envs so the next student
            # forward starts fresh for them (GRU hidden and/or TCN ring).
            if dones.any():
                reset_ids = torch.nonzero(dones).squeeze(-1)
                if self.gru_hidden is not None:
                    self.gru_hidden[:, reset_ids] = 0.0
                if use_student and self.collect_ring is not None:
                    self.collect_ring[reset_ids] = 0.0

            obs = obs_next["policy"]
            privileged = obs_next["privileged"]
            prev_dones = dones.to(torch.bool)

        # Persist last env.step dones so the next rollout's step_idx=0 records
        # the correct "post-reset" flag for envs that terminated at the boundary.
        self.prev_dones = prev_dones

        # Slide the last H rollout obs into the pre-rollout history region of
        # flat_buf so the NEXT iteration's early windows contain real history.
        # (GRU path is a no-op.)
        if use_student:
            self.student.train()  # restore train mode for the optimization phase in learn()
        self.buffer.carry_over_history()
        return obs, privileged

    @torch.no_grad()
    def _dagger_action(self, obs: torch.Tensor, a_teacher: torch.Tensor, beta: float) -> torch.Tensor:
        """Mix the teacher action with the action the student's own latent induces.

        The student latent is built from the same normalized history-window machinery as
        eval-time inference (StudentInLoopPolicy.__call__, analysis/student_policy.py): a
        left-rolled TCN ring (newest obs at index H-1) or the carried GRU hidden. no_grad:
        this only shapes the rollout state distribution; the loss is computed later on the
        buffer targets, so the student action must not carry gradient here.
        """
        if self.cfg.encoder_type == "tcn":
            assert self.collect_ring is not None
            # Match StudentInLoopPolicy: shift LEFT (drop oldest at idx 0), newest at idx H-1.
            self.collect_ring = torch.roll(self.collect_ring, shifts=-1, dims=1)
            self.collect_ring[:, -1] = obs
            B, H, D = self.collect_ring.shape
            ring_n = self.obs_normalizer(self.collect_ring.reshape(B * H, D)).reshape(B, H, D)
            l_hat = self.student(ring_n)
        else:
            obs_n = self.obs_normalizer(obs)
            l_hat_seq, self.gru_hidden = self.student(obs_n.unsqueeze(1), hidden=self.gru_hidden)
            l_hat = l_hat_seq[:, -1]
        obs_normed = self.teacher.normalize_obs(obs)
        a_student = self.teacher.actor_forward(obs_normed, l_hat)
        return beta * a_teacher + (1.0 - beta) * a_student

    def _compute_loss_tcn(self, batch) -> dict[str, torch.Tensor]:
        # Normalize per-step with teacher's actor_obs_normalizer so TCN input
        # matches the GRU path and the teacher actor's own input distribution.
        # Previously TCN trained on raw 87D obs (scales 10^-2..10^2), a known
        # cause of the loss_latent plateau the GRU path was already fixed for.
        B, H, D = batch.obs_window.shape
        obs_window_n = self.obs_normalizer(batch.obs_window.reshape(B * H, D)).reshape(B, H, D)
        l_hat = self.student(obs_window_n)               # (M, 9)
        obs_normed = self.teacher.normalize_obs(batch.obs_t)
        a_hat = self.teacher.actor_forward(obs_normed, l_hat)  # (M, 8)
        loss_action = F.mse_loss(a_hat, batch.a_t)
        loss_latent = F.mse_loss(l_hat, batch.l_t)
        total = loss_action + self.cfg.lambda_latent * loss_latent
        return {"loss_total": total, "loss_action": loss_action, "loss_latent": loss_latent}

    def _compute_loss_gru(self, batch, h_in: torch.Tensor) -> dict[str, torch.Tensor]:
        """h_in: (num_layers, M_envs, gru_hidden) — rollout-start hidden for this
        minibatch's envs. Threaded across iters so GRU can accumulate evidence
        over many rollouts, not just 24 steps.
        """
        # Normalize student input (obs_seq) with teacher's actor_obs_normalizer.
        B, T, D = batch.obs_seq.shape
        obs_seq_n = self.obs_normalizer(batch.obs_seq.reshape(B * T, D)).reshape(B, T, D)
        l_hat_seq, _ = self.student(obs_seq_n, hidden=h_in)             # (envs, T, 9)
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
        # Freshly-reset obs: treat as post-reset (dones=True) so flat_buf's
        # pre-rollout region (zeros) isn't mixed with bogus history on step 0.
        self.prev_dones = torch.ones(self.cfg.num_envs, dtype=torch.bool, device=self.device)

        t_start = time.time()
        for it in range(self.cfg.max_iterations):
            # Collect (DAgger: beta anneals teacher->student action over the rollout)
            beta = dagger_beta_at(self.cfg, it)
            t0 = time.time()
            obs, privileged = self._collect_rollout(obs, privileged, beta)
            t_collect = time.time() - t0

            # Train
            t0 = time.time()
            epoch_totals = {"loss_total": 0.0, "loss_action": 0.0, "loss_latent": 0.0, "grad_norm": 0.0}
            n_updates = 0

            # GRU hidden threading: snapshot the rollout-start hidden, zero it
            # for envs that reset mid-rollout (rare given episode length), then
            # reuse the same snapshot across n_epochs so gradient flow through
            # each env's 24-step chunk starts from the correct initial state.
            if self.cfg.encoder_type == "gru":
                assert self.train_hidden is not None
                T_ = self.buffer.step_idx
                any_done_in_rollout = self.buffer.done_flat[:T_].any(dim=0)
                h_start = self.train_hidden.detach().clone()
                h_start[:, any_done_in_rollout] = 0.0
            else:
                h_start = None
                any_done_in_rollout = None

            for _ in range(self.cfg.n_epochs):
                if self.cfg.encoder_type == "tcn":
                    batches = self.buffer.iter_minibatches_tcn()
                else:
                    batches = self.buffer.iter_minibatches_gru()
                for batch in batches:
                    if self.cfg.encoder_type == "tcn":
                        losses = self._compute_loss_tcn(batch)
                    else:
                        assert h_start is not None and batch.env_idx is not None
                        h_in = h_start[:, batch.env_idx].contiguous()
                        losses = self._compute_loss_gru(batch, h_in)
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

            # GRU: recompute the end-of-rollout hidden with ONE no-grad forward
            # over the full rollout so the next iter's h_start reflects the
            # post-update student's hidden trajectory. Uses normalized obs.
            if self.cfg.encoder_type == "gru":
                with torch.no_grad():
                    T_ = self.buffer.step_idx
                    D = self.cfg.policy_obs_dim
                    obs_all = self.buffer.obs_flat[:T_].transpose(0, 1)    # (E, T, D)
                    obs_all_n = self.obs_normalizer(
                        obs_all.reshape(-1, D)
                    ).reshape(self.cfg.num_envs, T_, D)
                    _, h_end = self.student(obs_all_n, hidden=h_start)
                    h_end[:, any_done_in_rollout] = 0.0
                    self.train_hidden = h_end.detach()

            # Log
            metrics = {
                "student/loss_total": epoch_totals["loss_total"],
                "student/loss_action": epoch_totals["loss_action"],
                "student/loss_latent": epoch_totals["loss_latent"],
                "student/grad_norm": epoch_totals["grad_norm"],
                "student/time_collect": t_collect,
                "student/time_train": t_train,
                "student/iter": it,
                "student/dagger_beta": beta,
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
