# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for velocity + attitude tracking ALBC environment.

8D action (2D arm + 6D thruster). Roll/pitch: attitude command, yaw: rate command,
linear: velocity command. Single registered task: Isaac-FullDOF-TRPO-v0
"""

from __future__ import annotations

import math

import isaaclab.sim as sim_utils
from isaaclab.envs import DirectRLEnvCfg, ViewerCfg
from isaaclab.scene import InteractiveSceneCfg
from isaaclab.sim import PhysxCfg, SimulationCfg
from isaaclab.terrains import TerrainImporterCfg
from isaaclab.utils import configclass
from isaaclab.utils.noise import GaussianNoiseCfg, NoiseModelWithAdditiveBiasCfg, UniformNoiseCfg

from isaaclab_assets.robots.uuv import (
    HERO_AGENT_ALBC_JOINT_NAMES,
    HERO_AGENT_CFG,
    HeroAgentBuoyHydrodynamicsCfg,
    HeroAgentHydrodynamicsCfg,
    HydrodynamicsCfg,
    OceanCurrentCfg,
    ThrusterCfg,
)

from .doraemon import DoraemonCfg
from .mdp.constraints import (
    ALBCConstraintCfg,
    ConstraintTermCfg,
    attitude_limit_cost,
    cumulative_yaw_cost,
    joint1_position_cost,
    lin_vel_settling_cost,
    manipulability_cost,
    rp_rate_cost,
    rp_vel_settling_cost,
    thruster_utilization_cost,
    torque_limit_cost,
    velocity_limit_cost,
    yaw_rate_cost,
    yaw_settling_cost,
)
from .mdp.rewards import ALBCRewardCfg

# 10 constraint terms: 5 Probabilistic + 5 Average.
# thruster_rate removed: structurally incompatible with entropy_coef>0 (noise alone violates 5x).
# thruster_sat reverted to thruster_util (Average, budget=0.40): original form.
_FULL_DOF_CONSTRAINT_TERMS: list[ConstraintTermCfg] = [
    # --- Probabilistic (5): binary indicator, budget = violation probability ---
    ConstraintTermCfg(func=attitude_limit_cost, params={"limit": 1.396}, budget=0.01, name="attitude"),
    ConstraintTermCfg(func=torque_limit_cost, params={"limit_nm": 9.5}, budget=0.08, name="arm_torque"),
    ConstraintTermCfg(func=velocity_limit_cost, params={"limit_rad_per_s": 4.189}, budget=0.02, name="arm_joint_vel"),
    ConstraintTermCfg(func=joint1_position_cost, params={"limit_rad": 4 * math.pi}, budget=0.01, name="joint1_pos"),
    ConstraintTermCfg(func=cumulative_yaw_cost, params={"limit_rad": 8 * math.pi}, budget=0.01, name="cumul_yaw"),
    # --- Average (5): continuous cost, soft threshold for attitude/velocity tracking ---
    ConstraintTermCfg(func=thruster_utilization_cost, budget=0.40, name="thruster_util"),
    ConstraintTermCfg(func=rp_rate_cost, params={"soft_threshold": 1.0}, budget=0.10, name="rp_rate"),
    ConstraintTermCfg(func=yaw_rate_cost, params={"soft_threshold": 0.7}, budget=0.10, name="yaw_rate"),
    ConstraintTermCfg(func=rp_vel_settling_cost, params={"settling_threshold": 0.087}, budget=0.20, name="rp_vel_settling"),
    ConstraintTermCfg(func=manipulability_cost, params={"w_threshold": 0.3}, budget=0.05, name="manipulability"),
]


@configclass
class HeroAgentThrusterCfg(ThrusterCfg):
    """Hero Agent 6-thruster configuration.

    TAM from hero_agent_control/config/TAM.yaml (verified against actuators.xacro).
    Thruster parameters use BlueROV T200 as baseline; DR covers real-robot differences.

    Layout:
        T0-T3: Horizontal (45-degree vectored) for surge, sway, yaw
        T4-T5: Vertical for heave, pitch
    """

    num_thrusters: int = 6
    max_thrust: float = 50.0
    thrust_coefficient: float = 40.0
    time_constant_up: float = 0.1
    time_constant_down: float = 0.05
    allocation_matrix: tuple[tuple[float, ...], ...] = (
        (0.707, -0.707, 0.707, -0.707, 0.0, 0.0),  # Fx surge
        (-0.707, -0.707, 0.707, 0.707, 0.0, 0.0),  # Fy sway
        (0.0, 0.0, 0.0, 0.0, 1.0, 1.0),  # Fz heave
        (0.007, 0.007, -0.007, -0.007, 0.0, 0.0),  # Mx roll
        (0.007, -0.007, 0.007, -0.007, 0.145, -0.145),  # My pitch
        (0.144, 0.144, 0.144, 0.144, 0.0, 0.0),  # Mz yaw
    )


@configclass
class DomainRandomizationCfg:
    """Configuration for domain randomization in ALBC environments."""

    enable: bool = False

    # -- Hydrodynamic Parameter Scales --
    added_mass_scale: tuple[float, float] = (0.85, 1.15)
    linear_damping_scale: tuple[float, float] = (0.5, 1.5)
    quadratic_damping_scale: tuple[float, float] = (0.5, 1.5)
    volume_scale: tuple[float, float] = (0.9, 1.1)

    # -- Center of Buoyancy/Gravity Offset (meters) --
    cob_offset_x: tuple[float, float] = (-0.01, 0.01)
    cob_offset_y: tuple[float, float] = (-0.01, 0.01)
    cob_offset_z: tuple[float, float] = (-0.02, 0.02)
    cog_offset_x: tuple[float, float] = (-0.01, 0.01)
    cog_offset_y: tuple[float, float] = (-0.01, 0.01)
    cog_offset_z: tuple[float, float] = (-0.02, 0.02)

    # -- Inertia / Mass --
    inertia_scale: tuple[float, float] = (0.75, 1.3)
    body_mass_scale: tuple[float, float] = (0.9, 1.1)
    water_density_range: tuple[float, float] = (995.0, 1025.0)

    # -- Joint Actuator --
    joint_stiffness_range: tuple[float, float] = (40.0, 120.0)
    joint_damping_range: tuple[float, float] = (0.5, 5.0)
    yaw_damping_scale: tuple[float, float] = (0.5, 1.5)
    joint_effort_limit_range: tuple[float, float] = (0.7, 1.0)
    joint_static_friction_range: tuple[float, float] = (0.0, 0.03)
    joint_viscous_friction_range: tuple[float, float] = (0.0, 0.2)

    # -- Payload --
    payload_mass_range: tuple[float, float] = (0.0, 1.0)
    payload_cog_offset_xy_radius: float = 0.10
    payload_cog_offset_z: tuple[float, float] = (-0.03, 0.0)
    buoy_moment_arm: float = 0.180

    # -- Thruster --
    thrust_coefficient_scale: tuple[float, float] = (0.8, 1.2)
    time_constant_scale: tuple[float, float] = (0.8, 1.2)


@configclass
class HardDomainRandomizationCfg(DomainRandomizationCfg):
    """Aggressive DR for encoder training. Widens all ranges significantly.

    Expanded 2026-04-10: DORAEMON saturated all 15 parameters at Beta(1,1)=UNIFORM
    in run 2026-04-09_16-41-45. All bounds widened by ~30-50% beyond prior limits.
    Physics stability constraints: added_mass/inertia ratio < 1.0 (init validation),
    post-DR per-axis clamp (0.95*I) ensures stability.
    """

    enable: bool = True
    added_mass_scale: tuple[float, float] = (0.5, 1.5)
    linear_damping_scale: tuple[float, float] = (0.4, 1.7)
    quadratic_damping_scale: tuple[float, float] = (0.4, 1.7)
    volume_scale: tuple[float, float] = (0.75, 1.25)
    cob_offset_x: tuple[float, float] = (-0.02, 0.02)
    cob_offset_y: tuple[float, float] = (-0.02, 0.02)
    cob_offset_z: tuple[float, float] = (-0.04, 0.04)
    cog_offset_x: tuple[float, float] = (-0.02, 0.02)
    cog_offset_y: tuple[float, float] = (-0.02, 0.02)
    cog_offset_z: tuple[float, float] = (-0.04, 0.04)
    inertia_scale: tuple[float, float] = (0.4, 2.0)
    body_mass_scale: tuple[float, float] = (0.75, 1.25)
    payload_mass_range: tuple[float, float] = (0.0, 3.0)
    payload_cog_offset_xy_radius: float = 0.15
    payload_cog_offset_z: tuple[float, float] = (-0.05, 0.0)
    # -- Joint Actuator --
    joint_stiffness_range: tuple[float, float] = (30.0, 150.0)
    joint_damping_range: tuple[float, float] = (0.3, 7.0)
    # -- Thruster --
    thrust_coefficient_scale: tuple[float, float] = (0.7, 1.3)
    time_constant_scale: tuple[float, float] = (0.7, 1.3)


# ==========================================================================
# 81D Observation Noise Model (26D current proprio + 55D temporal history)
#
# Current Proprioception (26D):
#   Command (6D): vel_cmd_lin(3), ang_cmd(3) [att_rp(2) + yaw_rate(1)]
#   Body State (9D): euler(3), ang_vel(3), lin_vel(3)
#   Arm State (5D): joint_pos(2), joint_vel(2), manipulability(1)
#   Thruster (6D): filtered output (ESC feedback)
#
# Temporal History (55D, stride=3):
#   Joint tracking x3 steps (12D): joint_pos_error(2), joint_vel(2)
#   Body tracking x3 steps (27D): lin_vel_err(3), ang_err(3) [att_rp(2)+yaw_rate(1)], rpy(3)
#   Action x2 steps (16D): full_action(8)
# ==========================================================================
_OBS_NOISE_STD = tuple(
    # --- Current Proprioception (26D) ---
    [0.0] * 3  # vel_cmd_lin (our command, no noise)
    + [0.0] * 3  # ang_cmd [att_rp(2) + yaw_rate(1)] (our command, no noise)
    + [0.02] * 3  # euler
    + [0.04] * 3  # ang_vel
    + [0.04] * 3  # lin_vel
    + [0.02] * 2  # joint_pos
    + [0.04] * 2  # joint_vel
    + [0.0]  # manipulability (computed)
    + [0.02] * 6  # thruster_state (ESC feedback)
    # --- Joint Tracking History (12D = 4D x 3 steps) ---
    + ([0.02] * 2 + [0.04] * 2) * 3  # joint_pos_error + joint_vel
    # --- Body Tracking History (27D = 9D x 3 steps) ---
    + ([0.04] * 3 + [0.04] * 3 + [0.02] * 3) * 3  # lin_vel_err + ang_err [att_rp+yaw_rate] + rpy
    # --- Action History (16D = 8D x 2 steps) ---
    + [0.0] * 16  # actions (our command, no noise)
)

_OBS_BIAS_MIN = tuple(
    # --- Current Proprioception (26D) ---
    [0] * 3  # vel_cmd_lin
    + [0] * 3  # ang_cmd
    + [-0.02] * 3  # euler
    + [-0.03] * 3  # ang_vel
    + [-0.02] * 3  # lin_vel
    + [-0.02] * 2  # joint_pos
    + [-0.03] * 2  # joint_vel
    + [0]  # manipulability
    + [-0.01] * 6  # thruster
    # --- Joint Tracking History (12D) ---
    + ([-0.02] * 2 + [-0.03] * 2) * 3
    # --- Body Tracking History (27D) ---
    + ([-0.02] * 3 + [-0.04] * 3 + [-0.02] * 3) * 3  # lin_vel_err + ang_err [att_rp+yaw_rate] + rpy
    # --- Action History (16D) ---
    + [0] * 16
)

_OBS_BIAS_MAX = tuple(
    # --- Current Proprioception (26D) ---
    [0] * 3  # vel_cmd_lin
    + [0] * 3  # ang_cmd
    + [0.02] * 3  # euler
    + [0.03] * 3  # ang_vel
    + [0.02] * 3  # lin_vel
    + [0.02] * 2  # joint_pos
    + [0.03] * 2  # joint_vel
    + [0]  # manipulability
    + [0.01] * 6  # thruster
    # --- Joint Tracking History (12D) ---
    + ([0.02] * 2 + [0.03] * 2) * 3
    # --- Body Tracking History (27D) ---
    + ([0.02] * 3 + [0.04] * 3 + [0.02] * 3) * 3  # lin_vel_err + ang_err [att_rp+yaw_rate] + rpy
    # --- Action History (16D) ---
    + [0] * 16
)


@configclass
class ALBCEnvCfg(DirectRLEnvCfg):
    """Velocity + attitude tracking ALBC environment configuration.

    8D action (2D arm delta + 6D thruster), 81D observation (26D current + 55D history),
    24D privileged. TRPO + IPO + Asymmetric Encoder with 10 constraints (5 prob + 5 avg).

    Roll/pitch: attitude command (+-30 deg, exp kernel reward).
    Yaw: rate command (+-0.5 rad/s, quadratic penalty).
    Linear: velocity command (+-0.5 m/s, quadratic penalty).
    """

    # ==========================================================================
    # Environment Settings
    # ==========================================================================
    episode_length_s: float = 30.0
    decimation: int = 4
    action_space: int = 8  # 2D arm delta + 6D thruster
    observation_space: int = 81  # 26D current proprio + 55D history (see observations.py)
    # Breakdown: cmd(6) + body(9) + arm(5) + thruster(6) = 26D current
    #            + joint_hist(12) + body_hist(27) + action_hist(16) = 55D history
    state_space: int = 24  # Privileged info (see observations.py compute_privileged_obs)
    # Integral error observation (Hwangbo 2017 pattern)
    use_integral_obs: bool = False  # When True, appends 3D leaky-integral to policy obs
    integral_leak: float = 0.99  # Leaky integrator decay: I_{t+1} = leak * I_t + err * dt
    integral_clamp: float = 2.0  # Windup prevention: clamp |I| <= this value
    debug_vis: bool = False

    viewer: ViewerCfg = ViewerCfg(eye=(0.0, 0.0, 12.0), lookat=(0.0, 0.0, 4.5))

    # ==========================================================================
    # Simulation
    # ==========================================================================
    sim: SimulationCfg = SimulationCfg(
        dt=0.005,
        render_interval=4,
        physics_material=sim_utils.RigidBodyMaterialCfg(
            friction_combine_mode="multiply",
            restitution_combine_mode="multiply",
            static_friction=0.5,
            dynamic_friction=0.5,
            restitution=0.0,
        ),
        physx=PhysxCfg(enable_external_forces_every_iteration=True),
    )

    scene: InteractiveSceneCfg = InteractiveSceneCfg(
        num_envs=4096, env_spacing=4.0, replicate_physics=True, clone_in_fabric=False
    )

    terrain: TerrainImporterCfg | None = None

    # ==========================================================================
    # Robot and Hydrodynamics
    # ==========================================================================
    robot = HERO_AGENT_CFG.replace(prim_path="/World/envs/env_.*/Robot")
    hydrodynamics: HydrodynamicsCfg = HeroAgentHydrodynamicsCfg()
    buoy_hydrodynamics: HydrodynamicsCfg = HeroAgentBuoyHydrodynamicsCfg()
    ocean_current: OceanCurrentCfg = OceanCurrentCfg(
        max_velocity=(0.5, 0.5, 0.25, 0.0, 0.0, 0.0),
        noise_scale=(0.1, 0.1, 0.05, 0.0, 0.0, 0.0),
    )
    thrusters: HeroAgentThrusterCfg | None = HeroAgentThrusterCfg()

    # ==========================================================================
    # ALBC Joint Control
    # ==========================================================================
    albc_joint_names: list[str] = HERO_AGENT_ALBC_JOINT_NAMES
    control_decimation: int = 1
    initial_joint_pos_range: tuple[float, float] = (-math.pi, math.pi)
    nominal_joint_pos: tuple[float, float] = (0.0, math.pi / 2.0)
    delta_scale: float = 0.10

    # ==========================================================================
    # Temporal History (ring buffer, recorded every ``hist_stride`` control steps)
    # ==========================================================================
    hist_len: int = 3
    """Number of past timesteps stored in the history ring buffer."""
    hist_stride: int = 3
    """Record every N-th control step. Effective span = hist_len * hist_stride * step_dt."""
    hist_feature_dim: int = 21
    """Features per timestep: joint_tracking(4) + body_tracking(9) + action(8)."""
    hist_action_len: int = 2
    """Number of action history steps to include in observation (newest N of hist_len)."""

    # ==========================================================================
    # Task: Command Tracking (velocity + attitude)
    # ==========================================================================
    vel_cmd_lin_range: tuple[float, float] = (-0.5, 0.5)
    """Linear velocity command range per axis (m/s, body frame)."""
    att_cmd_rp_range: tuple[float, float] = (-math.pi / 6.0, math.pi / 6.0)
    """Roll/pitch attitude command range (radians). +-30 degrees."""
    yaw_rate_cmd_range: tuple[float, float] = (-0.5, 0.5)
    """Yaw rate command range (rad/s, body frame)."""
    vel_cmd_resample_steps: int = 250
    """Resample velocity command every N steps (250 = 5s at 50Hz)."""
    vel_cmd_zero_prob: float = 0.1
    """Probability of zeroing velocity command per env on each resample."""

    play_mode: bool = False
    """Play/eval mode: disable command resampling, fix all commands to zero (hovering)."""

    reward: ALBCRewardCfg = ALBCRewardCfg()

    # ==========================================================================
    # Mid-Episode Dynamics
    # ==========================================================================
    # -- Payload Toggle (binary pick/place event) --
    payload_toggle_steps: int = 0
    """Toggle payload after N steps (0 = disabled, -1 = episode midpoint)."""
    payload_start_with_prob: float = 0.5
    """Probability that episode starts WITH payload (mass > 0)."""
    payload_no_toggle_prob: float = 0.2
    """Probability that payload stays constant (no mid-episode toggle)."""
    # -- Ocean Current OU Drift --
    ou_theta: float = 0.15
    """OU mean reversion rate (1/s). 0.15 gives ~6.7s time constant."""
    ou_sigma: float = 0.05
    """OU noise scale (m/s per sqrt(s)). 0.05 gives steady-state std ~0.091 m/s."""
    ou_enable: bool = False
    """Enable OU process drift on ocean current (False = fixed per episode)."""

    # ==========================================================================
    # Termination
    # ==========================================================================
    max_angular_velocity: float = math.pi
    max_attitude_angle: float = math.pi / 2.0
    max_linear_velocity: float = 2.0  # m/s

    # ==========================================================================
    # Domain Randomization
    # ==========================================================================
    randomization: HardDomainRandomizationCfg = HardDomainRandomizationCfg()
    doraemon: DoraemonCfg = DoraemonCfg(enable=True, kl_ub=0.06, performance_lb=90.0, step_interval=250)

    # ==========================================================================
    # Payload
    # ==========================================================================
    payload_mass: float = 0.5
    payload_attachment_offset: tuple[float, float, float] = (0.0, 0.0, -0.05)

    # ==========================================================================
    # Observation Noise (81D)
    # ==========================================================================
    observation_noise_model: NoiseModelWithAdditiveBiasCfg = NoiseModelWithAdditiveBiasCfg(
        noise_cfg=GaussianNoiseCfg(mean=0.0, std=_OBS_NOISE_STD),
        bias_noise_cfg=UniformNoiseCfg(n_min=_OBS_BIAS_MIN, n_max=_OBS_BIAS_MAX),
    )

    # ==========================================================================
    # Constraints (10 terms: 5 probabilistic + 5 average)
    # ==========================================================================
    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_FULL_DOF_CONSTRAINT_TERMS)


# =============================================================================
# Experiment Env Configs
# =============================================================================

# Settling constraint terms (anti-overshoot for lin_vel and yaw)
_SETTLING_CONSTRAINT_TERMS: list[ConstraintTermCfg] = _FULL_DOF_CONSTRAINT_TERMS + [
    ConstraintTermCfg(
        func=lin_vel_settling_cost,
        params={"settling_threshold": 0.04},
        budget=0.005,
        name="lin_vel_settling",
    ),
    ConstraintTermCfg(
        func=yaw_settling_cost,
        params={"settling_threshold": 0.04},
        budget=0.005,
        name="yaw_settling",
    ),
]


@configclass
class ALBCEnvL1Cfg(ALBCEnvCfg):
    """Exp 1: L1 penalty for SS error reduction.

    Enables linear penalty term in lin_vel and yaw_vel tracking rewards.
    L1 provides constant gradient at e=0, fixing the dead zone where
    exp+quad gradients vanish. Ratio 0.15 is low enough to avoid the
    'moderate error dead zone' that caused L1 to be disabled originally.
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_lin_ratio=0.15,
        yaw_vel_lin_ratio=0.15,
    )


