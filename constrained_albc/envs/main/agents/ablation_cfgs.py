# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Runner configurations for ablation variants.

Kept separate from rsl_rl_ppo_cfg.py so main is untouched.
"""

from __future__ import annotations

import rsl_rl.runners.on_policy_runner as _runner_module

from isaaclab.utils import configclass

# Spelled out to the module, exactly as `rsl_rl_ppo_cfg.py` imports ConstraintTRPO:
# `constrained_albc.algorithms` keeps a docstring-only __init__ (the deploy isolation
# path loads submodules under stubbed parents), so there is no package-level re-export
# to import from. `tests/test_config_equivalence.py` stubs this exact module name.
from constrained_albc.algorithms.constraint_lagrangian import ConstraintLagrangian

from .rsl_rl_ppo_cfg import (
    ALBCTRPORunnerCfg,
    RslRlConstraintTRPOAlgorithmCfg,
    _ALBCNoEncoderPolicyCfg,
    _ALBCPolicyCfg,
    _ALBCPPOAlgorithmCfg,
    _BaseALBCRunnerCfg,
)

# rsl-rl resolves `algorithm.class_name` against the runner module's namespace, the
# same way `rsl_rl_ppo_cfg.py` injects ALBCConstraintTRPO there.
_runner_module.ALBCConstraintLagrangian = ConstraintLagrangian

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
    every iteration — same DR schedule as Isaac-ConstrainedALBC-TRPO-v0.
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


# =============================================================================
# Variant #5: TRPO-NoIPO-NoEncoder ("no-both": encoder AND IPO both removed)
# =============================================================================
#
# Combines Baseline 1's no-encoder policy with Variant #3's no-IPO env
# (ALBCNoConstraintEnvCfg). ConstraintEncoderRunner auto-sync propagates
# num_constraints=0 from the env to both cfgs (same mechanism as Variant #3),
# so RslRlConstraintTRPOAlgorithmCfg no-ops the IPO barrier and cost critic
# without any algorithm override. Only the policy differs from
# ALBCTRPONoIPORunnerCfg.


@configclass
class ALBCTRPONoIPONoEncoderRunnerCfg(ALBCTRPORunnerCfg):
    """Encoder-free TRPO without IPO ("no-both"). Uses ALBCNoConstraintEnvCfg."""

    experiment_name: str = "albc_ablation"
    policy = _ALBCNoEncoderPolicyCfg()


# =============================================================================
# Arm N1: Lagrangian constrained TRPO (program `paper-ablation-5000`)
# =============================================================================
#
# Same encoder, same TRPO trust region, same K=10 constraint list and the same
# budgets as the main method -- only the constraint MECHANISM differs (IPO log
# barrier -> Lagrangian multipliers with dual ascent). The env cfg is therefore
# the constraint-carrying one, NOT `config_noconstraint`: an empty constraint list
# would make this arm identical to TRPO-NoIPO and measure nothing.
#
# Pre-registered read-out (PLAN.md §4-1): line-search success rate. A large
# multiplier can make every TRPO backtrack fail, which freezes the policy without
# raising anything -- see the ConstraintLagrangian module docstring.


@configclass
class _ALBCLagrangianAlgorithmCfg(RslRlConstraintTRPOAlgorithmCfg):
    """ConstraintTRPO's algorithm cfg pointed at the Lagrangian subclass.

    Every inherited field keeps its main-method value on purpose. The three added
    below are the dual-ascent knobs and are UNTUNED starting points -- no run has
    used this class yet.
    """

    class_name: str = "ALBCConstraintLagrangian"
    lagrangian_lr: float = 0.01
    lagrangian_init: float = 0.0
    lagrangian_max: float = 10.0


@configclass
class ALBCTRPOLagrangianRunnerCfg(ALBCTRPORunnerCfg):
    """Encoder + TRPO with Lagrangian constraints. Uses ALBCSimToRealEnvCfg."""

    experiment_name: str = "albc_ablation"

    algorithm = _ALBCLagrangianAlgorithmCfg()


# =============================================================================
# Arm N4: Residual RL over classical TDC (program `paper-ablation-5000`)
# =============================================================================
#
# Identical learner to the main method -- encoder, ConstraintTRPO, IPO, same K=10
# budgets -- so the only thing that differs from A1 is WHAT the policy commands: a
# correction torque on top of TDC instead of the whole action. Env side lives in
# `envs/tdc_main/residual_tdc_env.py`.


@configclass
class ALBCResidualTDCRunnerCfg(ALBCTRPORunnerCfg):
    """Encoder + TRPO + IPO driving a residual over TDC. Uses ALBCResidualTDCEnvCfg."""

    experiment_name: str = "albc_ablation"
