# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Full-DOF ALBC environment driven by classical TDC + thruster P controller.

This subclass replaces the RL policy with a fixed classical control pipeline:
    - Arm 2D (roll/pitch): TDC + DLS IK (reuses `hero_agent.controllers.tdc`)
    - Thruster 6D (surge/sway/heave/yaw): body-frame velocity/rate P control

All other behaviour -- domain randomization, reward, constraints, observation,
command sampling, DORAEMON curriculum -- is inherited unchanged from
`ALBCEnv` so the baseline faces identical conditions to the RL variants.

Action pipeline integration
---------------------------
`ALBCEnv._pre_physics_step` integrates arm actions as deltas
(`_joint_pos_targets += delta_scale * a[:, 0:2]`) and passes thruster actions
through a first-order lag filter. Instead of reimplementing this, we compute
the classical controller output as an 8D pseudo-action and delegate to
`super()._pre_physics_step`:
    1. Compute TDC absolute joint target, rate-limited to match the RL-equivalent
       delta budget (`max_joint_velocity * step_dt`).
    2. Encode it as a delta action `(joint_target - _joint_pos_targets) / delta_scale`
       so the parent's integration restores the exact absolute target.
    3. Compute normalized thruster commands via `ThrusterPDController`.
    4. Pack into an 8D tensor and call `super()._pre_physics_step` so that
       observation history, reward/cost accounting, and thruster lag all run
       as if these actions came from a policy.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

import torch

from isaaclab.utils.math import euler_xyz_from_quat

from isaaclab_tasks.direct.constrained_full_albc.albc_env import ALBCEnv
from isaaclab_tasks.direct.hero_agent.controllers.kinematics import ALBCKinematics
from isaaclab_tasks.direct.hero_agent.controllers.tdc import TDCController

from .controllers.thruster_pd import ThrusterPDController

if TYPE_CHECKING:
    from .config import FullDOFTDCEnvCfg