@configclass
class ALBCEnvSettlingCfg(ALBCEnvCfg):
    """Exp 2: Settling constraints for overshoot reduction.

    Adds lin_vel_settling_cost and yaw_settling_cost constraints.
    These penalize acceleration (velocity change) when near the target,
    mirroring the proven rp_vel_settling_cost mechanism that keeps
    attitude overshoot under control.
    """

    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_SETTLING_CONSTRAINT_TERMS)


@configclass
class ALBCEnvTanhCfg(ALBCEnvCfg):
    """Round 4 Exp A: Saturating tanh penalty for SS error.

    Replaces L1 |e| with coef·eps·tanh(|e|/eps). Non-zero gradient at e=0
    (= coef, kills SS error dead zone), but penalty gradient decays as
    sech²(|e|/eps) so far-field force vanishes. This avoids the constant
    far-field force that caused Round 3 Exp1 (L1) to increase overshoot.

    Coefs chosen from gradient analysis:
      coef=1.0: grad at 0 ~16% of exp kernel peak (strong near-zero, weak far)
      eps=sigma=0.10: saturation kicks in at the exp kernel's active region

    Control: Round 2 PerDimEnt kl_ub=0.06 (no penalty).
    Comparison: Round 3 Exp1 (L1 ratio=0.15) showed SS -15-24% but overshoot +25-86%.
    Tanh predicted SS reduction ~50% with overshoot near baseline.
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_tanh_coef=1.0,
        lin_vel_tanh_eps=0.10,
        yaw_vel_tanh_coef=1.0,
        yaw_vel_tanh_eps=0.10,
    )


@configclass
class ALBCEnvArctanCfg(ALBCEnvCfg):
    """Round 4 Exp B: Saturating arctan penalty for SS error.

    Replaces L1 |e| with coef·eps·(2/pi)·arctan(|e|/eps). Similar motivation
    to Tanh variant but with smoother 1/(1+(e/eps)^2) decay (heavier tail).
    grad at 0 = 2·coef/pi (~0.637 for coef=1.0, about 10.5% of exp kernel peak).
    Safer margin against overshoot at the cost of weaker near-zero pressure.

    Serves as companion experiment to Tanh (ALBCEnvTanhCfg) to compare
    shape decay profiles. If Tanh creates instability, Arctan is the safer fallback.
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_arctan_coef=1.0,
        lin_vel_arctan_eps=0.10,
        yaw_vel_arctan_coef=1.0,
        yaw_vel_arctan_eps=0.10,
    )


