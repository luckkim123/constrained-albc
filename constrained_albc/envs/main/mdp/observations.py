# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observation functions for the attitude-only tracking environment (no linear velocity).

    o_t (69D): Unified policy observation = current proprioception (20D) + temporal history (46D) + integral (3D)
    p_t (28D): Privileged info (simulator-only DR params) + measured root_lin_vel_b (3D, critic-only) + control-action delay (1D, critic-only)

The encoder receives p_t to compress physical unknowns into latent z.
The actor receives o_t + z. The critic receives o_t + z + p_t (asymmetric).
Linear velocity is excluded from o_t (no DVL on the real robot); it appears only in p_t.

Current proprioception (20D) -- measurable on real robot:
    Command (3D):       ang_cmd(3) [att_rp(2) + yaw_rate(1)]   -- no lin_vel command
    Body State (6D):    euler(3), ang_vel(3)                   -- no measured lin_vel
    Arm State (5D):     joint_pos(2), joint_vel(2), manipulability(1)
    Thruster (6D):      filtered output (ESC channels m0-m5)

Temporal history (46D) -- ring buffer, stride=3:
    Joint tracking (12D):   (q_des_prev - q_actual, joint_vel) x 3 steps
    Body tracking (18D):    (ang_err [att_rp(2)+yaw_rate(1)], rpy(3)) x 3 steps   -- no lin_vel_err
    Action (16D):           full_action(8D) x 2 steps

Integral error (3D): leaky-integrated [roll, pitch, yaw_rate] (mirrors the 3 tracking channels).
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

if TYPE_CHECKING:
    from isaaclab.assets import Articulation

    from ..albc_env import ALBCEnv


def compute_policy_obs(
    env: ALBCEnv,
    robot: Articulation,
) -> torch.Tensor:
    """Compute current proprioception (20D).

    Measurable on real robot (IMU, motor encoders, ESC feedback).
    Linear velocity is excluded -- no DVL on real robot.

    Command (3D):
        [0:3]   ang_cmd [roll_att, pitch_att, yaw_rate]

    Body State (6D):
        [3:6]   euler angles (roll, pitch, yaw)
        [6:9]   angular velocity in body frame (p, q, r)

    Arm State (5D):
        [9:11]  joint positions (raw cumulative angle)
        [11:13] joint velocities
        [13]    manipulability index w (normalized [0, 1])

    Thruster State (6D):
        [14:20] thruster filtered output (ESC channels m0-m5)
    """
    roll, pitch, yaw = env._euler_cache
    joint_pos = robot.data.joint_pos[:, env._albc_joint_ids]
    joint_vel = robot.data.joint_vel[:, env._albc_joint_ids]
    thr_state = env._thruster.state if env._thruster is not None else torch.zeros(env.num_envs, 6, device=env.device)

    return torch.cat(
        [
            # Command (3D) -- attitude only (no linear velocity command)
            env._ang_cmd,  # 3D: [roll_att_cmd, pitch_att_cmd, yaw_rate_cmd]
            # Body State (6D) -- no measured linear velocity (no DVL on real robot)
            torch.stack([roll, pitch, yaw], dim=-1),  # 3D: euler angles
            robot.data.root_ang_vel_b,  # 3D: angular velocity body
            # Arm State (5D)
            joint_pos,  # 2D: joint positions (raw cumulative)
            joint_vel,  # 2D: joint velocities
            env._manipulability.unsqueeze(-1),  # 1D: Yoshikawa manipulability
            # Thruster State (6D)
            thr_state,  # 6D: filtered thruster output
        ],
        dim=-1,
    )


