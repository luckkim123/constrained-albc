# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""OnPolicyRunner with DORAEMON curriculum stepping and state persistence.

Wraps rsl_rl.OnPolicyRunner (stock PPO) so PPO-based ablations train against
the same adaptive DR curriculum as the ConstraintTRPO baseline. Without this
runner, PPO variants would leave the env's DORAEMON scheduler initialized but
never step it: the Beta distribution would stay frozen at ``init_concentration``
and the ablation would confound algorithm with DR-curriculum.

DORAEMON integration points mirror ConstraintEncoderRunner exactly:
    - ``learn()``: reset env so the first rollout uses DORAEMON-sampled physics
    - ``log()`` : call ``_doraemon.step()`` once per iteration, emit
      ``DORAEMON/*`` scalars (mean/std per parameter, KL, ESS, success_rate)
    - ``save()`` : dump ``doraemon_state.pt`` alongside each model checkpoint
    - ``load()`` : restore ``doraemon_state.pt`` from the checkpoint directory
"""

from __future__ import annotations

import logging
import os

import torch
from rsl_rl.runners import OnPolicyRunner

from ..utils.logging import flush_metrics
from . import sync_policy_obs_dim

logger = logging.getLogger(__name__)


class OnPolicyDoraemonRunner(OnPolicyRunner):
    """Stock OnPolicyRunner extended with DORAEMON curriculum hooks.

    All four overrides are no-ops when the env lacks ``_doraemon`` (e.g. if a
    user disables DORAEMON via ``cfg.doraemon.enable = False``), so this runner
    is safe to use as a drop-in replacement for OnPolicyRunner.
    """

    def __init__(self, env, train_cfg, log_dir=None, device="cpu"):
        # PPO-Enc reaches the encoder policy through this runner, so it needs the
        # same env->cfg obs-width sync ConstraintEncoderRunner does; without it the
        # encoder builds at the cfg's static 69 against a 72D env (use_bias_ema_obs).
        # No-op for the plain-PPO variant, whose ActorCritic cfg has no policy_obs_dim.
        sync_policy_obs_dim(env, train_cfg)
        super().__init__(env, train_cfg, log_dir=log_dir, device=device)

    # ------------------------------------------------------------------
    # Helpers (duplicated from ConstraintEncoderRunner; kept private to
    # avoid cross-runner inheritance from a TRPO-specific class).
    # ------------------------------------------------------------------

    @property
    def _should_log(self) -> bool:
        return self.log_dir is not None and not self.disable_logs

    @staticmethod
    def _save_aux_state(path: str, name: str, state: dict) -> None:
        aux_path = os.path.join(os.path.dirname(path), name)
        torch.save(state, aux_path)

    @staticmethod
    def _load_aux_state(path: str, name: str, device: str) -> dict | None:
        aux_path = os.path.join(os.path.dirname(path), name)
        if os.path.exists(aux_path):
            return torch.load(aux_path, map_location=device, weights_only=False)
        return None

    # ------------------------------------------------------------------
    # Training loop overrides
    # ------------------------------------------------------------------

    def learn(self, num_learning_iterations: int, init_at_random_ep_len: bool = False) -> None:
        """Reset env before training so the first rollout uses DORAEMON-sampled physics.

        Stock OnPolicyRunner skips this reset and reuses whatever env state was
        left over from construction; that would bypass DORAEMON sampling on the
        very first batch of episodes. ConstraintEncoderRunner follows the same
        pattern.
        """
        self.env.reset()
        super().learn(num_learning_iterations, init_at_random_ep_len)

    def log(self, locs: dict, width: int = 80, pad: int = 35) -> None:
        """Step DORAEMON and emit its metrics after the standard per-iteration log."""
        super().log(locs, width, pad)

        iteration = locs["it"]
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
        """Save model checkpoint plus ``doraemon_state.pt`` alongside it."""
        super().save(path, infos)
        raw_env = self.env.unwrapped
        if hasattr(raw_env, "_doraemon") and raw_env._doraemon is not None:
            self._save_aux_state(path, "doraemon_state.pt", raw_env._doraemon.state_dict())

    def load(self, path: str, load_optimizer: bool = True, map_location: str | None = None) -> dict:
        """Load model checkpoint plus ``doraemon_state.pt`` if present."""
        infos = super().load(path, load_optimizer, map_location)
        raw_env = self.env.unwrapped
        if hasattr(raw_env, "_doraemon") and raw_env._doraemon is not None:
            doraemon_state = self._load_aux_state(path, "doraemon_state.pt", self.device)
            if doraemon_state is not None:
                raw_env._doraemon.load_state_dict(doraemon_state)
                logger.info("Restored DORAEMON distribution state from checkpoint")
        return infos
