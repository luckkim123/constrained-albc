# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""2-Link planar arm kinematics for ALBC (Active Linear Buoyancy Controller).

This module implements forward and inverse kinematics for the Hero Agent's
2-link planar arm that positions a buoyancy element for attitude control.

ALBC Arm Geometry (from IROS 2026 paper):
    l1 = l2 = 0.233 m  (link lengths, from isaaclab_assets constants)

    Joint configuration: Two revolute joints (gamma1, gamma2) operating in
    the XY plane, with the end-effector (buoyancy element) position computed
    as a function of joint angles.

Inverse Kinematics uses DLS (Damped Least Squares) Jacobian pseudo-inverse
with Yoshikawa-style adaptive damping for smooth singularity handling.
The DLS solver uses torch.linalg.solve for dimension-independent computation,
making it extensible to higher-DOF arms without structural changes.

Note: This kinematic model is defined in the robot's local frame, where:
    - X points forward (along roll axis)
    - Y points left (along pitch axis)
    - Z points up

Extension to higher-DOF:
    Subclass ALBCKinematics and override forward(), jacobian(), and _w_max.
    The DLS solver (_dls_solve), manipulability(), and inverse() work for
    any Jacobian dimensions (m x n) without modification.
"""

from __future__ import annotations

import torch

from isaaclab_assets.robots.uuv import (
    HERO_AGENT_ALBC_LINK1_LENGTH,
    HERO_AGENT_ALBC_LINK2_LENGTH,
)


class ALBCKinematics:
    """GPU-parallel kinematics for ALBC arm.

    This class provides efficient batch computation of FK and IK for the ALBC
    arm across multiple parallel environments.

    IK uses DLS Jacobian pseudo-inverse with Yoshikawa-style adaptive damping
    via torch.linalg.solve. This provides smooth singularity handling without
    workspace clamping and generalizes to arbitrary Jacobian dimensions.
    """

    def __init__(
        self,
        num_envs: int,
        device: str,
        link1_length: float = HERO_AGENT_ALBC_LINK1_LENGTH,
        link2_length: float = HERO_AGENT_ALBC_LINK2_LENGTH,
    ) -> None:
        """Initialize ALBC kinematics model.

        Args:
            num_envs: Number of parallel environments.
            device: Computation device (e.g., "cuda:0", "cpu").
            link1_length: Length of first link in meters.
            link2_length: Length of second link in meters.
        """
        self.num_envs = num_envs
        self.device = device

        # Arm parameters
        self.l1 = link1_length
        self.l2 = link2_length

        # Maximum manipulability for adaptive lambda normalization.
        # For 2-link planar: w_max = sqrt(|l1 * l2|) (at g2 = pi/2).
        # Override _w_max for different arm geometries.
        self._w_max = (abs(self.l1 * self.l2)) ** 0.5

    def forward(
        self,
        joint_angles: torch.Tensor,
    ) -> torch.Tensor:
        """Compute end-effector position from joint angles (forward kinematics).

        Standard 2-link planar FK:
            x = l1*cos(g1) + l2*cos(g1+g2)
            y = l1*sin(g1) + l2*sin(g1+g2)

        Override for different arm geometry.

        Args:
            joint_angles: Joint angles in radians. Shape: (num_envs, num_joints).

        Returns:
            End-effector position in meters. Shape: (num_envs, task_dim).
        """
        g1 = joint_angles[:, 0]
        g12 = joint_angles[:, 0] + joint_angles[:, 1]

        x = self.l1 * torch.cos(g1) + self.l2 * torch.cos(g12)
        y = self.l1 * torch.sin(g1) + self.l2 * torch.sin(g12)

        return torch.stack([x, y], dim=-1)

    def jacobian(
        self,
        joint_angles: torch.Tensor,
    ) -> torch.Tensor:
        """Compute Jacobian matrix dx/dq.

        For 2-link planar arm:
            J = [[-l1*sin(g1) - l2*sin(g1+g2),  -l2*sin(g1+g2)],
                 [ l1*cos(g1) + l2*cos(g1+g2),   l2*cos(g1+g2)]]

        Override for different arm geometry.

        Args:
            joint_angles: Joint angles in radians. Shape: (num_envs, num_joints).

        Returns:
            Jacobian matrix. Shape: (num_envs, task_dim, num_joints).
        """
        g1 = joint_angles[:, 0]
        g12 = joint_angles[:, 0] + joint_angles[:, 1]

        sin_g1 = torch.sin(g1)
        cos_g1 = torch.cos(g1)
        sin_g12 = torch.sin(g12)
        cos_g12 = torch.cos(g12)

        J = torch.zeros(joint_angles.shape[0], 2, 2, device=self.device)
        J[:, 0, 0] = -self.l1 * sin_g1 - self.l2 * sin_g12
        J[:, 0, 1] = -self.l2 * sin_g12
        J[:, 1, 0] = self.l1 * cos_g1 + self.l2 * cos_g12
        J[:, 1, 1] = self.l2 * cos_g12

        return J

    def manipulability(
        self,
        J: torch.Tensor,
    ) -> torch.Tensor:
        """Compute Yoshikawa manipulability index (dimension-normalized).

        w = det(J @ J^T) ^ (1 / (2 * task_dim))

        This normalization ensures w/w_max stays in [0, 1] regardless of
        Jacobian dimensions. For the 2-link case (task_dim=2), this reduces to
        sqrt(|l1 * l2 * sin(g2)|), matching the ALBC 3rd week slides formula.

        Args:
            J: Jacobian matrix. Shape: (num_envs, task_dim, num_joints).

        Returns:
            Manipulability index per environment. Shape: (num_envs,).
        """
        JJT = torch.bmm(J, J.transpose(-1, -2))
        m = JJT.shape[-1]
        return torch.abs(torch.linalg.det(JJT)).pow(1.0 / (2 * m))

    def inverse(
        self,
        target_position: torch.Tensor,
        current_joint_angles: torch.Tensor,
        lambda_dls: float = 0.15,
        num_iterations: int = 1,
        learning_rate: float = 1.0,
    ) -> torch.Tensor:
        """Compute joint angle update from desired EE position using iterative DLS IK.

        Uses Jacobian DLS (Damped Least Squares) pseudo-inverse with
        Yoshikawa-style adaptive damping. The DLS solver is dimension-independent
        via torch.linalg.solve, so this method works for any arm geometry
        without modification.

        Iterative mode (num_iterations > 1, learning_rate < 1.0):
            Recomputes FK, Jacobian, and adaptive lambda each iteration,
            matching the C++ reference (learning_rate=0.02, 500-3000 iters).
            Converges accurately even for large displacements where the single-step
            linear Jacobian approximation would overshoot.

        DLS formula (per iteration):
            dp = p_target - FK(q)
            delta_q = J^T (J J^T + lambda^2 I)^{-1} dp
            q = q + learning_rate * delta_q

        Adaptive lambda (Yoshikawa):
            w = det(JJ^T)^(1/(2m))  (dimension-normalized manipulability)
            lambda = lambda_base * clamp(1 - w/w_max, min=0)
            Near singularity (w~0): lambda -> lambda_base (max damping)
            Far from singularity (w~w_max): lambda -> 0 (full accuracy)

        Args:
            target_position: Desired EE position in meters.
                Shape: (num_envs, task_dim).
            current_joint_angles: Current joint angles in radians.
                Shape: (num_envs, num_joints).
            lambda_dls: Base DLS damping factor. Larger = more damping near
                singularity. Default 0.15 (from C++ reference).
            num_iterations: Number of IK iterations. 1 = single-step (original
                behavior). Higher values improve accuracy for large displacements.
            learning_rate: Step size per iteration. 1.0 = full step (original
                behavior). Smaller values (e.g. 0.02) with more iterations give
                smoother convergence matching the C++ reference.

        Returns:
            New joint angles in radians. Shape: (num_envs, num_joints).
        """
        q = current_joint_angles.clone()
        for _ in range(num_iterations):
            p_current = self.forward(q)
            dp = target_position - p_current

            J = self.jacobian(q)

            # Yoshikawa-style adaptive lambda (recomputed each iteration)
            w = self.manipulability(J)
            lam2 = (lambda_dls * torch.clamp(1.0 - w / self._w_max, min=0.0)) ** 2

            dq = self._dls_solve(J, dp, lam2)
            q = q + learning_rate * dq
        return q

    def _dls_solve(
        self,
        J: torch.Tensor,
        dp: torch.Tensor,
        lam2: torch.Tensor,
    ) -> torch.Tensor:
        """Solve DLS IK: delta_q = J^T (JJ^T + lambda^2 I)^{-1} dp.

        Uses torch.linalg.solve instead of explicit matrix inversion for
        numerical stability and dimension-independence. Works for any
        (num_envs, m, n) Jacobian where m = task_dim, n = num_joints.

        For square J (m=n), this is equivalent to the analytical inverse
        but generalizes to non-square Jacobians (over/underdetermined systems).

        Args:
            J: Jacobian. Shape: (num_envs, m, n).
            dp: Position error. Shape: (num_envs, m).
            lam2: Squared damping per-env. Shape: (num_envs,).

        Returns:
            Joint angle update. Shape: (num_envs, n).
        """
        JJT = torch.bmm(J, J.transpose(-1, -2))  # (num_envs, m, m)
        m = JJT.shape[-1]
        A = JJT + lam2.unsqueeze(-1).unsqueeze(-1) * torch.eye(m, device=J.device)

        # Solve A @ x = dp for x = (JJ^T + lam^2 I)^{-1} dp
        # Then delta_q = J^T @ x
        x = torch.linalg.solve(A, dp.unsqueeze(-1))  # (num_envs, m, 1)
        dq = torch.bmm(J.transpose(-1, -2), x).squeeze(-1)  # (num_envs, n)
        return dq