def compute_privileged_obs(
    env: ALBCEnv,
) -> torch.Tensor:
    """Compute privileged information p_t (28D, union layout 2026-07-12 + latency).

    Non-redundant set of independent DR parameters. Each dimension corresponds
    to a single random variable -- no correlated pairs from shared DR scales.

    Union layout: Ixx and linear damping roll were REMOVED (priv-obs-slim
    Stage-1 validated removals); quadratic damping and measured lin_vel are
    RETAINED (slim marked them PENDING Stage-2 -- decide via a later A/B); the
    2 buoy scalars were ADDED (DR-backed, decorrelated from the main body),
    and the control-action delay (latency DR) was ADDED as the 28th dim.

    Invariant: all DR-backed dims come FIRST; measured lin_vel is ALWAYS the
    final 3. The buoy scalars (22,23) and the latency dim (24) are DR-backed,
    so they sit at the end of the DR-backed block (after the ocean block),
    before measured lin_vel (25:28).

        Hydrodynamics (7D):
            [0]     main body volume
            [1:4]   main body CoG (x, y, z)
            [4:7]   main body CoB (x, y, z)
        Dynamic Response (3D):
            [7]     quadratic damping roll (representative)
            [8]     body mass
            [9]     added mass surge
        Payload (4D):
            [10]    payload mass
            [11:14] payload CoG offset (x, y, z)
        Actuator (4D):
            [14]    joint stiffness Kp
            [15]    joint damping Kd
            [16]    thrust coefficient
            [17]    time constant up
        Environment (4D):
            [18]    water density
            [19:22] ocean current velocity (x, y, z, world frame)
        Buoy (2D) -- DR-backed, decorrelated from main body:
            [22]    buoy volume
            [23]    buoy body mass
        Latency (1D) -- DR-backed, normalized:
            [24]    control-action delay (normalized steps, 0 when off)
        Measured Velocity (3D):
            [25:28] body linear velocity (u, v, w)
    """
    jid = env._albc_joint_ids[0]

    # Thruster params: per-env tensors when DR enabled, config scalars as fallback
    thr = env._thruster
    if thr is not None and thr._thrust_coeff is not None and thr._time_constant_up is not None:
        thrust_coeff = thr._thrust_coeff
        time_const = thr._time_constant_up
    elif thr is not None:
        thrust_coeff = torch.full((env.num_envs,), thr.cfg.thrust_coefficient, device=env.device)
        time_const = torch.full((env.num_envs,), thr.cfg.time_constant_up, device=env.device)
    else:
        thrust_coeff = torch.zeros(env.num_envs, device=env.device)
        time_const = torch.zeros(env.num_envs, device=env.device)

    return torch.cat(
        [
            # Hydrodynamics (7D)
            env._hydro.volume.unsqueeze(-1),
            env._hydro.center_of_gravity,  # 3D: x, y, z
            env._hydro.center_of_buoyancy,  # 3D: x, y, z
            # Dynamic Response (3D) -- Ixx and lin_damp dropped (slim Stage-1 validated)
            env._hydro.quadratic_damping[:, 3:4],  # roll only
            env._hydro.body_mass.unsqueeze(-1),
            env._hydro.added_mass_matrix[:, 0, 0].unsqueeze(-1),  # surge
            # Payload (4D)
            env._payload_mass.unsqueeze(-1),
            env._payload_cog_offset,  # 3D: x, y, z
            # Actuator (4D)
            env._robot.data.joint_stiffness[:, jid : jid + 1],
            env._robot.data.joint_damping[:, jid : jid + 1],
            thrust_coeff.unsqueeze(-1),
            time_const.unsqueeze(-1),
            # Environment (4D)
            env._hydro.water_density.unsqueeze(-1),
            env._hydro.current.velocity_w[:, :3],  # ocean current linear xyz (world frame)
            # Buoy (2D) -- DR-backed, decorrelated from the main-body scales.
            # At the END of the DR-backed block (before measured lin_vel) so the
            # "DR dims first, measured last" p_t invariant holds.
            env._buoy_hydro.volume.unsqueeze(-1),  # 22: buoy volume
            env._buoy_hydro.body_mass.unsqueeze(-1),  # 23: buoy body mass
            # Latency (1D) -- normalized per-env control-action delay (0 when off);
            # DR-backed, so it stays in the DR-backed block before measured lin_vel
            (
                env._control_delay_steps.float()
                / max(env.cfg.randomization.control_delay_steps[1], 1)
            ).unsqueeze(-1),  # 24: control-action delay
            # Measured velocity (3D) -- privileged: actor is blinded, critic sees it
            env._robot.data.root_lin_vel_b,  # 3D: body linear velocity (u, v, w)
        ],
        dim=-1,
    )
