# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL agent configurations for velocity tracking ALBC environment.

Single pipeline: TRPO + IPO + Asymmetric Encoder (8D action, 81D obs).
"""

import rsl_rl.runners.on_policy_runner as _runner_module

from isaaclab.utils import configclass

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg, RslRlPpoAlgorithmCfg

# Register custom classes in RSL-RL runner module namespace.
from ..algorithms import ConstraintTRPO
from ..encoder import ActorCriticAsymConstrained, ActorCriticEncoder
from ..runners import ConstraintEncoderRunner

_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
_runner_module.FullDOFActorCriticAsymConstrained = ActorCriticAsymConstrained
_runner_module.FullDOFConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.FullDOFConstraintTRPO = ConstraintTRPO


# =============================================================================
# Encoder Bounds (24D privileged obs, static min-max normalization)
# =============================================================================

# 24D non-redundant privileged obs bounds from HardDomainRandomizationCfg.
# Each pair is (lower, upper) with ~10% margin beyond Hard DR range.
# Layout: hydro(7) + dynamics(5) + payload(4) + actuator(4) + env(4)
#
# Base values from HeroAgentHydrodynamicsCfg:
#   volume=0.009, CoG=(0,0,-0.05), CoB=(0,0,0), Ixx=0.0994
#   lin_damp_roll=0.3, quad_damp_roll=1.0, mass=9.18, added_mass_surge=8.0
#   thrust_coeff=40, time_const_up=0.1, water_density=998
_PRIV_OBS_LOWER: list[float] = [
    # Hydrodynamics (7D): volume, CoG(x,y,z), CoB(x,y,z)
    0.006,
    -0.025,
    -0.025,
    -0.10,
    -0.025,
    -0.025,
    -0.05,
    # Dynamic Response (5D): Ixx, lin_damp_roll, quad_damp_roll, mass, added_mass_surge
    0.045,
    0.10,
    0.3,
    6.5,
    4.3,
    # Payload (4D): mass, cog_offset(x,y,z)
    -0.1,
    -0.17,
    -0.17,
    -0.055,
    # Actuator (4D): stiffness, damping, thrust_coeff, time_const_up
    25.0,
    0.2,
    25.0,
    0.06,
    # Environment (4D): water_density, ocean_current(x,y,z)
    990.0,
    -0.55,
    -0.55,
    -0.30,
]

_PRIV_OBS_UPPER: list[float] = [
    # Hydrodynamics (7D)
    0.012,
    0.025,
    0.025,
    0.0,
    0.025,
    0.025,
    0.05,
    # Dynamic Response (5D)
    0.19,
    0.50,
    1.8,
    12.5,
    12.3,
    # Payload (4D)
    2.2,
    0.17,
    0.17,
    0.01,
    # Actuator (4D)
    165.0,
    7.7,
    55.0,
    0.15,
    # Environment (4D)
    1030.0,
    0.55,
    0.55,
    0.30,
]


# =============================================================================
# Policy Configuration
# =============================================================================


@configclass
class _EncoderPolicyCfg(RslRlPpoActorCriticCfg):
    """Base encoder policy configuration."""

    init_noise_std: float = 0.7
    actor_obs_normalization: bool = True
    critic_obs_normalization: bool = False
    actor_hidden_dims: list[int] = [256, 128, 64]
    critic_hidden_dims: list[int] = [512, 256, 128]
    activation: str = "elu"
    # Encoder
    encoder_hidden_dims: list[int] = [256, 128, 64]
    encoder_latent_dim: int = 9
    encoder_activation: str = "elu"
    encoder_obs_normalization: bool = False
    # Observation dimensions
    policy_obs_dim: int = 81  # 26D current proprio + 55D temporal history
    privileged_dim: int = 24


@configclass
class _FullDOFPolicyCfg(_EncoderPolicyCfg):
    """Asymmetric encoder with cost critic for TRPO + IPO.

    Architecture (24D->9D encoder, 8D action):
        Encoder: p_t(24D) -> static_minmax -> MLP[256,128,64] -> LN -> softsign -> z(9D)
        Actor:   cat([o_t(81D), z(9D)]) = 90D -> MLP[256,128,64] -> 8D
        Critic:  cat([o_t(81D), z(9D), p_t(24D)]) = 114D -> MLP[512,256,128] -> 1D
        Cost:    same 114D input -> MLP[512,256,128] -> K (multi-head)
    """

    class_name: str = "FullDOFActorCriticEncoder"
    shared_backbone: bool = False
    critic_uses_z: bool = True
    encoder_output_norm: bool = True  # LayerNorm before softsign
    encoder_obs_lower: list[float] = _PRIV_OBS_LOWER
    encoder_obs_upper: list[float] = _PRIV_OBS_UPPER
    # Cost critic for IPO
    num_constraints: int = 0  # Auto-synced from env config
    cost_critic_hidden_dims: list[int] = [512, 256, 128]


# =============================================================================
# Algorithm Configuration
# =============================================================================


@configclass
class RslRlConstraintTRPOAlgorithmCfg:
    """TRPO + IPO (Interior-Point Optimization) algorithm.

    Two optimizer groups:
    - Actor + Encoder + Sigma (log_std): TRPO natural gradient (trust region)
    - Value (critic + cost_critic): Adam (MSE loss)
    """

    class_name: str = "FullDOFConstraintTRPO"

    # TRPO
    max_kl: float = 0.005
    cg_iters: int = 10
    cg_damping: float = 0.1
    line_search_max_backtracks: int = 10
    line_search_shrink_factor: float = 0.5

    # Value function
    num_learning_epochs: int = 5
    num_mini_batches: int = 4
    value_loss_coef: float = 1.0
    cost_value_loss_coef: float = 1.0
    value_lr: float = 1e-3
    max_grad_norm: float = 1.0

    # GAE
    gamma: float = 0.99
    lam: float = 0.95

    # Constraint
    num_constraints: int = 0
    constraint_budgets: tuple[float, ...] = ()
    cost_gamma: float = 0.99
    cost_lam: float = 0.95
    line_search_kl_margin: float = 1.5

    # Log barrier (IPO)
    barrier_t: float = 100.0
    barrier_alpha: float = 0.05

    # Entropy bonus: counteracts TRPO's natural noise reduction.
    # 04-09 run (entropy_coef=0.003): noise recovered 0.36->0.55 after iter 3758.
    # 04-10 run (entropy_coef=0): noise collapsed to 0.12.
    entropy_coef: float = 0.003
    # Per-dim entropy_coef: overrides scalar when non-empty. Allows targeted
    # entropy pressure per action dim (e.g., stronger for arm, weaker for thrusters).
    # Default: arm=0.01 (prevents noise collapse), thr=0.001 (prevents noise divergence).
    # Validated in Round 2 experiments (2026-04-14): PerDimEnt outperformed Baseline
    # and ArmOnly on reward, noise stability, and DORAEMON success.
    entropy_coef_per_dim: tuple[float, ...] = (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001)

    # Sigma safety bounds (clamped after TRPO step)
    min_std: float = 0.05
    max_std: float = 2.0
    # Per-dim min_std: arm joints(0,1)=0.10, thrusters(2-7)=0.05.
    # Arm dims collapse to scalar min_std by iter 1404; thruster dims stay above 0.14.
    min_std_per_dim: tuple[float, ...] = (0.10, 0.10, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05)


# =============================================================================
# Runner Configuration
# =============================================================================


@configclass
class FullDOFTRPORunnerCfg(RslRlOnPolicyRunnerCfg):
    """Velocity tracking TRPO + IPO + Asymmetric Encoder runner.

    8D action (2D arm + 6D wrench), 81D policy obs, 24D privileged obs.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 2500
    save_interval = 50
    experiment_name = "full_dof_trpo"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Experiment: Per-dim entropy_coef (arm=0.01, thr=0.001)
