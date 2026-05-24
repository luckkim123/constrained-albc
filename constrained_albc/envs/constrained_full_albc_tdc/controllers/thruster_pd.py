# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Stateless 6-DOF wrench PD controller with thruster allocation.

The controller drives **all six** body-frame wrench components so the
thruster contributes to roll, pitch, yaw, and linear-velocity tracking on
equal footing with the arm TDC. This is the only honest comparison baseline
to a 6D RL policy that has access to the full thruster authority.

Layout:
    Fx, Fy, Fz   - linear velocity tracking, body frame
    Tx, Ty       - roll/pitch attitude tracking (PD: P on error - D on rate)
    Tz           - yaw rate tracking (P)

Wrench is allocated to the six Hero Agent thrusters via the pseudo-inverse
of the (6x6) thruster allocation matrix and normalized to the [-1, 1]
command range expected by `ThrusterModel.apply_dynamics`.
"""

from __future__ import annotations

import torch

from isaaclab.utils import configclass


@configclass
class ThrusterPDCfg:
    """Gains and normalization for the 6-DOF thruster PD controller.

    Default values are tuned to minimize steady-state error within the
    saturation budget of the Hero Agent thrusters (max 50 N each, nominal
    40 N at command 1.0). P-only control leaves a residual proportional to
    drag/disturbance divided by Kp; the gains here trade off SS error against
    overshoot from Kd damping.
    """

    kp_lin: float = 120.0
    """P gain for linear velocity tracking (Fx, Fy, Fz; body frame).

    Tuned 2026-04-22 from 100 -> 120 (+20%) to reduce SS error under OOD
    payload/drag. SS error formula: v_err = F_drag / kp_lin.
    """

    kp_att: float = 24.0
    """P gain for roll/pitch attitude tracking (Tx, Ty). Tuned 20->24 (+20%)
    to maintain bandwidth under OOD inertia scaling (2.3x)."""

    kd_att: float = 6.0
    """D gain on body angular velocity for roll/pitch (rate damping).
    Tuned 5->6 to keep zeta near original design point after kp bump."""

    kp_yaw: float = 30.0
    """P gain for yaw rate tracking (Tz). Tuned 25->30 (+20%)."""

    thrust_coefficient: float = 40.0
    """Per-thruster force magnitude at a normalized command of 1.0 (Newtons).

    Must match the `thrust_coefficient` in the env thruster configuration so
    the inverse normalization maps forces back to the [-1, 1] command range.
    """


class ThrusterPDController:
    """6-DOF wrench PD controller with TAM pseudo-inverse allocation.

    Stateless: no integrator, no filter. Each step it
        1. builds a 6D body-frame wrench (P on linear/yaw errors, PD on
           roll/pitch attitude),
        2. allocates to per-thruster forces via the pre-computed `TAM^+`,
        3. normalizes by `thrust_coefficient` and clips to [-1, 1].
    """

    def __init__(
        self,
        num_envs: int,
        device: str,
        cfg: ThrusterPDCfg,
        allocation_matrix: tuple[tuple[float, ...], ...] | torch.Tensor,
    ) -> None:
        """Initialize the controller.

        Args:
            num_envs: Number of parallel environments.
            device: Torch device (e.g. "cuda:0").
            cfg: Gains and normalization.
            allocation_matrix: 6x6 TAM mapping per-thruster forces to the
                body-frame wrench [Fx, Fy, Fz, Tx, Ty, Tz]. Either a tuple of
                tuples (from `HeroAgentThrusterCfg.allocation_matrix`) or a
                pre-built tensor.
        """
        self.num_envs = num_envs
        self.device = device
        self.cfg = cfg

        if isinstance(allocation_matrix, torch.Tensor):
            tam = allocation_matrix.to(device=device, dtype=torch.float32)
        else:
            tam = torch.tensor(allocation_matrix, device=device, dtype=torch.float32)
        if tam.shape != (6, 6):
            raise ValueError(f"allocation_matrix must be 6x6, got {tuple(tam.shape)}")
        # Precompute pseudo-inverse once (TAM is fixed geometry).
        self._tam_pinv = torch.linalg.pinv(tam)

    def compute(
        self,
        lin_vel_cmd_body: torch.Tensor,
        roll: torch.Tensor,
        pitch: torch.Tensor,
        roll_cmd: torch.Tensor,
        pitch_cmd: torch.Tensor,
        yaw_rate_cmd: torch.Tensor,
        lin_vel_body: torch.Tensor,
        ang_vel_body: torch.Tensor,
    ) -> torch.Tensor:
        """Compute normalized thruster commands for all 6 wrench components.

        Args:
            lin_vel_cmd_body: Body-frame linear velocity command. Shape (N, 3).
            roll: Current roll angle in radians. Shape (N,).
            pitch: Current pitch angle in radians. Shape (N,).
            roll_cmd: Target roll in radians. Shape (N,).
            pitch_cmd: Target pitch in radians. Shape (N,).
            yaw_rate_cmd: Body-frame yaw rate command in rad/s. Shape (N,).
            lin_vel_body: Current body-frame linear velocity. Shape (N, 3).
            ang_vel_body: Current body-frame angular velocity. Shape (N, 3).

        Returns:
            Normalized thruster commands in [-1, 1]. Shape (N, 6).
        """
        v_err = lin_vel_cmd_body - lin_vel_body  # (N, 3)
        # Roll/pitch attitude error wrapped to [-pi, pi].
        roll_err_raw = roll_cmd - roll
        pitch_err_raw = pitch_cmd - pitch
        roll_err = torch.atan2(torch.sin(roll_err_raw), torch.cos(roll_err_raw))
        pitch_err = torch.atan2(torch.sin(pitch_err_raw), torch.cos(pitch_err_raw))
        yaw_rate_err = yaw_rate_cmd - ang_vel_body[:, 2]

        wrench = torch.zeros(self.num_envs, 6, device=self.device)
        wrench[:, 0:3] = self.cfg.kp_lin * v_err
        # PD: P on attitude error, D on body angular rate (rate damping).
        wrench[:, 3] = self.cfg.kp_att * roll_err - self.cfg.kd_att * ang_vel_body[:, 0]
        wrench[:, 4] = self.cfg.kp_att * pitch_err - self.cfg.kd_att * ang_vel_body[:, 1]
        wrench[:, 5] = self.cfg.kp_yaw * yaw_rate_err

        thrust_forces = torch.einsum("ij,nj->ni", self._tam_pinv, wrench)
        return torch.clamp(thrust_forces / self.cfg.thrust_coefficient, -1.0, 1.0)
