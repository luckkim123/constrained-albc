# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Constraint cost functions for IPO (Interior-Point Optimization).

Two types following the paper's framework:
    Probabilistic: C_k = I(violation) in {0, 1}, budget = max violation probability
    Average:       C_k = f(s,a,s') in R+, budget = max average value

All constraints satisfy: J_Ck(pi) = E[sum gamma^t C_k] <= d_k

Constraint layout (5 Probabilistic + 5 Average = 10 total in the shipped config):
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

Experiment-only Average costs (joint1-constraint-redesign; NOT in the shipped
config -- wired in per-arm by the experiment, reward centering off):
    joint1_centering   (avg)   wrap(theta1)^2            (arm A, instantaneous angle)
    joint1_cumulative  (avg)   |q_des_1 - nominal|       (arm B, integrated command)
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

import torch

from isaaclab.utils import configclass

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
    limit: float,
) -> torch.Tensor:
    """I(max(|roll|, |pitch|) > limit). Tilt safety bound."""
    roll, pitch, _ = _env._euler_cache
    return (torch.max(roll.abs(), pitch.abs()) > limit).float()


def torque_limit_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_nm: float,
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
    limit_rad_per_s: float,
) -> torch.Tensor:
    """I(any |q_dot_j| > q_dot_max). Arm joint velocity limit."""
    joint_vel = _robot.data.joint_vel[:, env._albc_joint_ids]
    return (joint_vel.abs().max(dim=-1).values > limit_rad_per_s).float()


def joint1_position_cost(
    _robot: Articulation,
    env: ALBCEnv,
    limit_rad: float,
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
    limit_rad: float,
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
    soft_threshold: float,
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
    soft_threshold: float,
) -> torch.Tensor:
    """max(0, |w_z| - threshold). Penalizes excessive yaw rate only.

    ReLU-style: zero cost below threshold, linear penalty above.
    Threshold > yaw_rate_cmd_range (0.5) so normal yaw tracking is unaffected.
    Replaces the old yaw_velocity_cost which conflicted with yaw commands.
    """
    return (_robot.data.root_ang_vel_b[:, 2].abs() - soft_threshold).clamp(min=0.0)


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


def rp_vel_settling_cost(
    _robot: Articulation,
    _env: ALBCEnv,
    settling_threshold: float,
) -> torch.Tensor:
    """Settling-aware (|p| + |q|) / 2. Active only when near target attitude.

    Type: Average
    Budget: 0.20

    Gated by attitude error: cost is zero during transit (|att_err| > threshold)
    and active during settling (|att_err| <= threshold). This prevents the
    constraint from opposing attitude tracking during the transit phase,
    where angular velocity is needed to reach the target.

    Args:
        settling_threshold: attitude error below which settling is enforced (rad).
            Default 0.087 rad = 5.0 deg.
    """
    rp_vel = _robot.data.root_ang_vel_b[:, :2].abs().mean(dim=-1)
    att_err_norm = _env._att_rp_err.abs().max(dim=-1).values
    settling_mask = (att_err_norm <= settling_threshold).float()
    return rp_vel * settling_mask


def manipulability_cost(
    _robot: Articulation,
    env: ALBCEnv,
    w_threshold: float,
) -> torch.Tensor:
    """max(0, threshold - w). Penalizes proximity to arm singularity.

    w is the Yoshikawa manipulability index normalized to [0, 1].
    At w=0 (singularity): cost = threshold. At w >= threshold: cost = 0.
    Protects against sustained arm extension under load (structural damage risk).
    """
    return (w_threshold - env._manipulability).clamp(min=0.0)


