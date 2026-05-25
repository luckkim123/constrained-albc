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

_runner_module.ALBCActorCriticEncoder = ActorCriticEncoder
_runner_module.ALBCActorCriticAsymConstrained = ActorCriticAsymConstrained
_runner_module.ALBCConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.ALBCConstraintTRPO = ConstraintTRPO


# =============================================================================
# Encoder Bounds (24D privileged obs, static min-max normalization)
# =============================================================================

# 24D non-redundant privileged obs bounds from HardDomainRandomizationCfg.
# Each pair is (lower, upper) with ~10% margin beyond Hard DR range.
# Layout: hydro(7) + dynamics(5) + payload(4) + actuator(4) + env(4)
#
# Base values from ALBCHydrodynamicsCfg:
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
    # r13_A: latent=9 (r11_emabias config, rank #1 across 24 runs).
    # r13_B tests latent=16 with same k_bias=-2.0 to resolve whether latent=16
    # + full-strength emabias is better than r11_emabias or replicates r12_baseline failure.
    encoder_latent_dim: int = 9
    encoder_activation: str = "elu"
    encoder_obs_normalization: bool = False
    # Observation dimensions
    policy_obs_dim: int = 87  # 26D current proprio + 55D temporal history + 6D integral
    privileged_dim: int = 24


@configclass
class _ALBCPolicyCfg(_EncoderPolicyCfg):
    """Asymmetric encoder with cost critic for TRPO + IPO.

    Architecture (24D->9D encoder, 8D action):
        Encoder: p_t(24D) -> static_minmax -> MLP[256,128,64] -> LN -> softsign -> z(9D)
        Actor:   cat([o_t(87D), z(9D)]) = 96D -> MLP[256,128,64] -> 8D
        Critic:  cat([o_t(87D), z(9D), p_t(24D)]) = 120D -> MLP[512,256,128] -> 1D
        Cost:    same 120D input -> MLP[512,256,128] -> K (multi-head)
    """

    class_name: str = "ALBCActorCriticEncoder"
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

    class_name: str = "ALBCConstraintTRPO"

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
class _BaseALBCRunnerCfg(RslRlOnPolicyRunnerCfg):
    """Shared ALBC runner constants (de-dup base; no behavior change).

    Runners below inherit these and override only what differs (class_name,
    experiment_name, obs_groups, algorithm, policy, normalize_value).
    """

    seed = 30
    num_steps_per_env = 64
    max_iterations = 2500
    save_interval = 50


@configclass
class ALBCTRPORunnerCfg(_BaseALBCRunnerCfg):
    """Velocity tracking TRPO + IPO + Asymmetric Encoder runner.

    8D action (2D arm + 6D wrench), 81D policy obs, 24D privileged obs.
    """

    class_name: str = "ALBCConstraintEncoderRunner"
    experiment_name = "albc_trpo"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    normalize_value: bool = False

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _ALBCPolicyCfg()


# =============================================================================
# Baseline 1: NoEncoder + TRPO + IPO (ablation)
# =============================================================================


@configclass
class _ALBCNoEncoderPolicyCfg(RslRlPpoActorCriticCfg):
    """Asymmetric actor-critic without encoder (Baseline 1).

    Architecture (no encoder, 8D action):
        Actor:       o_t(87D) -> MLP[256,128,64] -> 8D
        Critic:      cat([o_t(87D), p_t(24D)]) = 111D -> MLP[512,256,128] -> 1D
        Cost Critic: cat([o_t(87D), p_t(24D)]) = 111D -> MLP[512,256,128] -> K
    """

    class_name: str = "ALBCActorCriticAsymConstrained"
    init_noise_std: float = 0.7
    actor_obs_normalization: bool = True
    critic_obs_normalization: bool = False
    actor_hidden_dims: list[int] = [256, 128, 64]
    critic_hidden_dims: list[int] = [512, 256, 128]
    activation: str = "elu"
    # Observation dimensions
    policy_obs_dim: int = 87
    privileged_dim: int = 24
    # Cost critic for IPO
    num_constraints: int = 0  # Auto-synced from env config
    cost_critic_hidden_dims: list[int] = [512, 256, 128]


@configclass
class ALBCNoEncoderRunnerCfg(_BaseALBCRunnerCfg):
    """NoEncoder ablation baseline: TRPO + IPO without encoder.

    Removes encoder only. DR, reward, constraints, action space, and DORAEMON
    are identical to Isaac-ConstrainedALBC-TRPO-v0. The actor uses o_t only while the
    critic and cost critic use asymmetric cat([o_t, p_t]).
    """

    class_name: str = "ALBCConstraintEncoderRunner"
    experiment_name = "albc_ablation"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy", "privileged"],
        "critic": ["policy", "privileged"],
    }

    algorithm = RslRlConstraintTRPOAlgorithmCfg()
    policy = _ALBCNoEncoderPolicyCfg()


# =============================================================================
# Baseline 2: Standard PPO (no encoder, no constraint)
# =============================================================================


@configclass
class _ALBCPPOPolicyCfg(RslRlPpoActorCriticCfg):
    """Standard rsl-rl ActorCritic with asymmetric obs (Baseline 2).

    Architecture (8D action):
        Actor:  o_t(87D)           -> MLP[256,128,64] -> 8D
        Critic: cat(o_t, p_t)=111D -> MLP[512,256,128] -> 1D

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
class _ALBCPPOAlgorithmCfg(RslRlPpoAlgorithmCfg):
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
class ALBCPPORunnerCfg(_BaseALBCRunnerCfg):
    """PPO baseline: standard PPO + asymmetric critic, no encoder, no constraint.

    Uses OnPolicyDoraemonRunner (OnPolicyRunner + DORAEMON curriculum hook)
    so the DR schedule matches Isaac-ConstrainedALBC-TRPO-v0 — without this override
    stock OnPolicyRunner would never step the env's DORAEMON scheduler,
    freezing the Beta distribution at ``init_concentration=30`` and
    confounding the algorithm ablation with a DR-curriculum ablation.

    Asymmetric actor/critic observation routing is expressed purely through
    obs_groups: actor receives "policy" (81D) only while critic receives
    cat(["policy", "privileged"]) = 105D.

    DR, reward weights, action space, and DORAEMON hyperparameters are
    identical to Isaac-ConstrainedALBC-TRPO-v0 (all variants inherit ALBCEnvCfg).
    Constraint costs are still computed by the env for diagnostics but do
    not influence the PPO objective.
    """

    class_name: str = "OnPolicyDoraemonRunner"
    experiment_name = "albc_ablation"
    obs_groups: dict[str, list[str]] = {
        "policy": ["policy"],
        "critic": ["policy", "privileged"],
    }

    algorithm = _ALBCPPOAlgorithmCfg()
    policy = _ALBCPPOPolicyCfg()