# =============================================================================
# Round 5: Constraint-only SS error reduction (no reward changes)
# =============================================================================
# Diagnostic: Round 4 showed rp_vel_settling at 33% of budget utilization
# (cost_return ~6.6 vs d_k 20.0), lin_vel_settling/yaw_settling not registered.
# Strategy: attack SS error via constraint tuning, keep reward identical to
# Control (pure exp+quad, no L1/tanh/arctan). Two orthogonal interventions.

# GPU1 variant: tighten rp_vel_settling budget from 0.20 to 0.08 (2.5x tighter).
# Targets roll/pitch SS error (hard DR 1.68/1.38 -> <1.25 goal).
_R5_RP_VEL_CONSTRAINT_TERMS: list[ConstraintTermCfg] = [
    ConstraintTermCfg(func=attitude_limit_cost, params={"limit": 1.396}, budget=0.01, name="attitude"),
    ConstraintTermCfg(func=torque_limit_cost, params={"limit_nm": 9.5}, budget=0.08, name="arm_torque"),
    ConstraintTermCfg(func=velocity_limit_cost, params={"limit_rad_per_s": 4.189}, budget=0.02, name="arm_joint_vel"),
    ConstraintTermCfg(func=joint1_position_cost, params={"limit_rad": 4 * math.pi}, budget=0.01, name="joint1_pos"),
    ConstraintTermCfg(func=cumulative_yaw_cost, params={"limit_rad": 8 * math.pi}, budget=0.01, name="cumul_yaw"),
    ConstraintTermCfg(func=thruster_utilization_cost, budget=0.40, name="thruster_util"),
    ConstraintTermCfg(func=rp_rate_cost, params={"soft_threshold": 1.0}, budget=0.10, name="rp_rate"),
    ConstraintTermCfg(func=yaw_rate_cost, params={"soft_threshold": 0.7}, budget=0.10, name="yaw_rate"),
    # Tightened: 0.20 -> 0.08. Expected to move rp_vel_settling utilization 33% -> ~80%.
    ConstraintTermCfg(func=rp_vel_settling_cost, params={"settling_threshold": 0.087}, budget=0.08, name="rp_vel_settling"),
    ConstraintTermCfg(func=manipulability_cost, params={"w_threshold": 0.3}, budget=0.05, name="manipulability"),
]

