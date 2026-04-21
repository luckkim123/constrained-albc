# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Runner configurations for ablation variants.

Kept separate from rsl_rl_ppo_cfg.py so main is untouched.
"""

from __future__ import annotations

from isaaclab.utils import configclass

from .rsl_rl_ppo_cfg import FullDOFTRPORunnerCfg, _FullDOFPolicyCfg


# =============================================================================
# Phase 0.6: Baseline challenger (hist5_act3 obs + encoder_latent_dim=16)
# =============================================================================


@configclass
class _FullDOFChallengerEnc16PolicyCfg(_FullDOFPolicyCfg):
    """Encoder policy for challenger: obs=121, latent=16."""

    policy_obs_dim: int = 121
    encoder_latent_dim: int = 16


@configclass
class FullDOFTRPOChallengerEnc16RunnerCfg(FullDOFTRPORunnerCfg):
    """Encoder + IPO + TRPO trained on hist5_act3 obs with doubled latent."""

    policy = _FullDOFChallengerEnc16PolicyCfg()
