# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tracking reward: r = r_att + r_lin + r_yaw + r_tau + r_thr + r_s.

All tracking terms use exp kernel + quadratic penalty:
    r = k * (exp(-e^2/2s^2) - q*e^2)
    exp kernel: positive reward in [0,1], gradient peaks at err=sigma
    quadratic: persistent gradient at small errors where exp saturates

r_att:  k_att * (exp(-e^2/2s^2) - q*e^2)   (roll/pitch attitude, s=0.15 rad)
r_lin:  k_lin * (exp(-e^2/2s^2) - q*e^2)   (linear velocity, s=0.15 m/s)
r_yaw:  k_yaw * (exp(-e^2/2s^2) - q*e^2)   (yaw rate, s=0.20 rad/s)
r_tau:  -k_tau * mean(tau^2)                 (joint energy efficiency)
r_thr:  -k_thr * mean(thruster_cmd^2)       (thruster energy)
r_s:    -k_s   * (mean(da^2) + mean(d2a^2)) (action smoothness)
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
    """Tracking reward weights (dt-scaled). All tracking terms use exp + quadratic."""

    k_att_rp: float = 6.0  # roll/pitch attitude (exp + quad)
    att_rp_sigma: float = 0.15  # exp kernel sigma (radians, ~8.6 deg; target 5 deg)
    att_rp_quad_ratio: float = 0.833  # quadratic/exp weight ratio
    k_lin: float = 4.0  # linear velocity (exp + quad)
    lin_vel_sigma: float = 0.15  # exp kernel sigma (m/s; target 0.05 m/s/axis)
    lin_vel_quad_ratio: float = 1.0  # quadratic/exp weight ratio
    k_yaw: float = 2.0  # yaw rate (exp + quad)
    yaw_vel_sigma: float = 0.20  # exp kernel sigma (rad/s; target 0.1 rad/s)
    yaw_vel_quad_ratio: float = 1.0  # quadratic/exp weight ratio
    k_tau: float = -0.01  # joint torque penalty
    k_thr: float = -0.35  # thruster energy penalty
    k_s: float = -0.1  # action smoothness penalty
    termination_penalty: float = 0.0


# --- Reward Functions ---


def lin_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_lin = exp(-||e||^2/2s^2) - q*||e||^2. Linear velocity tracking (exp + quad)."""
    cfg = env.cfg.reward
    err_sq = env._lin_vel_err.pow(2).sum(dim=-1)
    exp_term = torch.exp(-err_sq / (2.0 * cfg.lin_vel_sigma ** 2))
    return exp_term - cfg.lin_vel_quad_ratio * err_sq


def att_rp_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_att = exp(-e^2/2s^2) - q*e^2. Combined exp kernel + quadratic penalty.

    Exp kernel: positive reward in [0, 1], strong gradient for large errors.
    Quadratic: persistent gradient at small errors where exp kernel saturates.
    At err=3 deg, exp kernel alone gives 0.9915 (99.15%) -- quadratic adds ~27%
    more gradient pressure at all error magnitudes for SS error convergence.
    """
    cfg = env.cfg.reward
    err_sq = env._att_rp_err.pow(2).sum(dim=-1)
    exp_term = torch.exp(-err_sq / (2.0 * cfg.att_rp_sigma * cfg.att_rp_sigma))
    return exp_term - cfg.att_rp_quad_ratio * err_sq


def yaw_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_yaw = exp(-e^2/2s^2) - q*e^2. Yaw rate tracking (exp + quad)."""
    cfg = env.cfg.reward
    err_sq = env._yaw_rate_err.pow(2)
    exp_term = torch.exp(-err_sq / (2.0 * cfg.yaw_vel_sigma ** 2))
    return exp_term - cfg.yaw_vel_quad_ratio * err_sq


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
    """Computes 6-term tracking reward with dt-scaling and episode tracking."""

    _NAMES = ["lin_vel", "att_rp", "yaw_vel", "torque", "thruster", "smoothness"]

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
            ("att_rp", cfg.k_att_rp, att_rp_tracking(env)),
            ("yaw_vel", cfg.k_yaw, yaw_vel_tracking(env)),
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