# =============================================================================


@configclass
class _ExpPerDimEntAlgorithmCfg(RslRlConstraintTRPOAlgorithmCfg):
    """TRPO + IPO with per-dim entropy coefficient.

    arm dims (0,1): 0.01 — net gradient +0.003 (reverses arm collapse direction).
    thr dims (2-7): 0.001 — 1/3 of baseline, slows thr6/7 noise divergence.
    """

    entropy_coef_per_dim: tuple[float, ...] = (0.01, 0.01, 0.001, 0.001, 0.001, 0.001, 0.001, 0.001)


@configclass
class FullDOFPerDimEntRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Exp 1: per-dim entropy_coef experiment."""

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_perdim_ent"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Experiment: max_std=1.0 (cap thr6/7 divergence)
# =============================================================================


@configclass
class _ExpMaxStd1AlgorithmCfg(RslRlConstraintTRPOAlgorithmCfg):
    """TRPO + IPO with max_std capped at 1.0."""

    max_std: float = 1.0


@configclass
class FullDOFMaxStd1RunnerCfg(RslRlOnPolicyRunnerCfg):
    """Exp 2: max_std=1.0 experiment."""

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_maxstd1"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpMaxStd1AlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Experiment: Arm-only boost (arm=0.01, thr=0.003 = baseline uniform)
# =============================================================================


@configclass
class _ExpArmOnlyAlgorithmCfg(RslRlConstraintTRPOAlgorithmCfg):
    """TRPO + IPO with per-dim entropy: arm boost only.

    arm dims (0,1): 0.01 -- same as PerDimEnt.
    thr dims (2-7): 0.003 -- same as baseline uniform entropy_coef.
    Tests whether arm-only intervention suffices without thruster noise reduction.
    """

    entropy_coef_per_dim: tuple[float, ...] = (0.01, 0.01, 0.003, 0.003, 0.003, 0.003, 0.003, 0.003)


@configclass
class FullDOFArmOnlyRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Exp: arm-only entropy boost (thr = baseline uniform)."""

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_armonly"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpArmOnlyAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Experiment: L1 SS error penalty (lin_vel_lin_ratio=0.15, yaw_vel_lin_ratio=0.15)
# =============================================================================


