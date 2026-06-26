# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tracking reward: r = r_att + r_lin + r_yaw + r_tau + r_thr + r_s.

All tracking terms use exp kernel + quadratic + linear penalty:
    r = k * (exp(-e^2/2s^2) - q_quad*e^2 - q_lin*|e|)
    exp kernel: positive reward in [0,1], gradient peaks at err=sigma
    quadratic: gradient grows with error magnitude
    linear: constant gradient at all error magnitudes (kills SS error tolerance)

The linear term is the critical fix for "SS error tolerance" -- both exp and
quadratic gradients vanish as err -> 0, so the policy has no incentive to push
small errors below ~5% of sigma. The linear term provides a constant downward
force on |e|, ensuring the policy keeps reducing SS error all the way to zero.

r_att:  k_att * (exp(-e^2/2s^2) - q_quad*e^2 - q_lin*|e|)
r_lin:  k_lin * (exp(-e^2/2s^2) - q_quad*e^2 - q_lin*|e|)
r_yaw:  k_yaw * (exp(-e^2/2s^2) - q_quad*e^2 - q_lin*|e|)
r_tau:  -k_tau * mean(tau^2)                 (joint energy efficiency)
r_thr:  -k_thr * mean(thruster_cmd^2)       (thruster energy)
r_s:    -k_s   * (mean(da^2) + mean(d2a^2)) (action smoothness)
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Any

import torch

from isaaclab.utils import configclass

if TYPE_CHECKING:
    from isaaclab.assets import Articulation

    from ..albc_env import ALBCEnv


# --- Configuration ---


@configclass
class TrackingTermCfg:
    """Config for a single tracking reward term (exp kernel + quadratic + saturating penalty).

    r = k * (exp(-e^2/2s^2) - quad_ratio*e^2 - lin_ratio*|e| - saturating_penalty)

    Saturating penalty options (active if coef > 0, only one of tanh/arctan at a time):
      tanh:   coef * eps * tanh(|e|/eps)    -- sech^2-decay, grad at 0 = coef
      arctan: coef * eps * (2/pi) * atan(|e|/eps) -- 1/(1+x^2)-decay
    """

    k: float = 1.0  # reward weight (dt-scaled)
    sigma: float = 0.10  # exp kernel sigma
    quad_ratio: float = 1.0  # quadratic/exp weight ratio
    lin_ratio: float = 0.0  # linear penalty ratio (disabled: caused dead zone)
    tanh_coef: float = 0.0  # saturating tanh coefficient
    tanh_eps: float = 0.10  # tanh saturation scale (match sigma by default)
    arctan_coef: float = 0.0  # saturating arctan coefficient
    arctan_eps: float = 0.10  # arctan saturation scale


@configclass
class ALBCRewardCfg:
    """Tracking reward config. Three tracking terms + penalty terms."""

    att_rp: TrackingTermCfg = TrackingTermCfg(k=9.0, sigma=0.10, quad_ratio=0.833)
    att_roll_weight: float = 1.5  # roll weight in err_sq (weak TAM actuation: 0.007m vs pitch 0.145m)
    lin_vel: TrackingTermCfg = TrackingTermCfg(k=4.0, sigma=0.10, quad_ratio=1.0)
    yaw_vel: TrackingTermCfg = TrackingTermCfg(k=3.5, sigma=0.10, quad_ratio=1.0)
    k_tau: float = -0.01  # joint torque penalty
    k_thr: float = -0.35  # thruster energy penalty
    k_s: float = -0.1  # action smoothness penalty
    # Joint1 (arm rotation) centering penalty. Joint1 is a free DOF under a pure
    # delta-integrator with no restoring signal, so sim-to-real micro-bias drifts
    # it monotonically on the real robot. This penalizes the *wrapped* angular
    # distance from nominal (0 rad), so a continuous-rotation motor is not falsely
    # penalized for a full turn back to the same pose. Default 0.0 = disabled
    # (byte-identical to runs without this term).
    k_joint1_center: float = 0.0
    termination_penalty: float = 0.0
    # EMA bias penalty (r11_emabias): penalize sustained per-env tracking offset that
    # per-step reward cannot see. bias_ema = a * bias_ema + (1-a) * err per axis.
    # Default k_bias=0 disables; r11_emabias overrides to nonzero.
    k_bias: float = 0.0
    bias_ema_alpha: float = 0.99  # effective window ~100 steps = 2 s at 50 Hz
    # Per-axis weights for bias penalty so roll (weak authority) gets stronger bias signal.
    bias_weights: tuple[float, float, float] = (1.5, 1.0, 1.0)


# --- Reward Functions ---


