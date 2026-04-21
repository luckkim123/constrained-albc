# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for the Full-DOF ALBC TDC + thruster PD baseline.

Inherits every field from `ALBCEnvCfg` (DR, reward, constraints, observation,
command sampling, thruster model, DORAEMON) so the baseline experiences the
exact same training conditions as `Isaac-FullDOF-TRPO-v0`. Only adds the
classical controller gains.
"""

from __future__ import annotations

from isaaclab.utils import configclass

from isaaclab_tasks.direct.constrained_full_albc.config import ALBCEnvCfg

from .controllers.tdc import TDCControllerCfg
from .controllers.thruster_pd import ThrusterPDCfg


@configclass
class FullDOFTDCEnvCfg(ALBCEnvCfg):
    """Full-DOF ALBC env with classical TDC (arm) + P controller (thruster).

    No RL training. The `action_space` stays at 8D so that observation
    history and downstream scripts remain compatible with the RL variants.
    The 8D action vector passed to `_pre_physics_step` is ignored; the env
    overwrites it with the classical controller output before running the
    parent action pipeline.
    """

    tdc_controller: TDCControllerCfg = TDCControllerCfg(
        # Single-step DLS IK for fast eval (overrides the C++ reference's
        # 100-iteration accurate mode used by hero_agent). Single-step is the
        # ALBCKinematics function default and accurate enough for the small
        # delta-per-step that the rate limiter (max_joint_velocity * step_dt
        # = 0.05 rad) lets through.
        ik_num_iterations=1,
        ik_learning_rate=1.0,
    )
    """Arm TDC controller for roll/pitch attitude stabilization.

    Other parameters inherit from the hero_agent reference implementation
    (`m_hat=(0.15, 0.16)`, `kp=40.0`, `kd=12.0`, `h=0.180`,
    `max_joint_velocity=2.5 rad/s`).
    """

    thruster_pd: ThrusterPDCfg = ThrusterPDCfg()
    """6-DOF thruster PD: lin vel (Fx,Fy,Fz) + roll/pitch (Tx,Ty) + yaw rate (Tz)."""