# GPU2 variant: activate lin_vel + yaw settling constraints, threshold matched to reward sigma.
# Targets velocity SS error (hard DR vx/vy/vz 0.046/0.059/0.069 -> <0.04 goal).
# Threshold = sigma = 0.10 matches rp_vel_settling design (threshold ~= att sigma 0.087 rad ~= 5deg).
# Budget 0.015 per step = 3x original 0.005 to accommodate the 2.5x larger active region.
_R5_VEL_SETTLING_CONSTRAINT_TERMS: list[ConstraintTermCfg] = _FULL_DOF_CONSTRAINT_TERMS + [
    ConstraintTermCfg(
        func=lin_vel_settling_cost,
        params={"settling_threshold": 0.10},  # = lin_vel_sigma (was 0.04)
        budget=0.015,  # was 0.005
        name="lin_vel_settling",
    ),
    ConstraintTermCfg(
        func=yaw_settling_cost,
        params={"settling_threshold": 0.10},  # = yaw_vel_sigma (was 0.04)
        budget=0.015,  # was 0.005
        name="yaw_settling",
    ),
]


@configclass
class ALBCEnvR5RpVelSettlingCfg(ALBCEnvCfg):
    """Round 5 GPU1: Tightened rp_vel_settling budget for attitude SS.

    Baseline: Control (pure exp+quad reward, matches perdim_kl06 run).
    Change: rp_vel_settling budget 0.20 -> 0.08 (2.5x tighter).

    Rationale: Round 4 analysis showed rp_vel_settling cost_return ~6.6 vs
    d_k 20.0 (33% utilization). Budget was slack, constraint not actively
    pushing policy toward lower angular velocity near target. Tightening
    to 0.08 brings utilization closer to 80%, activating the settling
    mechanism designed to reduce roll/pitch SS error.

    No reward changes (6 reward items preserved per user constraint).
    Expected: roll SS 1.68 -> 1.3-1.5, pitch SS 1.38 -> 1.2-1.3 on hard DR.
    """

    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_R5_RP_VEL_CONSTRAINT_TERMS)


