# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""RSL-RL agent configurations for velocity tracking ALBC environment.

Single pipeline: TRPO + IPO + Asymmetric Encoder (8D action, 81D obs).
"""

import rsl_rl.runners.on_policy_runner as _runner_module

from isaaclab.utils import configclass

from isaaclab_rl.rsl_rl import RslRlOnPolicyRunnerCfg, RslRlPpoActorCriticCfg

# Register custom classes in RSL-RL runner module namespace.
from ..algorithms import ConstraintTRPO
from ..encoder import ActorCriticEncoder
from ..runners import ConstraintEncoderRunner

_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
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

    Three optimizer groups:
    - Actor + Encoder: TRPO natural gradient (trust region)
    - Sigma (log_std): decoupled Adam (score-function gradient, std_lr=1e-3)
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

    # Sigma (decoupled from TRPO)
    min_std: float = 0.01
    std_lr: float = 1e-3


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
