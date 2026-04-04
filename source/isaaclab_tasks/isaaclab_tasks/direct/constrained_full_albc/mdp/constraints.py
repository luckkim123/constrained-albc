# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Constraint cost functions for IPO (Interior-Point Optimization).

Two types following the paper's framework:
    Probabilistic: C_k = I(violation) in {0, 1}, budget = max violation probability
    Average:       C_k = f(s,a,s') in R+, budget = max average value

All constraints satisfy: J_Ck(pi) = E[sum gamma^t C_k] <= d_k

Constraint layout (5 Probabilistic + 5 Average = 10 total):
    [0]  attitude        (prob)  I(max(|roll|,|pitch|) > limit)
    [1]  arm_torque      (prob)  I(any |tau_j| > limit)
    [2]  arm_joint_vel   (prob)  I(any |q_dot_j| > limit)
    [3]  joint1_pos      (prob)  I(|theta1| > limit)
    [4]  cumul_yaw       (prob)  I(|yaw_accumulated| > limit)
    [5]  thruster_util   (avg)   max(|state_i|) over thrusters
    [6]  rp_rate         (avg)   max(0, max(|p|,|q|) - threshold)
    [7]  yaw_rate        (avg)   max(0, |w_z| - threshold)
    [8]  rp_vel_settling (avg)   (|p| + |q|) / 2
    [9]  manipulability  (avg)   max(0, threshold - w)
"""

from __future__ import annotations

import math
from collections.abc import Callable
from typing import TYPE_CHECKING

import torch

from isaaclab.utils import configclass
from isaaclab.utils.math import euler_xyz_from_quat

if TYPE_CHECKING:
    from isaaclab.assets import Articulation

    from ..albc_env import ALBCEnv


# --- Configuration ---


@configclass
class ConstraintTermCfg:
    """Single constraint: cost function + per-step budget D_k."""

    func: Callable = lambda _r, _e: torch.zeros(1)
    params: dict = {}
    budget: float = 0.1
    name: str = ""


@configclass
class ALBCConstraintCfg:
    """List of constraint terms for IPO barrier."""

    terms: list[ConstraintTermCfg] = []
    cost_gamma: float = 0.99
    cost_lam: float = 0.95

    @property
    def num_constraints(self) -> int:
        return len(self.terms)

    @property
    def constraint_budgets(self) -> tuple[float, ...]:
        return tuple(t.budget for t in self.terms)

    @property
    def constraint_names(self) -> tuple[str, ...]:
        return tuple(t.name or t.func.__name__ for t in self.terms)


# =============================================================================
# Probabilistic Constraints (binary indicator, budget = violation probability)
# =============================================================================


def attitude_limit_cost(
    _robot: Articulation,
    _env: ALBCEnv,
    limit: float = 1.396,
) -> torch.Tensor:
    """I(max(|roll|, |pitch|) > limit). Tilt safety bound."""
    roll, pitch, _ = euler_xyz_from_quat(_robot.data.root_quat_w)
    return (torch.max(roll.abs(), pitch.abs()) > limit).float()


def torque_limit_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_nm: float = 9.5,
) -> torch.Tensor:
    """I(any |tau_j| > tau_max). Arm joint torque limit.

    Uses applied_torque (post-actuator-clamp) rather than computed_torque (pre-clamp)
    because computed_torque from the PD controller is unbounded (Kp*error can be 500+ Nm)
    while the physical motor output is limited by the actuator effort_limit.
    """
    applied = _robot.data.applied_torque[:, env._albc_joint_ids]
    return (applied.abs() > limit_nm).any(dim=-1).float()


def velocity_limit_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_rad_per_s: float = 4.189,
) -> torch.Tensor:
    """I(any |q_dot_j| > q_dot_max). Arm joint velocity limit."""
    joint_vel = _robot.data.joint_vel[:, env._albc_joint_ids]
    return (joint_vel.abs().max(dim=-1).values > limit_rad_per_s).float()


def joint1_position_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_rad: float = 4 * math.pi,
) -> torch.Tensor:
    """I(|theta1| > limit). Prevents cable wrapping on joint1.

    Joint1 is continuous (no PhysX position limit). This constraint provides
    a soft boundary to prevent the arm base motor cable from wrapping.
    Joint2 is unaffected (no cable routing concern).
    """
    theta1 = _robot.data.joint_pos[:, env._albc_joint_ids[0]]
    return (theta1.abs() > limit_rad).float()


def cumulative_yaw_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_rad: float = 8 * math.pi,
) -> torch.Tensor:
    """I(|yaw_accumulated| > limit). Prevents tether wrapping around robot body.

    Tracks cumulative yaw rotation (not instantaneous). The env maintains
    a running sum of yaw changes with wrapping correction.
    """
    return (env._cumulative_yaw.abs() > limit_rad).float()


# =============================================================================
# Average Constraints (continuous, ReLU-style threshold for velocity tracking)
# =============================================================================


def rp_rate_cost(
    _robot: Articulation,
    _env: ALBCEnv,
    soft_threshold: float = 1.0,
) -> torch.Tensor:
    """max(0, max(|p|,|q|) - threshold). Roll/pitch angular velocity limit.

    Type: Average
    Formula: max(0, max(|p|, |q|) - threshold)
    Budget: 0.10

    With attitude commands for roll/pitch, angular velocity is a byproduct of
    tracking, not the command itself. Threshold=1.0 rad/s (57 deg/s) is generous
    for smooth attitude transitions (+-45 deg command range, 5s resample interval
    needs only ~0.3 rad/s average). Yaw rate has its own dedicated constraint.
    """
    rp_omega = _robot.data.root_ang_vel_b[:, :2].abs().max(dim=-1).values
    return (rp_omega - soft_threshold).clamp(min=0.0)


def yaw_rate_cost(
    _robot: Articulation,
    _env: ALBCEnv,
    soft_threshold: float = 1.0,
) -> torch.Tensor:
    """max(0, |w_z| - threshold). Penalizes excessive yaw rate only.

    ReLU-style: zero cost below threshold, linear penalty above.
    Threshold > yaw_rate_cmd_range (0.5) so normal yaw tracking is unaffected.
    Replaces the old yaw_velocity_cost which conflicted with yaw commands.
    """
    return (_robot.data.root_ang_vel_b[:, 2].abs() - soft_threshold).clamp(min=0.0)


def body_linear_velocity_cost(
    _robot: Articulation,
    _env: ALBCEnv,
    soft_threshold: float = 1.0,
) -> torch.Tensor:
    """max(0, ||v_body|| - threshold). Penalizes excessive translation speed.

    Protects tether from becoming taut due to rapid robot movement.
    Threshold > vel_cmd_lin_range (0.5) so normal tracking is unaffected.
    Softer than termination threshold (2.0 m/s).
    """
    return (_robot.data.root_lin_vel_b.norm(dim=-1) - soft_threshold).clamp(min=0.0)


def thruster_utilization_cost(
    _robot: Articulation,
    env: ALBCEnv,
) -> torch.Tensor:
    """max(|state_i|) over all thrusters. Peak thruster utilization.

    Type: Average
    Budget: 0.40

    Keeps peak thruster utilization below budget to preserve control authority
    reserve and battery life. Reward (k_thr) handles mean energy; this constraint
    limits the worst-case single-thruster output.
    """
    if env._thruster is None:
        return torch.zeros(_robot.data.root_pos_w.shape[0], device=_robot.device)
    return env._thruster.state.abs().max(dim=-1).values


def thruster_rate_cost(
    _robot: Articulation,
    env: ALBCEnv,
    soft_threshold: float = 0.5,
) -> torch.Tensor:
    """max(0, max(|dT_i|) - threshold). Penalizes rapid thruster command changes.

    Type: Average
    Budget: 0.10

    Protects thruster motors from rapid command changes that cause
    mechanical wear and electrical stress. Threshold=0.5 means a 50% range
    change per control step (50Hz) is tolerated; anything faster is penalized.
    Complements action_smoothness reward (which covers all 8D equally).
    """
    da_thr = env._actions[:, 2:] - env._prev_actions[:, 2:]
    return (da_thr.abs().max(dim=-1).values - soft_threshold).clamp(min=0.0)


def rp_vel_settling_cost(
    _robot: Articulation,
    _env: ALBCEnv,
) -> torch.Tensor:
    """(|p| + |q|) / 2. Average roll/pitch angular velocity settling.

    Type: Average
    Budget: 0.05

    Roll/pitch are attitude (position) targets, not velocity targets.
    This constraint forces angular velocity to average near zero,
    encouraging fast settling after reaching the target attitude.
    Complements rp_rate_cost which only penalizes >1.0 rad/s.
    """
    return _robot.data.root_ang_vel_b[:, :2].abs().mean(dim=-1)


def manipulability_cost(
    _robot: Articulation,
    env: ALBCEnv,
    w_threshold: float = 0.3,
) -> torch.Tensor:
    """max(0, threshold - w). Penalizes proximity to arm singularity.

    w is the Yoshikawa manipulability index normalized to [0, 1].
    At w=0 (singularity): cost = threshold. At w >= threshold: cost = 0.
    Protects against sustained arm extension under load (structural damage risk).
    """
    return (w_threshold - env._manipulability).clamp(min=0.0)


# =============================================================================
# Dispatch
# =============================================================================


def compute_all_costs(
    robot: Articulation,
    env: ALBCEnv,
    cfg: ALBCConstraintCfg,
) -> torch.Tensor:
    """Compute all K costs -> (num_envs, K) tensor."""
    return torch.stack([t.func(robot, env, **t.params) for t in cfg.terms], dim=-1)