@configclass
class ALBCEnvR5VelSettlingCfg(ALBCEnvCfg):
    """Round 5 GPU2: Activate lin_vel + yaw settling constraints for velocity SS.

    Baseline: Control (pure exp+quad reward, matches perdim_kl06 run).
    Change: 10 -> 12 constraints. Add lin_vel_settling + yaw_settling with
            threshold=sigma=0.10, budget=0.015.

    Rationale: Round 4 runs all used only 10 constraints (rp_vel_settling for
    attitude only). lin_vel_settling and yaw_settling existed in code but were
    inactive. Original threshold 0.04 < Control hard DR SS (0.06-0.07) caused
    chicken-egg problem (constraint never activates). Matching threshold to
    reward sigma (0.10) follows rp_vel_settling's design principle (threshold
    ~= att_rp_sigma 0.087) and guarantees activation in practical SS regime.

    No reward changes (6 reward items preserved per user constraint).
    Expected: vx/vy/vz hard SS 0.046/0.059/0.069 -> ~0.035/0.04/0.05.
    """

    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_R5_VEL_SETTLING_CONSTRAINT_TERMS)


# =============================================================================
# Round 6: Axis-specific saturating penalty (reward shape calibration)
# =============================================================================
# Diagnosis from Rounds 3/4/5: settling constraints are a structural dead end
# (Round 3 + R5 GPU1 + R5 GPU2 all failed). 5-way eval showed reward shape has
# real axis-specific effects -- Arctan was the only winner for roll SS (-15%),
# Tanh/L1 were winners for vy/yaw SS (-17~-26%). Round 4 coef=1.0 was too strong
# (e=0 grad 1.0/0.637) and caused vy reward -40% + OS +40%. This round retries
# with coef calibrated to L1's grad=0.15 region (coef=0.3: e=0 grad 0.191/0.3).
#
# Constraints unchanged (10 terms, Control's _FULL_DOF_CONSTRAINT_TERMS). Only
# reward shape parameter changes per experiment. Single-variable control.