class FullDOFTDCEnv(ALBCEnv):
    """Full-DOF ALBC environment driven by classical controllers (no RL)."""

    cfg: FullDOFTDCEnvCfg

    def __init__(self, cfg: FullDOFTDCEnvCfg, render_mode: str | None = None, **kwargs) -> None:
        super().__init__(cfg, render_mode, **kwargs)

        if self._thruster is None:
            raise RuntimeError(
                "FullDOFTDCEnv requires `cfg.thrusters` to be set; the thruster "
                "PD controller cannot operate without the ThrusterModel/TAM."
            )

        tdc_cfg = cfg.tdc_controller
        # TDC `compute()` runs once per `_pre_physics_step`, which fires every
        # `step_dt` seconds. This is the TDE delay L and the rate-limit window.
        self._tdc_dt = self.step_dt
        # Per-control-step joint position budget (matches TDC's rate limit).
        self._tdc_max_joint_delta = tdc_cfg.max_joint_velocity * self._tdc_dt

        self._kinematics = ALBCKinematics(
            num_envs=self.num_envs,
            device=str(self.device),
            link1_length=tdc_cfg.link1_length,
            link2_length=tdc_cfg.link2_length,
        )
        self._tdc = TDCController(
            num_envs=self.num_envs,
            device=str(self.device),
            cfg=tdc_cfg,
            F_bu=self._buoy_hydro.buoyancy_force,
            dt=self._tdc_dt,
        )
        self._thruster_pd = ThrusterPDController(
            num_envs=self.num_envs,
            device=str(self.device),
            cfg=cfg.thruster_pd,
            allocation_matrix=cfg.thrusters.allocation_matrix,
        )

    # ------------------------------------------------------------------
    # Action pipeline: replace RL action with classical controller output.
    # ------------------------------------------------------------------

    def _pre_physics_step(self, actions: torch.Tensor) -> None:
        """Overwrite the incoming RL action with the classical controller output."""
        del actions  # The classical controllers ignore policy actions.
        with torch.no_grad():
            classical_actions = self._compute_classical_actions()
            super()._pre_physics_step(classical_actions)

    def _compute_classical_actions(self) -> torch.Tensor:
        """Run TDC + thruster PD and pack the result into an 8D action tensor.

        The arm half is emitted as the delta that, after the parent's
        `_apply_joint_pd_action` integration, reproduces the rate-limited
        absolute joint target. The thruster half is the normalized command
        consumed by `ThrusterModel.apply_dynamics`.
        """
        # --- State extraction ---------------------------------------------------
        root_quat = self._robot.data.root_quat_w
        roll, pitch, _ = euler_xyz_from_quat(root_quat)
        ang_vel_b = self._robot.data.root_ang_vel_b
        lin_vel_b = self._robot.data.root_lin_vel_b

        # --- Arm TDC pipeline ---------------------------------------------------
        # Target roll/pitch come from _ang_cmd[:, :2]; yaw slot is unused by TDC.
        target_euler = torch.stack(
            [self._ang_cmd[:, 0], self._ang_cmd[:, 1], torch.zeros_like(roll)],
            dim=-1,
        )
        p_ee_desired = self._tdc.compute(roll, pitch, ang_vel_b, target_euler)

        # IK starting point is the accumulated joint target (the arm's
        # commanded trajectory), matching `hero_agent/tdc_env.py:249`. Using
        # `_joint_pos_targets` here is required for the delta round-trip
        # below: encoding `(target - _joint_pos_targets) / delta_scale` into
        # the 8D action lets the parent's delta integration reproduce the
        # rate-limited absolute target exactly.
        current_joints = self._joint_pos_targets.clone()
        tdc_cfg = self.cfg.tdc_controller
        joint_target = self._kinematics.inverse(
            target_position=p_ee_desired,
            current_joint_angles=current_joints,
            lambda_dls=tdc_cfg.ik_dls_lambda,
            num_iterations=tdc_cfg.ik_num_iterations,
            learning_rate=tdc_cfg.ik_learning_rate,
        )

        # Rate-limit to the TDC velocity budget, then feed the anti-windup FK back.
        joint_delta_abs = torch.clamp(
            joint_target - current_joints,
            -self._tdc_max_joint_delta,
            self._tdc_max_joint_delta,
        )
        joint_target = current_joints + joint_delta_abs
        p_ee_actual = self._kinematics.forward(joint_target)
        self._tdc.update_ee_position(p_ee_actual)

        # Encode as a delta action so the parent integration restores `joint_target`.
        arm_delta_action = torch.clamp(joint_delta_abs / self.cfg.delta_scale, -1.0, 1.0)

        # --- Thruster 6-DOF PD controller --------------------------------------
        # Thruster drives all 6 wrench components on equal footing with arm
        # TDC -- this is the only fair comparison to the RL policy that has
        # access to the full thruster authority.
        thruster_cmds = self._thruster_pd.compute(
            lin_vel_cmd_body=self._vel_cmd_lin,
            roll=roll,
            pitch=pitch,
            roll_cmd=self._ang_cmd[:, 0],
            pitch_cmd=self._ang_cmd[:, 1],
            yaw_rate_cmd=self._ang_cmd[:, 2],
            lin_vel_body=lin_vel_b,
            ang_vel_body=ang_vel_b,
        )

        return torch.cat([arm_delta_action, thruster_cmds], dim=-1)

    # ------------------------------------------------------------------
    # Reset: propagate post-DR buoyancy force to the TDC controller.
    # ------------------------------------------------------------------

    def _reset_idx(self, env_ids: torch.Tensor | None) -> None:
        super()._reset_idx(env_ids)
        # Coerce None / full-batch env_ids to the canonical tensor form used
        # by ALBCEnv. Matches the hero_agent/tdc_env.py reset pattern.
        env_ids_ = self._coerce_env_ids(env_ids)
        self._tdc.reset(env_ids_)
        # DR randomizes volume -> buoyancy force changes every reset; push the
        # post-DR value so the TDC law uses the correct F_bu.
        self._tdc.update_controller_params(
            F_bu=self._buoy_hydro.buoyancy_force[env_ids_],
            env_ids=env_ids_,
        )
