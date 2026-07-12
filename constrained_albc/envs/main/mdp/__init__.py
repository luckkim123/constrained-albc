# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""MDP functions for Full 6-DOF ALBC environment."""

from . import faults
from .constraints import (
    ALBCConstraintCfg,
    ConstraintTermCfg,
    attitude_limit_cost,
    compute_all_costs,
    cumulative_yaw_cost,
    joint1_position_cost,
    manipulability_cost,
    thruster_utilization_cost,
    torque_limit_cost,
    velocity_limit_cost,
    yaw_rate_cost,
)
from .events import (
    DRSampler,
    apply_joint_fault,
    randomize_body_mass,
    randomize_hydrodynamics,
    randomize_joint_effort_limit,
    randomize_joint_friction,
    randomize_joint_gains,
    randomize_joint_positions,
    randomize_ocean_current,
    randomize_payload,
    reset_joint_positions_default,
    reset_robot_pose_default,
)
from .observations import (
    compute_policy_obs,
    compute_privileged_obs,
)
from .rewards import (
    ALBCRewardCfg,
    RewardManager,
    RewardTermCfg,
    action_smoothness,
    att_rp_tracking,
    joint_torque,
    thruster_energy,
    yaw_vel_tracking,
)
