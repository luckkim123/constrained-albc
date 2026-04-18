# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Single runner for constrained ALBC: encoder metrics + constraint state.

Flat subclass of OnPolicyRunner that combines:
    - Teacher encoder metrics logging (if encoder present)
    - Log-barrier constraint metrics (TRPO + IPO)
    - Auto-sync of num_constraints from env config
"""

from __future__ import annotations

import logging
import os

import torch
from rsl_rl.runners import OnPolicyRunner

from ..utils.logging import flush_metrics, log_encoder_metrics

logger = logging.getLogger(__name__)


class ConstraintEncoderRunner(OnPolicyRunner):
    """OnPolicyRunner with encoder metrics and log-barrier constraint support.

    Provides:
        - Encoder metrics: z latent statistics, gradient norms (when encoder present)
        - Constraint metrics: barrier margins, penalty (Modified IPO)
        - Auto-sync: num_constraints from env config to algorithm/policy config
    """

    def __init__(self, env, train_cfg, log_dir=None, device="cpu"):
        # Auto-sync num_constraints from env config before parent init.
        # train_cfg is a plain dict (from agent_cfg.to_dict()), so use dict
        # key access instead of hasattr/getattr which only work on objects.
        constraints_cfg = getattr(env.unwrapped.cfg, "constraints", None)
        if constraints_cfg is not None:
            env_k = constraints_cfg.num_constraints
            alg_cfg = train_cfg["algorithm"]
            policy_cfg = train_cfg["policy"]

            if "num_constraints" in alg_cfg and alg_cfg["num_constraints"] != env_k:
                logger.info(
                    "Auto-syncing num_constraints: alg %d -> %d",
                    alg_cfg["num_constraints"],
                    env_k,
                )
                alg_cfg["num_constraints"] = env_k
                alg_cfg["constraint_budgets"] = constraints_cfg.constraint_budgets

            if "num_constraints" in policy_cfg and policy_cfg["num_constraints"] != env_k:
                logger.info(
                    "Auto-syncing num_constraints: policy %d -> %d",
                    policy_cfg["num_constraints"],
                    env_k,
                )
                policy_cfg["num_constraints"] = env_k

            # Cache constraint names for logging
            self._constraint_names = constraints_cfg.constraint_names
        else:
            self._constraint_names = ()

        # Value normalization flag (set via train_cfg or algorithm config)
        self._normalize_value = train_cfg.get("normalize_value", False)

        super().__init__(env, train_cfg, log_dir, device)

        # Detect encoder for conditional metrics logging
        self._has_encoder = hasattr(self.alg.policy, "encoder")
        if self._has_encoder:
            logger.info("[ConstraintEncoderRunner] Encoder detected. Encoder metrics logging enabled.")

        # Set up value normalization (HORA-style running mean/std).
        #
        # HORA flow (hora/algo/ppo/ppo.py:152-159, 364-368):
        #   Rollout: critic -> denormalize (v*std+mean) -> raw values stored
        #   GAE:     raw values -> returns, advantages (normalized mean=0,std=1)
        #   Post-GAE: normalize values/returns in-place (critic targets)
        #   Update:  critic learns to predict normalized values
        #
        # Without denormalization during rollout, GAE mixes raw rewards with
        # normalized values once the critic converges, corrupting advantages.
        if self._normalize_value:
            self._value_running_mean = torch.zeros(1, device=device)
            self._value_running_var = torch.ones(1, device=device)
            self._value_count = 1e-4

            def _compute_returns_with_value_norm(obs):
                storage = self.alg.storage
                std = torch.sqrt(self._value_running_var + 1e-8)
                mean = self._value_running_mean

                # 1. Denormalize stored values (critic outputs normalized scale
                #    after training). On iter 0: mean=0, std=1, so identity.
                storage.values[:] = storage.values * std + mean

                # 2. Compute last_values and denormalize for GAE bootstrap.
                last_values = self.alg.policy.evaluate(obs).detach()
                last_values = last_values * std + mean

                # 3. GAE on raw-scale values -> normalized advantages (mean=0).
                storage.compute_returns(
                    last_values,
                    self.alg.gamma,
                    self.alg.lam,
                    normalize_advantage=not self.alg.normalize_advantage_per_mini_batch,
                )

                # 4. Update running stats from raw returns, then normalize
                #    values/returns in-place for critic loss targets.
                self._normalize_storage_values()

            self.alg.compute_returns = _compute_returns_with_value_norm
            logger.info("[ConstraintEncoderRunner] Value normalization enabled (HORA-style).")

    # ------------------------------------------------------------------
    # Value normalization
    # ------------------------------------------------------------------

    def _normalize_storage_values(self) -> None:
        """Update running stats and normalize values/returns for critic targets.

        Called after GAE (which uses raw-scale values). Advantages are already
        normalized by storage.compute_returns() and are NOT touched here.
        """
        storage = self.alg.storage
        returns_flat = storage.returns.flatten()

        # Update running statistics (Welford's algorithm)
        batch_mean = returns_flat.mean()
        batch_var = returns_flat.var()
        batch_count = returns_flat.numel()

        delta = batch_mean - self._value_running_mean
        total_count = self._value_count + batch_count
        self._value_running_mean = self._value_running_mean + delta * batch_count / total_count
        m_a = self._value_running_var * self._value_count
        m_b = batch_var * batch_count
        m2 = m_a + m_b + delta**2 * self._value_count * batch_count / total_count
        self._value_running_var = m2 / total_count
        self._value_count = total_count

        # Normalize values and returns in-place (for critic targets).
        # Do NOT recompute advantages -- they are already normalized.
        std = torch.sqrt(self._value_running_var + 1e-8)
        storage.values[:] = (storage.values - self._value_running_mean) / std
        storage.returns[:] = (storage.returns - self._value_running_mean) / std

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def _should_log(self) -> bool:
        """Whether logging is active (log_dir set and logs not disabled)."""
        return self.log_dir is not None and not self.disable_logs

    # ------------------------------------------------------------------
    # Auxiliary state persistence helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _save_aux_state(path: str, name: str, state: dict) -> None:
        """Save auxiliary state dict alongside a model checkpoint."""
        aux_path = os.path.join(os.path.dirname(path), name)
        torch.save(state, aux_path)

    @staticmethod
    def _load_aux_state(path: str, name: str, device: str) -> dict | None:
        """Load auxiliary state dict from alongside a model checkpoint, or None."""
        aux_path = os.path.join(os.path.dirname(path), name)
        if os.path.exists(aux_path):
            return torch.load(aux_path, map_location=device, weights_only=False)
        return None

    # ------------------------------------------------------------------
    # Training loop overrides
    # ------------------------------------------------------------------

    def learn(self, num_learning_iterations: int, init_at_random_ep_len: bool = False) -> None:
        """Reset environments before training."""
        if hasattr(self.alg, "set_max_iterations"):
            self.alg.set_max_iterations(num_learning_iterations)
        self.env.reset()
        super().learn(num_learning_iterations, init_at_random_ep_len)

    def log(self, locs: dict, width: int = 80, pad: int = 35) -> None:
        """Extended log with encoder metrics and constraint metrics."""
        super().log(locs, width, pad)

        iteration = locs["it"]

        # Encoder metrics (z latent health: z_mean, z_std, z_min, z_max)
        if self._has_encoder and self._should_log:
            log_encoder_metrics(
                writer=self.writer,
                policy=self.alg.policy,
                env=self.env,
                iteration=iteration,
                device=self.device,
                logger_type=self.logger_type,
            )

        # Constraint metrics
        if self._should_log:
            self._log_constraint_metrics(iteration)

        # DORAEMON: update DR distribution based on episode statistics
        raw_env = self.env.unwrapped
        if hasattr(raw_env, "_doraemon") and raw_env._doraemon is not None:
            metrics = raw_env._doraemon.step()
            if self._should_log:
                prefixed = {f"DORAEMON/{k}": v for k, v in metrics.items()}
                flush_metrics(self.writer, prefixed, iteration, self.logger_type)

    # ------------------------------------------------------------------
    # Checkpoint save/load
    # ------------------------------------------------------------------

    def save(self, path: str, infos: dict | None = None) -> None:
        """Save model checkpoint, DORAEMON state, and adaptive entropy state."""
        super().save(path, infos)

        # Save DORAEMON distribution state
        raw_env = self.env.unwrapped
        if hasattr(raw_env, "_doraemon") and raw_env._doraemon is not None:
            self._save_aux_state(path, "doraemon_state.pt", raw_env._doraemon.state_dict())

    def load(self, path: str, load_optimizer: bool = True, map_location: str | None = None) -> dict:
        """Load model checkpoint, DORAEMON state, and adaptive entropy state."""
        infos = super().load(path, load_optimizer, map_location)

        # Restore DORAEMON distribution state
        raw_env = self.env.unwrapped
        if hasattr(raw_env, "_doraemon") and raw_env._doraemon is not None:
            doraemon_state = self._load_aux_state(path, "doraemon_state.pt", self.device)
            if doraemon_state is not None:
                raw_env._doraemon.load_state_dict(doraemon_state)
                logger.info("Restored DORAEMON distribution state from checkpoint")

        return infos

    # ------------------------------------------------------------------
    # Constraint metrics
    # ------------------------------------------------------------------

    def _log_constraint_metrics(self, iteration: int) -> None:
        """Log constraint metrics to TensorBoard/WandB.

        Logs per-constraint: cost_return, violation, d_k, barrier_margin.
        Also logs aggregate barrier penalty and policy diagnostics.
        """
        alg = self.alg
        if not hasattr(alg, "num_constraints"):
            return

        K = alg.num_constraints
        metrics: dict[str, float] = {}

        # Per-constraint: violation + barrier margin (2-level hierarchy for WandB grouping)
        for k in range(K):
            suffix = self._constraint_names[k] if k < len(self._constraint_names) else str(k)
            metrics[f"Constraint/viol/{suffix}"] = alg._last_violations[k]
            metrics[f"Constraint/margin/{suffix}"] = alg._last_barrier_margins[k]

        # Aggregate constraint metric
        metrics["Constraint/barrier_penalty"] = alg._last_barrier_penalty

        # Policy diagnostics
        metrics["Policy/line_search_success"] = alg._last_line_search_success
        metrics["Policy/entropy"] = alg._last_mean_entropy
        metrics["Policy/encoder_grad_norm"] = alg._last_encoder_grad_norm
        metrics["Policy/surrogate_loss"] = alg._last_surrogate_loss

        # Gradient step norms (consolidated from GradDecomp + SigmaStep)
        metrics["Grad/enc_step"] = alg._last_enc_step_norm
        metrics["Grad/actor_step"] = alg._last_actor_step_norm
        metrics["Grad/sigma_step"] = alg._last_sigma_step_norm
        metrics["Grad/sigma_dir"] = alg._last_sigma_step_mean  # positive = noise increase

        # Noise std (consolidated from per-dim NoiseStd)
        with torch.no_grad():
            per_dim_std = self.alg.policy.log_std.exp()
        metrics["Noise/std_mean"] = per_dim_std.mean().item()
        metrics["Noise/std_min"] = per_dim_std.min().item()

        flush_metrics(self.writer, metrics, iteration, self.logger_type)
