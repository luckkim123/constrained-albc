# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""2-Link planar arm kinematics for ALBC (Active Linear Buoyancy Controller).

This module implements forward and inverse kinematics for the ALBC vehicle's
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

from marinelab.assets import (
    ALBC_LINK1_LENGTH,
    ALBC_LINK2_LENGTH,
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
        link1_length: float = ALBC_LINK1_LENGTH,
        link2_length: float = ALBC_LINK2_LENGTH,
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
    ) -> torch.Tensor:
        """Compute joint angles from desired EE position via closed-form 2-link IK.

        Analytic solution for 2-link planar arm (l1, l2). Single-shot O(1)
        computation -- deployment-faithful equivalent of real-robot TDC without
        the iterative DLS / realtime-budget tradeoffs. Elbow branch is selected
        from the sign of the current g2 to preserve continuity across steps.

        Formulas:
            r^2 = x^2 + y^2 (clamped to workspace (|l1-l2|, l1+l2))
            c2 = (r^2 - l1^2 - l2^2) / (2 l1 l2)
            s2 = sign(current_g2) * sqrt(1 - c2^2)
            g2 = atan2(s2, c2)
            g1 = atan2(y, x) - atan2(l2 s2, l1 + l2 c2)

        Args:
            target_position: Desired EE position in meters. Shape: (N, 2).
            current_joint_angles: Current joint angles in radians. Shape: (N, 2).
                Only g2 sign is consulted (elbow continuity).

        Returns:
            Joint angles in radians. Shape: (N, 2).
        """
        x = target_position[:, 0]
        y = target_position[:, 1]

        # Radial clamp to the reachable annulus (inner = |l1-l2|, outer = l1+l2).
        # Slight epsilon inside boundaries avoids degenerate Jacobian at the limits.
        eps = 1e-6
        r = torch.sqrt(x * x + y * y)
        r_max = self.l1 + self.l2 - eps
        r_min = abs(self.l1 - self.l2) + eps
        r_clamped = torch.clamp(r, min=r_min, max=r_max)
        scale = r_clamped / torch.clamp(r, min=eps)
        x = x * scale
        y = y * scale

        r2 = x * x + y * y
        c2 = (r2 - self.l1 * self.l1 - self.l2 * self.l2) / (2.0 * self.l1 * self.l2)
        c2 = torch.clamp(c2, -1.0 + eps, 1.0 - eps)

        # Elbow continuity: preserve sign of current g2 (default +1 at g2 == 0).
        sign_g2 = torch.where(current_joint_angles[:, 1] >= 0.0, 1.0, -1.0)
        s2 = sign_g2 * torch.sqrt(1.0 - c2 * c2)

        g2 = torch.atan2(s2, c2)
        g1 = torch.atan2(y, x) - torch.atan2(self.l2 * s2, self.l1 + self.l2 * c2)

        return torch.stack([g1, g2], dim=-1)

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
