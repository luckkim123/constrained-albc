# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Velocity tracking reward: r = r_lin + r_ang + r_tau + r_thr + r_s.

r_lin: -k_lin * ||lin_vel_err||^2   (linear velocity command tracking)
r_ang: -k_ang * ||ang_vel_err||^2   (angular velocity command tracking)
r_tau: -k_tau * mean(tau^2)          (joint energy efficiency)
r_thr: -k_thr * mean(thruster_cmd^2) (thruster energy)
r_s:   -k_s   * (mean(da^2) + mean(d2a^2))  (action smoothness)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

import torch

from isaaclab.utils import configclass

if TYPE_CHECKING:
    from isaaclab.assets import Articulation

    from ..albc_env import ALBCEnv


# --- Configuration ---


@configclass
class ALBCRewardCfg:
    """Velocity tracking reward weights (all dt-scaled, negative weights = penalties)."""

    k_lin: float = -4.0  # linear velocity tracking
    k_ang: float = -8.0  # angular velocity tracking
    ang_vel_axis_weights: tuple[float, float, float] = (2.0, 2.0, 1.0)
    """Per-axis weights for angular velocity tracking (roll_rate, pitch_rate, yaw_rate)."""
    k_tau: float = -0.005  # joint torque
    k_thr: float = -0.01  # thruster energy
    k_s: float = -0.1  # action smoothness
    termination_penalty: float = -50.0


# --- Reward Functions ---


def lin_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_lin = ||lin_vel_err||^2. Linear velocity command tracking."""
    return env._lin_vel_err.pow(2).sum(dim=-1)


def ang_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_ang = w_p*ep^2 + w_q*eq^2 + w_r*er^2. Weighted angular velocity tracking."""
    err_sq = env._ang_vel_err.pow(2)
    w = env.cfg.reward.ang_vel_axis_weights
    return err_sq[:, 0] * w[0] + err_sq[:, 1] * w[1] + err_sq[:, 2] * w[2]


def joint_torque(robot: Articulation, env: ALBCEnv) -> torch.Tensor:
    """r_tau = mean(tau^2). Energy efficiency penalty (post-clamp applied torque)."""
    return robot.data.applied_torque[:, env._albc_joint_ids].pow(2).mean(dim=-1)


def thruster_energy(env: ALBCEnv) -> torch.Tensor:
    """r_thr = mean(thruster_cmd^2). Thruster energy penalty."""
    return env._actions[:, 2:].pow(2).mean(dim=-1)


def action_smoothness(env: ALBCEnv) -> torch.Tensor:
    """r_s = mean(da^2) + mean(d2a^2). First + second order action difference."""
    da = env._actions - env._prev_actions
    d2a = env._actions - 2.0 * env._prev_actions + env._prev_prev_actions
    return da.pow(2).mean(dim=-1) + d2a.pow(2).mean(dim=-1)


# --- Reward Manager ---


class RewardManager:
    """Computes 5-term velocity tracking reward with dt-scaling and episode tracking."""

    _NAMES = ["lin_vel", "ang_vel", "torque", "thruster", "smoothness"]

    def __init__(self, cfg: ALBCRewardCfg, num_envs: int, device: str) -> None:
        self._cfg = cfg
        self._buf = torch.zeros(num_envs, dtype=torch.float32, device=device)
        self._episode_sums = {n: torch.zeros(num_envs, dtype=torch.float32, device=device) for n in self._NAMES}

    def compute(self, robot: Articulation, dt: float, env: ALBCEnv, **_ctx: Any) -> torch.Tensor:
        """Compute total reward (dt-scaled)."""
        cfg = self._cfg
        self._buf.zero_()

        terms = [
            ("lin_vel", cfg.k_lin, lin_vel_tracking(env)),
            ("ang_vel", cfg.k_ang, ang_vel_tracking(env)),
            ("torque", cfg.k_tau, joint_torque(robot, env)),
            ("thruster", cfg.k_thr, thruster_energy(env)),
            ("smoothness", cfg.k_s, action_smoothness(env)),
        ]
        for name, weight, value in terms:
            scaled = value * weight * dt
            self._buf += scaled
            self._episode_sums[name] += scaled

        return self._buf

    def reset(self, env_ids: torch.Tensor) -> dict[str, float]:
        """Reset episode sums, return means before reset."""
        sums = {n: self._episode_sums[n][env_ids].mean().item() for n in self._NAMES}
        for n in self._NAMES:
            self._episode_sums[n][env_ids] = 0.0
        return sums
