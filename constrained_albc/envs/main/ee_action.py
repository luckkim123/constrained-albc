# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""EE-delta action layer: maps a normalized [-1,1] arm action to joint targets.

Replaces the joint-delta integrator (q += delta_scale * a) with an EE-space
integrator (q_ee += delta_scale * a) plus a leak toward nominal, followed by a
differentiable closed-form 2-link inverse kinematics. The EE target lives on a
finite workspace disk, so joint1 cannot run away like an unbounded joint
integrator (real-robot drift fix). The leak gives the integrator a finite
equilibrium under a persistent biased action.
"""

from __future__ import annotations

import torch

from constrained_albc.envs.tdc.controllers.kinematics import ALBCKinematics


class EEActionLayer:
    """EE-delta integrate -> leak -> workspace clamp -> differentiable IK."""

    def __init__(
        self,
        num_envs: int,
        device: str,
        ee_delta_scale: float = 0.02,
        ee_leak: float = 0.02,
        nom_ee: tuple[float, float] = (0.233, 0.233),
        link1: float = 0.233,
        link2: float = 0.233,
    ) -> None:
        self.num_envs = num_envs
        self.device = device
        self.delta_scale = ee_delta_scale
        self.leak = ee_leak
        self.l1 = link1
        self.l2 = link2
        self._r_max = link1 + link2 - 1e-6
        self._kin = ALBCKinematics(num_envs, device, link1, link2)
        self._nom_ee = torch.tensor(nom_ee, device=device).expand(num_envs, -1).clone()
        self._ee_target = self._nom_ee.clone()

    @property
    def ee_target(self) -> torch.Tensor:
        return self._ee_target

    def reset(self, env_ids: torch.Tensor, cur_joint: torch.Tensor) -> None:
        """Reset the EE target of the given envs to FK of their current joints."""
        self._ee_target[env_ids] = self._kin.forward(cur_joint[env_ids])

    def step(self, a_arm: torch.Tensor, cur_joint: torch.Tensor) -> torch.Tensor:
        """Integrate EE-delta with leak, clamp to workspace, solve IK.

        Args:
            a_arm: Normalized arm action in [-1, 1]. Shape: (N, 2).
            cur_joint: Current joint angles (g1, g2) for elbow continuity. Shape: (N, 2).

        Returns:
            Joint targets (g1, g2). Shape: (N, 2).
        """
        q_ee = (1.0 - self.leak) * self._ee_target + self.leak * self._nom_ee + self.delta_scale * a_arm
        # Workspace clamp: smooth Pade saturation applied only when r > r_max.
        # r_eff = r_max * r / (r + r_max) maps (0, inf) -> (0, r_max) and is the
        # identity near the origin, so interior EE targets are not distorted.
        # Applying it only when r > r_max keeps the stored target strictly inside
        # the reachable disk, giving the leak a finite interior equilibrium instead
        # of pinning to the boundary under a persistent biased action.
        r = q_ee.norm(dim=-1, keepdim=True)
        r_eff = self._r_max * r / (r + self._r_max)
        scale = torch.where(r > self._r_max, r_eff / torch.clamp(r, min=1e-6), torch.ones_like(r))
        q_ee = q_ee * scale
        self._ee_target = q_ee
        return self._kin.inverse(q_ee, cur_joint)
