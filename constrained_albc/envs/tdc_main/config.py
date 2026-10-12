# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Configuration for the attitude-only ALBC TDC + thruster PD baseline.

Inherits every field from `main.ALBCEnvCfg` (DR, reward, constraints,
observation, command sampling, thruster model, DORAEMON) so the baseline
experiences the exact same evaluation conditions as
`Isaac-ConstrainedALBC-TRPO-v0`. Only adds the classical controller gains.
"""

from __future__ import annotations

from isaaclab.utils import configclass

from constrained_albc.envs.main.config import ALBCEnvCfg

from .controllers.tdc import TDCControllerCfg
from .controllers.thruster_pd import ThrusterPDCfg


@configclass
class ALBCTDCEnvCfg(ALBCEnvCfg):
    """Attitude-only ALBC env with classical TDC (arm) + P controller (thruster).

    No RL training. The `action_space` stays at 8D so that observation
    history and downstream scripts remain compatible with the RL variant.
    The 8D action vector passed to `_pre_physics_step` is ignored; the env
    overwrites it with the classical controller output before running the
    parent action pipeline.
    """

    tdc_controller: TDCControllerCfg = TDCControllerCfg()
    """Arm TDC controller for roll/pitch attitude stabilization.

    Gains inherited from the retired full-DOF TDC baseline (tag legacy-full-dof-final):
    `m_hat=(0.15, 0.16)`, `kp=48.0`, `kd=14.0`, `h=0.180`,
    `max_joint_velocity=2.5 rad/s`. The gains came from the original ROS reference
    implementation at 40.0/12.0 and were raised +20% on 2026-04-22 for OOD robustness
    (`tdc.py:48-49`, which is where the effective values live); this docstring still
    said 40/12 until 2026-09-07. Any classical-gain search starts from 48/14 --
    paper-ablation-5000 PLAN.md §8-R-3 is explicit about not starting from 40/12.
    """

    thruster_pd: ThrusterPDCfg = ThrusterPDCfg()
    """6-DOF thruster PD: lin vel (Fx,Fy,Fz) + roll/pitch (Tx,Ty) + yaw rate (Tz).

    Same gains as the retired full-DOF TDC baseline. `main` has no linear-velocity
    command (attitude-only task), so `tdc_env.ALBCTDCEnv` feeds a zero
    lin-vel target -- the controller then holds station on Fx/Fy/Fz instead
    of tracking a commanded velocity.
    """
