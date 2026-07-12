# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for attitude-only ALBC environment.

8D action (2D arm + 6D thruster). Roll/pitch: attitude command, yaw: rate command.
No linear velocity tracking. 69D observation, 28D privileged.
Single registered task: Isaac-ConstrainedALBC-TRPO-v0
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

from marinelab.assets import (
    ALBC_CFG,
    ALBC_JOINT_NAMES,
    ALBCBuoyHydrodynamicsCfg,
    ALBCHydrodynamicsCfg,
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
from .mdp.rewards import ALBCRewardCfg, TrackingTermCfg

# 10 constraint terms: 5 Probabilistic + 5 Average.
# thruster_rate removed: structurally incompatible with entropy_coef>0 (noise alone violates 5x).
# thruster_sat reverted to thruster_util (Average, budget=0.40): original form.
_FULL_DOF_CONSTRAINT_TERMS: list[ConstraintTermCfg] = [
    # --- Probabilistic (5): binary indicator, budget = violation probability ---
    ConstraintTermCfg(func=attitude_limit_cost, params={"limit": 1.396}, budget=0.01, name="attitude"),
    ConstraintTermCfg(func=torque_limit_cost, params={"limit_nm": 9.5}, budget=0.08, name="arm_torque"),
    # 2.8 = inside the 3.1 rad/s PhysX cap (albc.py velocity_limit_sim): soft must
    # bite before hard, else PhysX clamps first and this cost can never fire (dead
    # constraint). Tunable within 2.5-2.8 per the wiki ripple card.
    ConstraintTermCfg(func=velocity_limit_cost, params={"limit_rad_per_s": 2.8}, budget=0.02, name="arm_joint_vel"),
    ConstraintTermCfg(func=joint1_position_cost, params={"limit_rad": 4 * math.pi}, budget=0.01, name="joint1_pos"),
    ConstraintTermCfg(func=cumulative_yaw_cost, params={"limit_rad": 8 * math.pi}, budget=0.01, name="cumul_yaw"),
    # --- Average (5): continuous cost, soft threshold for attitude/velocity tracking ---
    ConstraintTermCfg(func=thruster_utilization_cost, budget=0.40, name="thruster_util"),
    ConstraintTermCfg(func=rp_rate_cost, params={"soft_threshold": 0.5}, budget=0.10, name="rp_rate"),
    ConstraintTermCfg(func=yaw_rate_cost, params={"soft_threshold": 0.55}, budget=0.10, name="yaw_rate"),
    ConstraintTermCfg(
        func=rp_vel_settling_cost, params={"settling_threshold": 0.087}, budget=0.20, name="rp_vel_settling"
    ),
    ConstraintTermCfg(func=manipulability_cost, params={"w_threshold": 0.3}, budget=0.05, name="manipulability"),
]


# Original sim thruster order (as authored from the ALBC ROS control package
# config/TAM.yaml). Columns are sim thrusters T0-T5. Preserved verbatim for
# physical audit; the live allocation_matrix below is derived from this by
# reordering columns via _ESC_CHANNEL_ORDER.
_BASE_ALLOCATION_MATRIX: tuple[tuple[float, ...], ...] = (
    (0.707, -0.707, 0.707, -0.707, 0.0, 0.0),  # Fx surge
    (-0.707, -0.707, 0.707, 0.707, 0.0, 0.0),  # Fy sway
    (0.0, 0.0, 0.0, 0.0, 1.0, 1.0),  # Fz heave
    (0.007, 0.007, -0.007, -0.007, 0.0, 0.0),  # Mx roll
    (0.007, -0.007, 0.007, -0.007, 0.145, -0.145),  # My pitch
    (0.144, 0.144, 0.144, 0.144, 0.0, 0.0),  # Mz yaw
)

# ESC channel order: new column j = original sim column _ESC_CHANNEL_ORDER[j].
# Firmware (agent-jetson) wiring: m0,m3 = vertical (heave); m1,m2,m4,m5 = horizontal.
# Vertical pair (m0<-T4, m3<-T5) and "which channels are vertical" are CONFIRMED.
# Horizontal-4 individual mapping (m1<-T0, m2<-T1, m4<-T2, m5<-T3) is PROVISIONAL,
# pending B1 watertank measurement -- edit ONLY this tuple to update it.
_ESC_CHANNEL_ORDER: tuple[int, ...] = (4, 0, 1, 5, 2, 3)


def _reorder_columns(
    base: tuple[tuple[float, ...], ...], order: tuple[int, ...]
) -> tuple[tuple[float, ...], ...]:
    """Reorder each row's columns so new column j = base column order[j].

    Physics is invariant under this column permutation (singular values
    identical); it only relabels sim thrusters to firmware ESC channels.
    """
    return tuple(tuple(row[j] for j in order) for row in base)


@configclass
class ALBCThrusterCfg(ThrusterCfg):
    """ALBC 6-thruster configuration.

    TAM from the ALBC ROS control package (config/TAM.yaml) (verified against
    actuators.xacro). Columns are then reordered to the robot firmware ESC wiring
    via _ESC_CHANNEL_ORDER, so the live column order no longer matches the raw
    TAM.yaml/xacro sim order (original sim order preserved in
    _BASE_ALLOCATION_MATRIX). Thruster parameters use BlueROV T200 as baseline;
    DR covers real-robot differences.

    Layout (channels ordered to match robot firmware ESC wiring, m0..m5):
        m0, m3:         Vertical (heave)
        m1, m2, m4, m5: Horizontal (45-degree vectored) for surge, sway, yaw
    (original sim thruster order preserved in _BASE_ALLOCATION_MATRIX;
     reorder via _ESC_CHANNEL_ORDER)
    """

    num_thrusters: int = 6
    max_thrust: float = 50.0
    thrust_coefficient: float = 40.0
    time_constant_up: float = 0.1
    time_constant_down: float = 0.05
    allocation_matrix: tuple[tuple[float, ...], ...] = _reorder_columns(
        _BASE_ALLOCATION_MATRIX, _ESC_CHANNEL_ORDER
    )


@configclass
class DomainRandomizationCfg:
    """Aggressive DR for encoder training (formerly HardDomainRandomizationCfg).

    Merged 2026-07-07: the former base DomainRandomizationCfg (easy ranges, never
    instantiated on any training/student path) and HardDomainRandomizationCfg were
    collapsed into this single class. It now holds the Hard (training) values
    directly; training DR ranges are byte-identical to the prior Hard class.

    Expanded 2026-04-10: DORAEMON saturated all 15 parameters at Beta(1,1)=UNIFORM
    in run 2026-04-09_16-41-45. All bounds widened by ~30-50% beyond prior limits.
    Physics stability constraints: added_mass/inertia ratio < 1.0 (init validation),
    post-DR per-axis clamp (0.95*I) ensures stability.

    NOTE on added_mass_scale=(0.5, 1.5): the upper tail is heavily attenuated but
    NOT dead. After DR, added mass is clamped per axis to 0.95 * (DR-randomized)
    rigid-body inertia (mdp/events.py:260-271), and nominal added mass already sits
    near that ceiling on this small vehicle (yaw M_a/I=0.94). The clamp threshold
    scales with inertia_scale=(0.4, 2.0), so the effective ceiling is a random
    variable, not a constant. At the curriculum-saturated endpoint (Beta(1,1)=UNIFORM)
    ~35-50% of scale>1 draws are clamped on rotational axes (~76% on surge/sway) and
    the mean *realized* added_mass_scale is ~0.87; the high tail (scale~1.5) survives
    only when a large inertia_scale is co-sampled. Raising the upper bound alone has
    diminishing effect without also raising base rigid-body inertia (a vehicle-model
    change). The low tail (0.5-1.0) is fully exercised.
    """

    enable: bool = True

    # -- Hydrodynamic Parameter Scales --
    added_mass_scale: tuple[float, float] = (0.5, 1.5)
    linear_damping_scale: tuple[float, float] = (0.4, 1.7)
    quadratic_damping_scale: tuple[float, float] = (0.4, 1.7)
    volume_scale: tuple[float, float] = (0.75, 1.25)

    # -- Center of Buoyancy/Gravity Offset (meters) --
    cob_offset_x: tuple[float, float] = (-0.02, 0.02)
    cob_offset_y: tuple[float, float] = (-0.02, 0.02)
    cob_offset_z: tuple[float, float] = (-0.04, 0.04)
    cog_offset_x: tuple[float, float] = (-0.02, 0.02)
    cog_offset_y: tuple[float, float] = (-0.02, 0.02)
    cog_offset_z: tuple[float, float] = (-0.04, 0.04)

    # -- Inertia / Mass --
    inertia_scale: tuple[float, float] = (0.4, 2.0)
    body_mass_scale: tuple[float, float] = (0.75, 1.25)
    water_density_range: tuple[float, float] = (995.0, 1025.0)

    # -- Buoy Volume / Mass (decorrelated from the main-body scales above) --
    # The buoy is a separately-fabricated float with its own manufacturing
    # tolerance. Ranges genuinely mirror volume_scale/body_mass_scale (0.75, 1.25)
    # above so "buoy scale == main scale" reproduces the correlated baseline.
    buoy_volume_scale: tuple[float, float] = (0.75, 1.25)
    buoy_body_mass_scale: tuple[float, float] = (0.75, 1.25)

    # -- Joint Actuator --
    joint_stiffness_range: tuple[float, float] = (30.0, 150.0)
    joint_damping_range: tuple[float, float] = (0.3, 7.0)
    yaw_damping_scale: tuple[float, float] = (0.5, 1.5)
    joint_effort_limit_range: tuple[float, float] = (0.7, 1.0)
    joint_static_friction_range: tuple[float, float] = (0.0, 0.03)
    joint_viscous_friction_range: tuple[float, float] = (0.0, 0.2)

    # -- Payload --
    payload_mass_range: tuple[float, float] = (0.0, 3.0)
    # Reduced 2026-04-19 from 0.15 -> 0.08: outlier-env analysis of r9_tightrates
    # (eval_dr hard) showed 3 kg payload at 0.15 m offset generates ~4.5 Nm
    # gravitational torque, far exceeding roll TAM authority (4 x 50 N x 0.007 m
    # = 1.4 Nm). Combinations in that regime are physically uncontrollable and
    # dominated per-env SS_std (CV 2.18). 0.08 caps torque at ~2.4 Nm so roll
    # can still stabilize within authority while keeping pitch/yaw challenge.
    payload_cog_offset_xy_radius: float = 0.08
    # payload XY offset radius as a NORMALIZED area-quantile u in [0, 1], managed by
    # DORAEMON. events applies radius = payload_cog_offset_xy_radius * sqrt(u) so the disk
    # stays AREA-uniform (the sqrt is the area correction, applied in events, NOT here).
    # Curriculum nominal u=0 (no XY offset) widening to u=1 (full radius). The normalized
    # range is independent of the physical r_max (payload_cog_offset_xy_radius).
    payload_cog_offset_xy_u_range: tuple[float, float] = (0.0, 1.0)
    payload_cog_offset_z: tuple[float, float] = (-0.05, 0.0)
    buoy_moment_arm: float = 0.180

    # -- Thruster --
    thrust_coefficient_scale: tuple[float, float] = (0.7, 1.3)
    time_constant_scale: tuple[float, float] = (0.7, 1.3)

    # Control-action transport delay (discrete N-step lag on the applied
    # action) as integer control steps; 1 step = 20 ms @ 50 Hz.
    # (0, 0) = off (byte-identical to baseline). Experiment value = (0, 3).
    # simplified: static uniform DR (like time_constant_scale), not on the
    # DORAEMON curriculum -- integer delay is awkward for the Beta-continuous
    # sampler. Promote to a _PARAM_DEFS entry only if warranted.
    control_delay_steps: tuple[int, int] = (0, 0)

    # -- Ocean Current (DORAEMON-managed) --
    # Scalar strength [0, 1] multiplier on ocean_current.max_velocity.
    # DORAEMON nominal=0 (no current at curriculum start) -> expands as policy
    # masters easier variants.
    ocean_current_strength_range: tuple[float, float] = (0.0, 1.0)
    # Observation-noise curriculum scale as a NORMALIZED knob u in [0, 1], managed by
    # DORAEMON. _get_observations multiplies the 69D _OBS_NOISE_STD by this per-env scale
    # and adds it as an EXTRA white-noise layer on top of the always-on noise_model.
    # Nominal u=0 -> no extra noise (byte-identical to today); u=1 -> +1x _OBS_NOISE_STD
    # (total std sqrt(2)x today). std only; the per-episode bias stays the static model.
    # Same normalized range for base and Hard (it is not a physical magnitude).
    obs_noise_scale_range: tuple[float, float] = (0.0, 1.0)


# ==========================================================================
# 69D Observation Noise Model
#
# Current Proprioception (20D):
#   Command (3D): ang_cmd(3) [att_rp(2) + yaw_rate(1)]
#   Body State (6D): euler(3), ang_vel(3)
#   Arm State (5D): joint_pos(2), joint_vel(2), manipulability(1)
#   Thruster (6D): filtered output (ESC feedback)
#
# Temporal History (46D, stride=3):
#   Joint tracking x3 steps (12D): joint_pos_error(2), joint_vel(2)
#   Body tracking x3 steps (18D): ang_err(3) [att_rp(2)+yaw_rate(1)], rpy(3)
#   Action x2 steps (16D): full_action(8)
#
# Integral Error (3D): roll, pitch, yaw_rate
# ==========================================================================
_OBS_NOISE_STD = tuple(
    # --- Current Proprioception (20D) ---
    [0.0] * 3  # ang_cmd [att_rp(2) + yaw_rate(1)] (our command, no noise)
    + [0.02] * 3  # euler
    + [0.04] * 3  # ang_vel
    + [0.02] * 2  # joint_pos
    + [0.04] * 2  # joint_vel
    + [0.0]  # manipulability (computed)
    + [0.02] * 6  # thruster_state (ESC feedback)
    # --- Joint Tracking History (12D = 4D x 3 steps) ---
    + ([0.02] * 2 + [0.04] * 2) * 3  # joint_pos_error + joint_vel
    # --- Body Tracking History (18D = 6D x 3 steps) ---
    + ([0.04] * 3 + [0.02] * 3) * 3  # ang_err [att_rp+yaw_rate] + rpy (no lin_vel_err)
    # --- Action History (16D = 8D x 2 steps) ---
    + [0.0] * 16  # actions (our command, no noise)
    # --- Integral Error (3D) ---
    + [0.0] * 3  # integral observation (computed, no sensor noise)
)

# Bias magnitude (symmetric: MIN = -MAG, MAX = +MAG)
_OBS_BIAS_MAG = tuple(
    # --- Current Proprioception (20D) ---
    [0] * 3  # ang_cmd
    + [0.02] * 3  # euler
    + [0.03] * 3  # ang_vel
    + [0.02] * 2  # joint_pos
    + [0.03] * 2  # joint_vel
    + [0]  # manipulability
    + [0.01] * 6  # thruster
    # --- Joint Tracking History (12D) ---
    + ([0.02] * 2 + [0.03] * 2) * 3
    # --- Body Tracking History (18D) ---
    + ([0.04] * 3 + [0.02] * 3) * 3  # ang_err + rpy (no lin_vel_err)
    # --- Action History (16D) ---
    + [0] * 16
    # --- Integral Error (3D) ---
    + [0] * 3  # integral observation (computed, no bias)
)
_OBS_BIAS_MIN = tuple(-x for x in _OBS_BIAS_MAG)
_OBS_BIAS_MAX = _OBS_BIAS_MAG


# ==========================================================================
# Fault Injection (per-env actuator / sensor FAILURE -- FTC infrastructure)
#
# Distinct from DomainRandomizationCfg: DR spreads a PHYSICAL PARAMETER across
# envs (every env is a valid-but-different vehicle); a FAULT models a component
# FAILING (a thruster dies, a sensor degrades, a joint stiffens). Faults are
# sampled per-env at reset, fixed for the episode, and recorded into the eval
# npz (fault_<name>[N]) so heavy-tail analysis can join failing envs <-> faults.
#
# Default enable=False -> no fault buffers allocated -> byte-identical to the
# fault-free env. The minimal preset below exists to drive a fault_enable=True
# eval that proves fault_* keys land in the npz; it is intentionally mild
# (proves the pipeline, not a stress test).
# ==========================================================================
@configclass
class FaultInjectionCfg:
    """Per-env fault injection configuration (off by default)."""

    enable: bool = False

    # -- Thruster fault (per-env per-thruster health in [0, 1]) --
    # Each env: each thruster independently fails with prob `thruster_fail_prob`;
    # a failed thruster keeps a residual health sampled from `thruster_health_range`
    # (0 = fully dead, 0.5 = half degradation). Healthy thrusters stay at 1.0.
    thruster_fail_prob: float = 0.10
    thruster_health_range: tuple[float, float] = (0.0, 0.5)

    # -- Sensor noise fault (per-env extra observation noise scale) --
    # Per-env multiplier ADDED on top of the always-on _OBS_NOISE_STD model:
    # extra_noise = scale[env] * N(0, 1) * obs_noise_std. 0 = nominal sensor.
    sensor_noise_scale_range: tuple[float, float] = (0.0, 2.0)

    # -- Joint fault (per-env arm joint response health in [0, 1]) --
    # Scales the joint effort limit (1.0 = nominal, 0.5 = half torque authority).
    joint_health_range: tuple[float, float] = (0.5, 1.0)


@configclass
class ActuationNoiseCfg:
    """Per-step multiplicative actuation noise (the 3rd actuation channel).

    Independent of DomainRandomizationCfg (reset-time parameter spread) and
    FaultInjectionCfg (reset-time actuator failure): this perturbs the COMMAND
    every step -- applied = commanded * (1 + eps), eps ~ N(0, std), drawn per-env
    per-actuator. Not identifiable by estimation; only closed-loop feedback can
    reject it (the existing measured obs suffice -- no new obs field).

    Off by default. When enabled, the env bridges thruster_noise_std into the
    ThrusterCfg and passes enable_actuation_noise=True to ThrusterModel, and sets
    the joint delta noise std on the env. sigma defaults are arbitrary (thrust
    unmeasured) -- sweep targets.
    """

    enable: bool = False
    thruster_noise_std: float = 0.05
    joint_noise_std: float = 0.05


@configclass
class ALBCEnvCfg(DirectRLEnvCfg):
    """Attitude-only ALBC environment configuration.

    8D action (2D arm delta + 6D thruster), 69D observation (20D current + 46D history
    + 3D integral), 28D privileged (incl. measured lin_vel + control-action delay). Attitude-only: roll/pitch
    attitude + yaw rate, no linear velocity tracking. TRPO + IPO + Asymmetric Encoder
    with 10 constraints (5 prob + 5 avg).

    Roll/pitch: attitude command (+-30 deg, exp kernel reward).
    Yaw: rate command (+-0.5 rad/s, quadratic penalty).
    """

    # ==========================================================================
    # Environment Settings
    # ==========================================================================
    episode_length_s: float = 30.0
    decimation: int = 4
    action_space: int = 8  # 2D arm delta + 6D thruster
    observation_space: int = 69  # 20D current proprio + 46D history + 3D integral
    # Breakdown: cmd(3) + body(6) + arm(5) + thruster(6) = 20D current
    #            + joint_hist(12) + body_hist(18) + action_hist(16) = 46D history
    #            + integral(3) [roll, pitch, yaw_rate]
    state_space: int = 28  # Privileged info (see observations.py compute_privileged_obs)
    # Integral error observation (Hwangbo 2017 pattern, validated in R7/R8 experiments)
    use_integral_obs: bool = True
    integral_dims: int = 3  # [roll, pitch, yaw_rate]
    integral_leak: float = 0.99  # Leaky integrator decay: I_{t+1} = leak * I_t + err * dt
    integral_clamp: float = 2.0  # Windup prevention: clamp |I| <= this value
    integral_gated: bool = True  # Error-gated integration: only accumulate when |err| < reward sigma
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
    robot = ALBC_CFG.replace(prim_path="/World/envs/env_.*/Robot")
    hydrodynamics: HydrodynamicsCfg = ALBCHydrodynamicsCfg()
    buoy_hydrodynamics: HydrodynamicsCfg = ALBCBuoyHydrodynamicsCfg()
    ocean_current: OceanCurrentCfg = OceanCurrentCfg(
        max_velocity=(0.5, 0.5, 0.25, 0.0, 0.0, 0.0),
        noise_scale=(0.1, 0.1, 0.05, 0.0, 0.0, 0.0),
    )
    thrusters: ALBCThrusterCfg | None = ALBCThrusterCfg()

    # ==========================================================================
    # ALBC Joint Control
    # ==========================================================================
    albc_joint_names: list[str] = ALBC_JOINT_NAMES
    control_decimation: int = 1
    initial_joint_pos_range: tuple[float, float] = (-math.pi, math.pi)
    nominal_joint_pos: tuple[float, float] = (0.0, math.pi / 2.0)
    # Sustained |a|=1 demands delta_scale/step_dt = 5.0 rad/s > the 3.1 rad/s PhysX
    # velocity cap, so _joint_pos_targets can run ahead of the actual angle (target
    # runaway). Left as-is pending the delta-command sysid (wiki: velocity_limit ripple).
    delta_scale: float = 0.10

    # ==========================================================================
    # Temporal History (ring buffer, recorded every ``hist_stride`` control steps)
    # ==========================================================================
    hist_len: int = 3
    """Number of past timesteps stored in the history ring buffer."""
    hist_stride: int = 3
    """Record every N-th control step. Effective span = hist_len * hist_stride * step_dt."""
    hist_feature_dim: int = 18
    """Features per timestep: joint_tracking(4) + body_tracking(6) + action(8)."""
    hist_action_len: int = 2
    """Number of action history steps to include in observation (newest N of hist_len)."""

    # ==========================================================================
    # Task: Command Tracking (attitude only -- roll/pitch + yaw rate; no linear velocity)
    # ==========================================================================
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

    reward: ALBCRewardCfg = ALBCRewardCfg(
        yaw_vel=TrackingTermCfg(k=3.5, sigma=0.10, quad_ratio=1.0, tanh_coef=0.3, tanh_eps=0.10),
        # r13: restored k_bias=-2.0 (r11_emabias strength). r12_baseline halving to
        # -1.0 combined with latent=16 produced rank #7 (hard roll 1.26 vs r11_emabias
        # 0.62, rank #1). Full strength emabias was verified strongest single
        # intervention across 24 runs. r13_A keeps latent=9 (r11_emabias config);
        # r13_B tests latent=16 + full strength (never tried).
        k_bias=-2.0,
    )

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
    randomization: DomainRandomizationCfg = DomainRandomizationCfg()

    # ==========================================================================
    # Fault Injection (off by default; FTC infrastructure, see FaultInjectionCfg)
    # ==========================================================================
    fault: FaultInjectionCfg = FaultInjectionCfg()

    # Per-step multiplicative actuation noise (3rd channel; off by default). Sibling
    # of fault/randomization -- independently toggleable, never entangled with them.
    actuation_noise: ActuationNoiseCfg = ActuationNoiseCfg()
    # performance_lb: DORAEMON binary-success threshold on accumulated episode return
    # (albc_env.py: _episode_return_accum += reward; success = return >= performance_lb).
    # Calibrated 68.0 -> 250.0 from a recon run (trpo_baseline_260608_160453, lb=68, 1146 iter):
    # the DORAEMON buffer's actual episode-return distribution (n=2000) was
    # min=81.9 / p5=227 / p25=250 / median=264 / p95=291. lb=68 sat BELOW the minimum return,
    # so success=return>=68 was always 1 -> the feasibility constraint (Ghat>=alpha) was inert
    # and the curriculum widened the DR distribution unconstrained (no self-pacing feedback).
    # lb=250 (p25) puts the starting success_rate at ~0.65: above alpha=0.5 so the distribution
    # still expands, but the signal is live again instead of pinned at 1. Chosen below the
    # median so a reward plateau cannot drag success_rate to 0 (which would shrink the DR range).
    # kl_ub 0.06 -> 0.12: doubles the per-step trust region so the distribution widens fast
    # enough to compensate for the slower expansion that the raised lb induces. Both levers move
    # together by design -- lb alone makes DR easier, kl_ub alone leaves success_rate pinned at 1.
    doraemon: DoraemonCfg = DoraemonCfg(enable=True, kl_ub=0.12, performance_lb=250.0, step_interval=250)

    # ==========================================================================
    # Payload
    # ==========================================================================
    payload_mass: float = 0.5
    payload_attachment_offset: tuple[float, float, float] = (0.0, 0.0, -0.05)

    # ==========================================================================
    # Payload Visualization (play/debug only; ignored during training)
    # ==========================================================================
    enable_payload_viz: bool = False
    """Render a translucent red sphere at payload CoG and a grey cylinder bar from
    attachment to CoG. Gated so training runs are unaffected."""
    payload_viz_min_mass: float = 0.05
    """Hide markers when |payload_mass| < this value (kg)."""
    payload_viz_sphere_r_min: float = 0.02
    """Sphere radius (m) at payload_mass = payload_viz_min_mass."""
    payload_viz_sphere_r_max: float = 0.06
    """Sphere radius (m) at payload_mass = payload_viz_mass_ref."""
    payload_viz_mass_ref: float = 3.0
    """Reference mass (kg) mapped to sphere_r_max (HardDR upper bound)."""
    payload_viz_bar_radius: float = 0.005
    """Cylinder radius (m) for attachment->CoG bar."""
    payload_viz_min_bar_len: float = 0.001
    """Hide bar when |cog_offset| < this value (m)."""

    # ==========================================================================
    # Observation Noise (69D)
    # ==========================================================================
    observation_noise_model: NoiseModelWithAdditiveBiasCfg = NoiseModelWithAdditiveBiasCfg(
        noise_cfg=GaussianNoiseCfg(mean=0.0, std=_OBS_NOISE_STD),
        bias_noise_cfg=UniformNoiseCfg(n_min=_OBS_BIAS_MIN, n_max=_OBS_BIAS_MAX),
    )

    # ==========================================================================
    # Constraints (10 terms: 5 probabilistic + 5 average)
    # ==========================================================================
    constraints: ALBCConstraintCfg = ALBCConstraintCfg(terms=_FULL_DOF_CONSTRAINT_TERMS)

    # --- joint1-constraint-redesign experiment (off by default = byte-identical) ---
    # Toggles the continuous joint1 anti-drift constraint. The reward-side centering
    # penalty and the wrapped-instantaneous constraint (arm A) were both removed
    # 2026-07, so this is now the only joint1 anti-drift mechanism. 'none' = no extra
    # term (shipped behavior). 'B' = average cost on the integrated-command
    # displacement (joint1_cumulative, drift-correct).
    #
    # NOTE: the extra term is materialized by apply_joint1_constraint_arm() called from
    # ALBCEnv.__init__, NOT from a cfg __post_init__. A constraint term bundles a function
    # ref + budget, so it cannot be added by a hydra scalar; and __post_init__ runs at cfg
    # construction BEFORE hydra applies the override (update_class_from_dict), so toggling
    # there would always see arm='none' and silently produce a baseline-dup. The env reads
    # cfg AFTER hydra, so that is the correct materialization point.
    joint1_constraint_arm: str = "none"  # one of {"none", "B"}
    joint1_constraint_budget: float = 0.05  # per-step average budget d_k for the joint1 term
