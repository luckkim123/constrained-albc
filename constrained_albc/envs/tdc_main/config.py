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
from constrained_albc.envs.main.config_simtoreal import ALBCSimToRealEnvCfg

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


@configclass
class ALBCATDCEnvCfg(ALBCTDCEnvCfg):
    """ATDC arm (N2): TDC whose design inertia adapts online.

    Identical to the TDC arm in every respect but one flag -- same env, same PD
    gains, same IK, same thruster PD, same DR/reward/constraints -- so the variable
    under comparison is the adaptation law alone. That is why this is a config
    subclass and not a new env class: `ALBCTDCEnv` needs no change to run it.

    The arm exists because the paper names ATDC (References [5], Baek et al. 2018)
    as a comparison target and defines its own contribution against "a fixed
    adaptation form driven by tracking error only", so without this arm that claim
    has no control group (PLAN.md §3-2 N2). Training cost is zero -- classical
    control, evaluation only.

    `m_hat_adapt_gain` here is the cfg default and is UNTUNED; §5/§8-R-3 require the
    classical arms to go through a declared gain grid before their numbers are
    reportable.
    """

    tdc_controller: TDCControllerCfg = TDCControllerCfg(adaptive_m_hat=True)


@configclass
class ALBCResidualTDCEnvCfg(ALBCSimToRealEnvCfg):
    """Residual-RL-over-TDC arm (N4): section-5 plant + the classical controllers.

    Descends from the plant cfg, not from `ALBCTDCEnvCfg`, and re-declares the two
    controller fields instead. This arm trains, so under anchor (B) it needs the
    seven section-5 overrides, and they must come from the one place that owns them
    (`config_simtoreal.py`) -- copying that block into a second base is the failure
    `finding/352` is filed against. The two fields repeated below are plain defaults
    with no such hazard.

    `constraints` is inherited un-emptied on purpose: the K=10 costs are measured from
    robot state, so they score the composite TDC-plus-residual behaviour, which is what
    puts this arm on the same scale as the RL arms (PLAN.md §4-4).
    """

    tdc_controller: TDCControllerCfg = TDCControllerCfg()
    thruster_pd: ThrusterPDCfg = ThrusterPDCfg()

    residual_tau_scale: float = 0.5
    """Newton-metres of arm residual torque at |action| = 1, per axis.

    UNTUNED starting point. For scale: the classical PD torque is `m_hat * u_pd` with
    `m_hat ~ 0.15` and `u_pd ~ kp * e = 48 * 0.1 rad ~ 4.8`, i.e. of order 0.7 N*m at a
    0.1 rad error, so 0.5 gives the policy roughly comparable authority to the
    controller it is correcting. Too large and the arm stops being residual (the policy
    can overpower TDC and the comparison degenerates into A1 with extra steps); too
    small and it cannot express a correction. This is a value to sweep, not to trust.
    """
