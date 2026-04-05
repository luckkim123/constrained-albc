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
    manipulability_cost,
    rp_rate_cost,
    rp_vel_settling_cost,
    thruster_utilization_cost,
    torque_limit_cost,
    velocity_limit_cost,
    yaw_rate_cost,
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
    ConstraintTermCfg(func=yaw_rate_cost, params={"soft_threshold": 1.0}, budget=0.10, name="yaw_rate"),
    ConstraintTermCfg(func=rp_vel_settling_cost, budget=0.20, name="rp_vel_settling"),
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
    """Aggressive DR for encoder training. Widens all ranges significantly."""

    enable: bool = True
    added_mass_scale: tuple[float, float] = (0.6, 1.4)
    volume_scale: tuple[float, float] = (0.75, 1.25)
    cob_offset_x: tuple[float, float] = (-0.02, 0.02)
    cob_offset_y: tuple[float, float] = (-0.02, 0.02)
    cob_offset_z: tuple[float, float] = (-0.04, 0.04)
    cog_offset_x: tuple[float, float] = (-0.02, 0.02)
    cog_offset_y: tuple[float, float] = (-0.02, 0.02)
    cog_offset_z: tuple[float, float] = (-0.04, 0.04)
    inertia_scale: tuple[float, float] = (0.5, 1.8)
    body_mass_scale: tuple[float, float] = (0.75, 1.25)
    payload_mass_range: tuple[float, float] = (0.0, 2.0)
    payload_cog_offset_xy_radius: float = 0.15
    payload_cog_offset_z: tuple[float, float] = (-0.05, 0.0)
    # -- Joint Actuator (widened for hard DR) --
    joint_stiffness_range: tuple[float, float] = (30.0, 150.0)
    joint_damping_range: tuple[float, float] = (0.3, 7.0)
    # -- Thruster (widened for hard DR) --
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

    Roll/pitch: attitude command (+-45 deg, exp kernel reward).
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
    att_cmd_rp_range: tuple[float, float] = (-math.pi / 4.0, math.pi / 4.0)
    """Roll/pitch attitude command range (radians). +-45 degrees."""
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
    doraemon: DoraemonCfg = DoraemonCfg(enable=True, kl_ub=1.5, performance_lb=200.0, step_interval=250)

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
    # Constraints (11 terms: 6 probabilistic + 5 average)
    # ==========================================================================
    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_FULL_DOF_CONSTRAINT_TERMS)