@configclass
class ALBCEnvR6AttArctanCfg(ALBCEnvCfg):
    """Round 6 GPU1: Arctan saturating penalty on attitude only.

    Hypothesis: Arctan (e=0 grad = 2*coef/pi = 0.191 at coef=0.3) breaks the
    reward dead zone on attitude while preserving Control's lin_vel/yaw_vel
    shape. Round 4's Arctan on lin/yaw was the roll SS winner (1.42, -15% vs
    Control 1.68); this re-applies the same shape to attitude directly.

    Change: att_rp_arctan_coef 0 -> 0.3, att_rp_arctan_eps = 0.10 (= att_rp_sigma).
    No other reward changes. Constraint set = Control (10 terms, rp_vel_settling
    budget=0.20 retained per user decision).

    Expected (hard DR):
      roll  SS: 1.68 -> ~1.35  (Round 4 Arctan lin/yaw case precedent: 1.42)
      pitch SS: 1.38 -> ~1.25  (structural dead-zone relief)
      vy/yaw SS: Control +/-5% (no change in lin/yaw reward)
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        att_rp_arctan_coef=0.3,
        att_rp_arctan_eps=0.10,  # = att_rp_sigma
    )


@configclass
class ALBCEnvR6VelTanhCfg(ALBCEnvCfg):
    """Round 6 GPU2: Tanh saturating penalty on lin_vel + yaw_vel only.

    Hypothesis: Calibrated Tanh (e=0 grad = coef = 0.3; 1/3 of Round 4's 1.0)
    gives velocity SS improvement without Round 4's OS blowup (vy OS was +40%).
    Round 4 Tanh at coef=1.0 achieved vy SS 0.045 (-22%) but lost 40% lin_vel
    reward. Coef=0.3 is near L1's grad=0.15 level, expected to retain most SS
    benefit at much lower reward magnitude cost.

    Change: lin_vel_tanh_coef 0 -> 0.3, yaw_vel_tanh_coef 0 -> 0.3.
    No other reward changes. Constraint set = Control (10 terms).

    Expected (hard DR):
      vy  SS: 0.059 -> ~0.045 (Round 4 Tanh matched)
      yaw SS: 0.025 -> ~0.020 (Round 4 Tanh matched)
      vy  OS: Control + at most 15-20%  (vs Round 4 Tanh's +40%, calibrated)
      attitude SS: Control +/-5% (no change)
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_tanh_coef=0.3,
        lin_vel_tanh_eps=0.10,  # = lin_vel_sigma
        yaw_vel_tanh_coef=0.3,
        yaw_vel_tanh_eps=0.10,  # = yaw_vel_sigma
    )


# =============================================================================
# Round 7: R6-VelTanh refinement experiments
# =============================================================================


@configclass
class ALBCEnvR7EpsSmoothCfg(ALBCEnvCfg):
    """Round 7 GPU1: Wider tanh eps + stronger smoothness penalty.

    Base: R6-VelTanh (tanh coef=0.3 on lin_vel + yaw_vel).
    Changes from R6-VelTanh:
      1. lin_vel_tanh_eps  0.10 -> 0.20: wider saturation scale reduces penalty
         at moderate velocity errors (off-equilibrium coupling zone ~0.1-0.2 m/s).
         This should reduce roll SS degradation at non-zero targets.
      2. yaw_vel_tanh_eps  0.10 -> 0.20: same rationale for yaw.
      3. k_s  -0.1 -> -0.2: doubled smoothness penalty suppresses action jerk,
         reducing attitude overshoot (currently ~100% for +/-15 deg steps).

    Expected vs R6-VelTanh:
      roll SS (medium): 1.29 -> <1.25 (eps widening reduces cross-axis interference)
      attitude OS: ~16 deg -> ~12-14 deg (smoothness penalty)
      vy/yaw SS: may degrade slightly (wider eps = weaker near-zero gradient)
    """

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_tanh_coef=0.3,
        lin_vel_tanh_eps=0.20,  # widened from 0.10
        yaw_vel_tanh_coef=0.3,
        yaw_vel_tanh_eps=0.20,  # widened from 0.10
        k_s=-0.2,  # doubled smoothness penalty
    )