@configclass
class FullDOFExpL1RunnerCfg(RslRlOnPolicyRunnerCfg):
    """Exp: L1 penalty for SS error reduction.

    Tests whether constant-gradient L1 term fixes the near-zero dead zone
    in exp+quad tracking reward. Uses PerDimEnt entropy (default).
    Control: Round 2 PerDimEnt (kl_ub=0.06, no L1).
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_exp_l1"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Experiment: Settling constraints (anti-overshoot for lin_vel + yaw)
# =============================================================================


@configclass
class FullDOFExpSettlingRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Exp: Settling constraints for overshoot reduction.

    Tests whether penalizing acceleration near target (same mechanism as
    rp_vel_settling for attitude) reduces lin_vel and yaw overshoot.
    Adds 2 constraints (12 total). Uses PerDimEnt entropy (default).
    Control: Round 2 PerDimEnt (kl_ub=0.06, 10 constraints).
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_exp_settling"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Round 4: Saturating penalty shapes for SS error without overshoot
# =============================================================================


@configclass
class FullDOFExpTanhRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 4 Exp A: tanh saturating penalty.

    Tests hypothesis from Round 3 Exp1 (L1) analysis: SS error reduction
    is achievable WITHOUT the overshoot side-effect if the penalty gradient
    decays far from zero. tanh penalty: coef·eps·tanh(|e|/eps).
    Control: Round 2 PerDimEnt kl_ub=0.06 (no penalty).
    Comparison: Round 3 Exp1 (L1 ratio=0.15).
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_exp_tanh"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


@configclass
class FullDOFExpArctanRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 4 Exp B: arctan saturating penalty.

    Companion to Tanh experiment. arctan penalty has heavier tail
    (1/(1+x^2)) and weaker near-zero gradient (2·coef/pi vs coef) --
    safer margin against instability.
    Control: Round 2 PerDimEnt kl_ub=0.06 (no penalty).
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_exp_arctan"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Round 5: Constraint-only SS error reduction
# =============================================================================
# Both variants inherit PerDimEnt entropy (arm=0.01, thr=0.001) to match the
# Control run (2026-04-14 perdiment_kl06). This isolates the constraint change
# as the single variable relative to Control baseline.


@configclass
class FullDOFR5RpVelRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 5 GPU1: rp_vel_settling budget 0.20 -> 0.08 (attitude SS attack).

    Env: ALBCEnvR5RpVelSettlingCfg (10 constraints, tightened rp_vel_settling).
    Algorithm: per-dim entropy (same as Control perdim_kl06 run).
    Target: hard DR roll SS 1.68 -> <1.5, pitch SS 1.38 -> <1.3.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r5_rpvel"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


@configclass
class FullDOFR5VelSettlingRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 5 GPU2: activate lin_vel + yaw settling constraints (velocity SS attack).

    Env: ALBCEnvR5VelSettlingCfg (12 constraints, threshold=sigma=0.10, budget=0.015).
    Algorithm: per-dim entropy (same as Control perdim_kl06 run).
    Target: hard DR vx/vy/vz SS 0.046/0.059/0.069 -> ~0.035/0.04/0.05.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r5_velsettling"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Round 6: Axis-specific saturating-penalty reward shape (calibrated coef=0.3)
# =============================================================================
# After R5 settling-constraint failure (yaw catastrophic +1117% on GPU2), revert
# to reward-shape intervention. Unlike Round 4 (coef=1.0 caused vy reward -40%,
# OS +40%), Round 6 uses coef=0.3 (e=0 grad 0.191 arctan / 0.3 tanh) -- near
# L1's 0.15. Applied axis-specifically: attitude-arctan vs velocity-tanh based
# on 5-way winner profile (Arctan roll winner, Tanh vy/yaw winner in Round 4).
# Constraints unchanged from Control (10 terms). Per-dim entropy matches
# perdim_kl06 Control run.


@configclass
class FullDOFR6AttArctanRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 6 GPU1: att_rp Arctan saturating penalty (coef=0.3).

    Env: ALBCEnvR6AttArctanCfg (reward shape change only, Control constraints).
    Algorithm: per-dim entropy (same as Control).
    Target: hard DR roll SS 1.68 -> ~1.35, pitch SS 1.38 -> ~1.25.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r6_attarctan"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


@configclass
class FullDOFR6VelTanhRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 6 GPU2: lin_vel + yaw_vel Tanh saturating penalty (coef=0.3).

    Env: ALBCEnvR6VelTanhCfg (reward shape change only, Control constraints).
    Algorithm: per-dim entropy (same as Control).
    Target: hard DR vy SS 0.059 -> ~0.045, yaw SS 0.025 -> ~0.020 with OS<+20%.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r6_veltanh"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


# =============================================================================
# Round 7: R6-VelTanh refinement experiments
# =============================================================================


@configclass
class FullDOFR7EpsSmoothRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 7 GPU1: Wider tanh eps (0.20) + stronger smoothness (k_s=-0.2).

    Env: ALBCEnvR7EpsSmoothCfg. Config-only change from R6-VelTanh.
    Target: roll medium DR 1.29 -> <1.25, attitude OS ~16 -> ~12-14 deg.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r7_epssmooth"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _FullDOFPolicyCfg()


@configclass
class _R7IntegralPolicyCfg(_FullDOFPolicyCfg):
    """Policy config for integral-obs variant (84D policy obs)."""

    policy_obs_dim: int = 84  # 81 + 3D integral error


@configclass
class _R8IntegralPolicyCfg(_FullDOFPolicyCfg):
    """Policy config for 6D integral-obs variant (87D policy obs)."""

    policy_obs_dim: int = 87  # 81 + 6D integral error


@configclass
class FullDOFR7IntegralRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 7 GPU2: Integral error observation (Hwangbo 2017 pattern).

    Env: ALBCEnvR7IntegralCfg (84D obs = 81 + 3D leaky integral).
    Reward: R6-VelTanh (tanh coef=0.3 on vel). Fresh training (no resume).
    Target: roll/pitch SS reduction via PI-like error accumulation.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r7_integral"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _R7IntegralPolicyCfg()


# =============================================================================
# Round 8: Full 6D integral + overshoot reduction experiments
# =============================================================================


@configclass
class FullDOFR8BaselineRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 8 Baseline: 6D integral observation (87D obs).

    Extends R7-Integral from 3D to 6D. Covers all tracking channels.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r8_baseline"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _R8IntegralPolicyCfg()


@configclass
class FullDOFR8GatedRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 8 Exp1: Error-gated conditional integration.

    Only accumulate integral when |error| < reward sigma.
    Target: reduce overshoot while preserving SS improvement.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r8_gated"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _R8IntegralPolicyCfg()


@configclass
class FullDOFR8FastLeakRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Round 8 Exp2: Faster leak rate (0.95, tau=0.39s).

    Integral drains ~5x faster. Less windup but weaker SS correction.
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 5000
    save_interval = 50
    experiment_name = "full_dof_trpo_r8_fastleak"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ExpPerDimEntAlgorithmCfg()
    policy = _R8IntegralPolicyCfg()


# =============================================================================
# Baseline 1: NoEncoder + TRPO + IPO (ablation)
# =============================================================================


@configclass
class _FullDOFNoEncoderPolicyCfg(RslRlPpoActorCriticCfg):
    """Asymmetric actor-critic without encoder (Baseline 1).

    Architecture (no encoder, 8D action):
        Actor:       o_t(81D) -> MLP[256,128,64] -> 8D
        Critic:      cat([o_t(81D), p_t(24D)]) = 105D -> MLP[512,256,128] -> 1D
        Cost Critic: cat([o_t(81D), p_t(24D)]) = 105D -> MLP[512,256,128] -> K
    """

    class_name: str = "FullDOFActorCriticAsymConstrained"
    init_noise_std: float = 0.7
    actor_obs_normalization: bool = True
    critic_obs_normalization: bool = False
    actor_hidden_dims: list[int] = [256, 128, 64]
    critic_hidden_dims: list[int] = [512, 256, 128]
    activation: str = "elu"
    # Observation dimensions
    policy_obs_dim: int = 81
    privileged_dim: int = 24
    # Cost critic for IPO
    num_constraints: int = 0  # Auto-synced from env config
    cost_critic_hidden_dims: list[int] = [512, 256, 128]


@configclass
class FullDOFNoEncoderRunnerCfg(RslRlOnPolicyRunnerCfg):
    """NoEncoder ablation baseline: TRPO + IPO without encoder.

    Removes encoder only. DR, reward, constraints, action space, and DORAEMON
    are identical to Isaac-FullDOF-TRPO-v0. The actor uses o_t only while the
    critic and cost critic use asymmetric cat([o_t, p_t]).
    """

    class_name: str = "FullDOFConstraintEncoderRunner"
    seed = 30
    num_steps_per_env = 64
    max_iterations = 2500
    save_interval = 50
    experiment_name = "full_dof_trpo_no_encoder"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _FullDOFNoEncoderPolicyCfg()


# =============================================================================
# Baseline 2: Standard PPO (no encoder, no constraint)
# =============================================================================


@configclass
class _FullDOFPPOPolicyCfg(RslRlPpoActorCriticCfg):
    """Standard rsl-rl ActorCritic with asymmetric obs (Baseline 2).

    Architecture (8D action):
        Actor:  o_t(81D)           -> MLP[256,128,64] -> 8D
        Critic: cat(o_t, p_t)=105D -> MLP[512,256,128] -> 1D

    Asymmetric routing is done via Runner.obs_groups -- no custom policy
    class required because rsl-rl ActorCritic auto-computes num_actor_obs
    and num_critic_obs by summing the dims of each obs group in
    obs_groups["policy"] and obs_groups["critic"] respectively.
    """

    class_name: str = "ActorCritic"
    init_noise_std: float = 0.7
    noise_std_type: str = "log"
    actor_obs_normalization: bool = True
    critic_obs_normalization: bool = False
    actor_hidden_dims: list[int] = [256, 128, 64]
    critic_hidden_dims: list[int] = [512, 256, 128]
    activation: str = "elu"


@configclass
class _FullDOFPPOAlgorithmCfg(RslRlPpoAlgorithmCfg):
    """Standard PPO with adaptive KL schedule (Baseline 2).

    No constraint / cost critic -- env still computes constraint costs for
    diagnostics but rsl-rl OnPolicyRunner/PPO silently ignores cost extras.
    """

    class_name: str = "PPO"
    num_learning_epochs: int = 5
    num_mini_batches: int = 4
    learning_rate: float = 3e-4
    schedule: str = "adaptive"
    gamma: float = 0.99
    lam: float = 0.95
    entropy_coef: float = 0.003
    desired_kl: float = 0.01
    max_grad_norm: float = 1.0
    value_loss_coef: float = 1.0
    use_clipped_value_loss: bool = True
    clip_param: float = 0.2


@configclass
class FullDOFPPORunnerCfg(RslRlOnPolicyRunnerCfg):
    """PPO baseline: standard PPO + asymmetric critic, no encoder, no constraint.

    Uses rsl-rl's default OnPolicyRunner (class_name inherited as
    "OnPolicyRunner"). Asymmetric actor/critic observation routing is
    expressed purely through obs_groups: actor receives "policy" (81D)
    only while critic receives cat(["policy", "privileged"]) = 105D.

    DR, reward weights, action space, and DORAEMON are identical to
    Isaac-FullDOF-TRPO-v0. Constraint costs are still computed by the env
    for diagnostics but do not influence the PPO objective.
    """

    seed = 30
    num_steps_per_env = 64
    max_iterations = 2500
    save_interval = 50
    experiment_name = "full_dof_ppo"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _FullDOFPPOAlgorithmCfg()
    policy = _FullDOFPPOPolicyCfg()
