# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Observation functions for velocity + attitude tracking environment.

    o_t (87D): Unified policy observation = current proprioception (26D) + temporal history (55D) + integral (6D)
    p_t (24D): Privileged information (simulator-only DR parameters)

The encoder receives p_t to compress physical unknowns into latent z.
The actor receives o_t + z. The critic receives o_t + z + p_t (asymmetric).

Current proprioception (26D) -- measurable on real robot:
    Command (6D):       vel_cmd_lin(3), ang_cmd(3) [att_rp(2) + yaw_rate(1)]
    Body State (9D):    euler(3), ang_vel(3), lin_vel(3)
    Arm State (5D):     joint_pos(2), joint_vel(2), manipulability(1)
    Thruster (6D):      filtered output (ESC channels m0-m5)

Temporal history (55D) -- ring buffer, stride=3:
    Joint tracking (12D):   (q_des_prev - q_actual, joint_vel) x 3 steps
    Body tracking (27D):    (lin_vel_err, ang_err [att_rp+yaw_rate], rpy) x 3 steps
    Action (16D):           full_action(8D) x 2 steps
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
    """Compute current proprioception (26D).

    Measurable on real robot (IMU, DVL, motor encoders, ESC feedback):

    Command (6D):
        [0:3]   linear velocity command (body frame, no noise)
        [3:5]   roll/pitch attitude command (radians, no noise)
        [5]     yaw rate command (rad/s, body frame, no noise)

    Body State (9D):
        [6:9]   euler angles (roll, pitch, yaw)
        [9:12]  angular velocity in body frame (p, q, r)
        [12:15] linear velocity in body frame (u, v, w)

    Arm State (5D):
        [15:17] joint positions (raw cumulative angle)
        [17:19] joint velocities
        [19]    manipulability index w (normalized [0, 1])

    Thruster State (6D):
        [20:26] thruster filtered output (ESC channels m0-m5)
    """
    roll, pitch, yaw = env._euler_cache
    joint_pos = robot.data.joint_pos[:, env._albc_joint_ids]
    joint_vel = robot.data.joint_vel[:, env._albc_joint_ids]
    thr_state = env._thruster.state if env._thruster is not None else torch.zeros(env.num_envs, 6, device=env.device)

    return torch.cat(
        [
            # Command (6D)
            env._vel_cmd_lin,  # 3D: linear velocity command
            env._ang_cmd,  # 3D: [roll_att_cmd, pitch_att_cmd, yaw_rate_cmd]
            # Body State (9D)
            torch.stack([roll, pitch, yaw], dim=-1),  # 3D: euler angles
            robot.data.root_ang_vel_b,  # 3D: angular velocity body
            robot.data.root_lin_vel_b,  # 3D: linear velocity body
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
    """Compute privileged information p_t (24D).

    Non-redundant set of independent DR parameters. Each dimension corresponds
    to a single random variable -- no correlated pairs from shared DR scales.

        Hydrodynamics (7D):
            [0]     main body volume
            [1:4]   main body CoG (x, y, z)
            [4:7]   main body CoB (x, y, z)
        Dynamic Response (5D):
            [7]     main body Ixx (representative inertia)
            [8]     linear damping roll (representative)
            [9]     quadratic damping roll (representative)
            [10]    body mass
            [11]    added mass surge
        Payload (4D):
            [12]    payload mass
            [13:16] payload CoG offset (x, y, z)
        Actuator (4D):
            [16]    joint stiffness Kp
            [17]    joint damping Kd
            [18]    thrust coefficient
            [19]    time constant up
        Environment (4D):
            [20]    water density
            [21:24] ocean current velocity (x, y, z, world frame)
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
            # Dynamic Response (5D)
            env._hydro.rigid_body_inertia[:, 0:1],  # Ixx only
            env._hydro.linear_damping[:, 3:4],  # roll only
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
        ],
        dim=-1,
    )
