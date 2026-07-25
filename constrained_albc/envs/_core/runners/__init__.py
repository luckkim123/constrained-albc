# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared runner modules. Import-light by design (see _core/__init__.py)."""

import logging

logger = logging.getLogger(__name__)


def sync_policy_obs_dim(env, train_cfg: dict) -> None:
    """Point the policy cfg's ``policy_obs_dim`` at the env's real observation width.

    The static cfg defaults (69 main / 87 full_dof) already match
    ``cfg.observation_space`` for every stock config, so this is a no-op there. A
    toggle that resizes the observation -- main's ``use_bias_ema_obs`` bumps it
    69 -> 72 -- changes the env without touching the agent cfg; without this sync the
    actor/critic/encoder build at the wrong input width and ``_PolicyBase._init_base``
    aborts the run.

    Every runner that can carry an encoder policy must call this before
    ``super().__init__()``, not just the constraint runner: PPO-Enc reaches the same
    encoder policy through ``OnPolicyDoraemonRunner``.
    """
    env_obs_dim = getattr(env.unwrapped.cfg, "observation_space", None)
    if env_obs_dim is None:
        return
    policy_cfg = train_cfg["policy"]
    if "policy_obs_dim" in policy_cfg and policy_cfg["policy_obs_dim"] != env_obs_dim:
        logger.info("Auto-syncing policy_obs_dim: policy %d -> %d", policy_cfg["policy_obs_dim"], env_obs_dim)
        policy_cfg["policy_obs_dim"] = env_obs_dim


def sync_privileged_dim(env, train_cfg: dict) -> None:
    """Point the policy cfg's ``privileged_dim`` at the env's real state-space width.

    Mirrors sync_policy_obs_dim above. The static cfg default (28) already matches
    ``cfg.state_space`` for every stock config, so this is a no-op there. A toggle
    that resizes the privileged obs -- main's ``use_privileged_fault_obs`` bumps it
    28 -> 34 (Arm B) -- changes the env without touching the agent cfg; without this
    sync the critic/encoder build at the wrong input width and
    ``_PolicyBase._init_base`` aborts the run.
    """
    env_state_dim = getattr(env.unwrapped.cfg, "state_space", None)
    if env_state_dim is None:
        return
    policy_cfg = train_cfg["policy"]
    if "privileged_dim" in policy_cfg and policy_cfg["privileged_dim"] != env_state_dim:
        logger.info("Auto-syncing privileged_dim: policy %d -> %d", policy_cfg["privileged_dim"], env_state_dim)
        policy_cfg["privileged_dim"] = env_state_dim