def joint1_centering_cost(
    _robot: Articulation,
    env: ALBCEnv,
) -> torch.Tensor:
    """wrap(theta1)^2 on the MEASURED instantaneous joint1 angle (experiment arm A).

    Type: Average
    Formula: wrap(theta1)^2, wrap = atan2(sin, cos) folded to (-pi, pi]

    Continuous restoring cost toward nominal (0 rad). The reward-side centering
    penalty was removed 2026-07, so the constraint side (arm A here, or arm B via
    joint1_cumulative_cost) is now the sole joint1 anti-drift mechanism -- it
    supplies the shaping gradient the binary joint1_pos indicator (flat inside
    +-4pi) does not.
    Reads MEASURED joint_pos (in steady tracking ~= the integrated command).

    Caveat (the reason arm B exists): the wrap fold makes theta1 = 2*pi cost ZERO
    (a continuous motor: one full turn is the same pose), so this form is blind to
    a full revolution of drift and can convert drift to a static offset rather than
    eliminate it. joint1_cumulative_cost (arm B) targets the accumulation directly.
    """
    theta1 = _robot.data.joint_pos[:, env._albc_joint_ids[0]]
    wrapped = torch.atan2(torch.sin(theta1), torch.cos(theta1))
    return wrapped.pow(2)


def joint1_cumulative_cost(
    _robot: Articulation,
    env: ALBCEnv,
) -> torch.Tensor:
    """|integrated joint1 command - nominal| (experiment arm B).

    Type: Average
    Formula: |_joint_pos_targets[:, 0] - nominal_joint1|

    The drift-correct form: it reads the COMMANDED integrator (_joint_pos_targets,
    where q_des += delta_scale * a accumulates -- the exact variable drift lives in,
    albc_env._apply_joint_pd_action) rather than the measured angle that arms A / the
    reward read. _joint_pos_targets is already an UNWRAPPED running sum (never folded
    to (-pi, pi]), so a full revolution of drift is a real accumulated displacement,
    not folded to zero -- which is precisely what the wrapped instantaneous form
    (arm A) cannot see. Displacement from nominal in either direction counts (drift
    is one-directional, but either sign). No extra env accumulator is needed: the
    integrator already holds the unwrapped sum, and it is reset to the measured pose
    on episode reset (albc_env._reset_action_buffers).
    """
    # joint1 is LOCAL index 0 in both _nominal_joint_pos (built from cfg.nominal_joint_pos
    # = (joint1, joint2)) and _joint_pos_targets[:, 0]. Use the local index, NOT the global
    # DOF id _albc_joint_ids[0], so this stays correct if the articulation DOF layout changes.
    nominal = env._nominal_joint_pos[0]
    return (env._joint_pos_targets[:, 0] - nominal).abs()


# =============================================================================
# Dispatch
# =============================================================================


def apply_joint1_constraint_arm(env_cfg) -> None:
    """Append the joint1-constraint-redesign experiment term to env_cfg.constraints, in place.

    MUST be called from ALBCEnv.__init__ (after hydra has applied its overrides), NOT from a
    cfg __post_init__: __post_init__ runs at cfg construction, BEFORE hydra's
    update_class_from_dict sets joint1_constraint_arm, so it would always see 'none' and
    silently leave the shipped 10-term set untouched (a baseline-dup masquerading as arm A/B).

    arm='none' is a no-op (byte-identical to the shipped config). 'A'/'B' append exactly one
    continuous Average term whose IPO budget governs its strength. The shared module-level
    _FULL_DOF_CONSTRAINT_TERMS (also used by full_dof) is never mutated: a new list is built.
    """
    arm = getattr(env_cfg, "joint1_constraint_arm", "none")
    if arm == "none":
        return
    budget = env_cfg.joint1_constraint_budget
    if arm == "A":
        term = ConstraintTermCfg(func=joint1_centering_cost, budget=budget, name="joint1_centering")
    elif arm == "B":
        term = ConstraintTermCfg(func=joint1_cumulative_cost, budget=budget, name="joint1_cumulative")
    else:
        raise ValueError(f"joint1_constraint_arm must be one of 'none'/'A'/'B', got {arm!r}")
    env_cfg.constraints.terms = [*env_cfg.constraints.terms, term]


def compute_all_costs(
    robot: Articulation,
    env: ALBCEnv,
    cfg: ALBCConstraintCfg,
) -> torch.Tensor:
    """Compute all K costs -> (num_envs, K) tensor."""
    return torch.stack([t.func(robot, env, **t.params) for t in cfg.terms], dim=-1)