def _exp_quad_saturating(
    err_sq: torch.Tensor,
    err_norm: torch.Tensor,
    term: TrackingTermCfg,
) -> torch.Tensor:
    """Shared tracking reward kernel: exp(-e^2/2s^2) - quad*e^2 - lin*|e| - saturating.

    Args:
        err_sq: Squared error (may be weighted). Shape: (num_envs,).
        err_norm: Norm or weighted absolute error. Shape: (num_envs,).
        term: Tracking term config with sigma, ratios, and saturating coefficients.
    """
    exp_term = torch.exp(-err_sq / (2.0 * term.sigma**2))
    penalty = term.quad_ratio * err_sq + term.lin_ratio * err_norm
    if term.tanh_coef > 0.0:
        penalty = penalty + term.tanh_coef * term.tanh_eps * torch.tanh(err_norm / term.tanh_eps)
    if term.arctan_coef > 0.0:
        penalty = penalty + term.arctan_coef * term.arctan_eps * (2.0 / math.pi) * torch.atan(
            err_norm / term.arctan_eps
        )
    return exp_term - penalty


# UNUSED in attitude_only (kept for cfg compatibility; not in RewardManager).
def lin_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_lin: Euclidean norm tracking for linear velocity."""
    err_sq = env._lin_vel_err.pow(2).sum(dim=-1)
    err_norm = err_sq.clamp(min=1e-12).sqrt()
    return _exp_quad_saturating(err_sq, err_norm, env.cfg.reward.lin_vel)


def att_rp_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_att: Roll-weighted attitude tracking (Manhattan norm for saturating terms).

    e_w^2 = w_roll * roll_err^2 + pitch_err^2 (quadratic weighting).
    |e_w| = w_roll * |roll_err| + |pitch_err| (Manhattan weighting for penalties).
    """
    cfg = env.cfg.reward
    rp_err = env._att_rp_err  # (num_envs, 2): [roll_err, pitch_err]
    err_sq = cfg.att_roll_weight * rp_err[:, 0].pow(2) + rp_err[:, 1].pow(2)
    err_abs_w = cfg.att_roll_weight * rp_err[:, 0].abs() + rp_err[:, 1].abs()
    return _exp_quad_saturating(err_sq, err_abs_w, cfg.att_rp)


def yaw_vel_tracking(env: ALBCEnv) -> torch.Tensor:
    """r_yaw: Scalar tracking for yaw rate."""
    err = env._yaw_rate_err
    return _exp_quad_saturating(err.pow(2), err.abs(), env.cfg.reward.yaw_vel)


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


def bias_ema_penalty(env: ALBCEnv) -> torch.Tensor:
    """r_bias = sum_i w_i * bias_ema_i^2. Sustained-offset penalty.

    Uses env._bias_ema (3D, ungated EMA of [roll, pitch, yaw_rate] tracking errors)
    updated each step. Squared form so reward gradient grows with offset; per-axis
    weights let roll (weak TAM authority) receive a stronger anti-bias signal than yaw.
    """
    w = env._reward_manager._bias_w
    return (env._bias_ema.pow(2) * w).sum(dim=-1)


def joint1_centering_penalty(env: ALBCEnv) -> torch.Tensor:
    """r_jc = wrap(theta1)^2. Centering penalty on joint1 (arm rotation).

    Joint1 is a continuous-rotation motor with no PhysX position limit, driven by a
    pure delta-integrator (q_des += delta_scale * a). Nothing pulls it back to
    nominal (0 rad), so sim-to-real bias accumulates into monotonic drift on the
    real robot. This term supplies the missing restoring gradient.

    The angle is wrapped to (-pi, pi] before squaring so that theta1 = 2*pi (one
    full revolution, physically identical to 0) is NOT penalized as if it were far
    from nominal -- only the genuine angular distance from nominal is penalized.
    Returns non-negative magnitude; the negative sign lives in cfg.k_joint1_center.
    """
    theta1 = env._robot.data.joint_pos[:, env._albc_joint_ids[0]]
    wrapped = torch.atan2(torch.sin(theta1), torch.cos(theta1))
    return wrapped.pow(2)


# --- Reward Manager ---


class RewardManager:
    """Computes 6-term tracking reward with dt-scaling and episode tracking."""

    _NAMES = ["att_rp", "yaw_vel", "torque", "thruster", "smoothness", "bias", "joint1_center"]

    def __init__(self, cfg: ALBCRewardCfg, num_envs: int, device: str) -> None:
        self._cfg = cfg
        self._buf = torch.zeros(num_envs, dtype=torch.float32, device=device)
        self._episode_sums = {n: torch.zeros(num_envs, dtype=torch.float32, device=device) for n in self._NAMES}
        # Preallocated per-axis bias weights (used by bias_ema_penalty each step).
        self._bias_w = torch.tensor(cfg.bias_weights, dtype=torch.float32, device=device)

    def compute(self, robot: Articulation, dt: float, env: ALBCEnv, **_ctx: Any) -> torch.Tensor:
        """Compute total reward (dt-scaled)."""
        cfg = self._cfg
        self._buf.zero_()

        terms = [
            ("att_rp", cfg.att_rp.k, att_rp_tracking(env)),
            ("yaw_vel", cfg.yaw_vel.k, yaw_vel_tracking(env)),
            ("torque", cfg.k_tau, joint_torque(robot, env)),
            ("thruster", cfg.k_thr, thruster_energy(env)),
            ("smoothness", cfg.k_s, action_smoothness(env)),
            ("bias", cfg.k_bias, bias_ema_penalty(env)),
            ("joint1_center", cfg.k_joint1_center, joint1_centering_penalty(env)),
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
