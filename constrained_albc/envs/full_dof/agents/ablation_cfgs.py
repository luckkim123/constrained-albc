# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Runner configurations for ablation variants.

Kept separate from rsl_rl_ppo_cfg.py so main is untouched.
"""

from __future__ import annotations

from isaaclab.utils import configclass

from .rsl_rl_ppo_cfg import (
    ALBCTRPORunnerCfg,
    _ALBCPolicyCfg,
    _ALBCPPOAlgorithmCfg,
    _BaseALBCRunnerCfg,
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
# _ALBCPolicyCfg, so the variable under ablation is purely "IPO on/off".


@configclass
class ALBCTRPONoIPORunnerCfg(ALBCTRPORunnerCfg):
    """Encoder + TRPO without IPO. Uses ALBCNoConstraintEnvCfg."""

    experiment_name: str = "albc_ablation"


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
#   1. OnPolicyRunner instantiates "ALBCActorCriticEncoder" correctly.
#   2. PPO's update loop accepts the encoder policy's forward signature.
#   3. No hardcoded num_constraints > 0 assumption in PolicyBase.


@configclass
class _ALBCPPOEncPolicyCfg(_ALBCPolicyCfg):
    """Encoder policy with num_constraints=0 (skips cost critic build)."""

    num_constraints: int = 0


@configclass
class ALBCPPOEncRunnerCfg(_BaseALBCRunnerCfg):
    """Encoder + PPO. No IPO. Uses ALBCNoConstraintEnvCfg.

    Runs under OnPolicyDoraemonRunner so DORAEMON curriculum is stepped
    every iteration — same DR schedule as Isaac-ConstrainedALBC-Full-TRPO-v0.
    """

    class_name: str = "OnPolicyDoraemonRunner"
    save_interval: int = 100  # intentional: ablation checkpoints less often than main (50)
    experiment_name: str = "albc_ablation"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ALBCPPOAlgorithmCfg()
    policy = _ALBCPPOEncPolicyCfg()