@configclass
class ALBCEnvR7IntegralCfg(ALBCEnvCfg):
    """Round 7 GPU2: Integral error observation (Hwangbo 2017 pattern).

    Adds 3D leaky-integrated error to policy observation:
      I_{t+1} = 0.99 * I_t + [roll_err, pitch_err, vy_err] * dt
    Clamped to [-2, 2] for windup prevention.

    The integral provides the policy with cumulative error information,
    enabling PI-like control that drives SS error toward zero. Without it,
    the policy has no signal distinguishing "just arrived at target" from
    "stuck at 1 deg offset for 100 steps".

    Changes from base:
      observation_space: 81 -> 84 (3D integral appended)
      use_integral_obs: True
      Reward: R6-VelTanh (tanh coef=0.3 on lin_vel + yaw_vel)

    Expected:
      roll/pitch SS: significant improvement (integral drives SS -> 0)
      vy/yaw SS: additional improvement on top of R6-VelTanh
      Attitude OS: neutral or slightly worse (integral may cause overshoot initially)
    """

    observation_space: int = 84  # 81 + 3D integral
    use_integral_obs: bool = True
    integral_leak: float = 0.99
    integral_clamp: float = 2.0

    # Extend noise vectors from 81D to 84D (integral dims get zero noise: internal computation)
    observation_noise_model: NoiseModelWithAdditiveBiasCfg = NoiseModelWithAdditiveBiasCfg(
        noise_cfg=GaussianNoiseCfg(mean=0.0, std=tuple(list(_OBS_NOISE_STD) + [0.0] * 3)),
        bias_noise_cfg=UniformNoiseCfg(
            n_min=tuple(list(_OBS_BIAS_MIN) + [0] * 3),
            n_max=tuple(list(_OBS_BIAS_MAX) + [0] * 3),
        ),
    )

    reward: ALBCRewardCfg = ALBCRewardCfg(
        lin_vel_tanh_coef=0.3,
        lin_vel_tanh_eps=0.10,
        yaw_vel_tanh_coef=0.3,
        yaw_vel_tanh_eps=0.10,
    )
