# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Runner configurations for ablation variants.

Kept separate from rsl_rl_ppo_cfg.py so main is untouched.
"""

from __future__ import annotations

from isaaclab.utils import configclass
from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg

from .rsl_rl_ppo_cfg import (
    FullDOFTRPORunnerCfg,
    _FullDOFPolicyCfg,
    _FullDOFPPOAlgorithmCfg,
)


# =============================================================================
# Variant #3: TRPO-NoIPO (encoder + TRPO, no IPO)
# =============================================================================
#
# Same encoder + TRPO as the main method, but the env's constraints list is
# empty (see ALBCNoConstraintEnvCfg). ConstraintEncoderRunner auto-sync then
# propagates num_constraints=0 to both the policy and algorithm cfgs, which
# causes ConstraintTRPO to skip the IPO barrier and cost-critic paths.
#
# Policy obs dim / encoder latent inherited from the main method's
# _FullDOFPolicyCfg, so the variable under ablation is purely "IPO on/off".


@configclass
class FullDOFTRPONoIPORunnerCfg(FullDOFTRPORunnerCfg):
    """Encoder + TRPO without IPO. Uses ALBCNoConstraintEnvCfg."""

    experiment_name: str = "full_dof_ablation"


# =============================================================================
# Variant #4: PPO-Enc (encoder + PPO)
# =============================================================================
#
# Encoder (ActorCriticEncoder) trained with standard PPO instead of TRPO.
# No IPO barrier (env constraints list is empty).
#
# Uses standard rsl-rl OnPolicyRunner, NOT ConstraintEncoderRunner — the
# encoder-aware runner auto-syncs num_constraints from env, which is fine
# here (env has 0) but it also enforces ConstraintTRPO-specific hooks.
# Standard OnPolicyRunner pairs with PPO and still picks up the encoder
# policy class from the global namespace via class_name.
#
# Risks to verify at smoke time:
#   1. OnPolicyRunner instantiates "FullDOFActorCriticEncoder" correctly.
#   2. PPO's update loop accepts the encoder policy's forward signature.
#   3. No hardcoded num_constraints > 0 assumption in PolicyBase.


@configclass
class _FullDOFPPOEncPolicyCfg(_FullDOFPolicyCfg):
    """Encoder policy with num_constraints=0 (skips cost critic build)."""

    num_constraints: int = 0


@configclass
class FullDOFPPOEncRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Encoder + PPO. No IPO. Uses ALBCNoConstraintEnvCfg."""

    # Standard rsl-rl OnPolicyRunner (default class_name).
    seed: int = 30
    num_steps_per_env: int = 64
    max_iterations: int = 2500
    save_interval: int = 100
    experiment_name: str = "full_dof_ablation"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _FullDOFPPOAlgorithmCfg()
    policy = _FullDOFPPOEncPolicyCfg()
