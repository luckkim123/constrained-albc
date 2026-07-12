# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Attitude-only tracking reward (6 terms), summed with dt-scaling.

  r = r_att + r_yaw + r_tau + r_thr + r_s + r_bias

Tracking terms (att, yaw) use an exp kernel + quadratic + saturating penalty:
    r = k * (exp(-e^2/2s^2) - q_quad*e^2 - q_lin*|e| - saturating)
    exp kernel: positive reward in [0,1], gradient peaks at err=sigma
    quadratic:  gradient grows with error magnitude
    linear:     constant gradient at all magnitudes (would remove the SS-error
                dead zone) -- DISABLED (lin_ratio=0; see TrackingTermCfg.lin_ratio)
    saturating: bounded tanh/arctan penalty with a nonzero gradient at err=0

The exp + quadratic gradients both vanish as err -> 0, leaving a "dead zone"
where the policy has no incentive to push small errors below ~5% of sigma. A
linear penalty was the original fix but it caused its own dead zone and was
disabled (lin_ratio=0 everywhere shipped). The live mitigation is the saturating
tanh term on r_yaw (config.py, tanh_coef=0.3); r_att has no saturating term, so
its SS-error dead zone remains.

r_att:  k_att * (exp(-e^2/2s^2) - q_quad*e^2)          (roll/pitch attitude)
r_yaw:  k_yaw * (exp(-e^2/2s^2) - q_quad*e^2 - tanh)   (yaw rate; tanh live)
r_tau:  k_tau * mean(tau^2)                 (joint torque energy;   k_tau  < 0)
r_thr:  k_thr * mean(thruster_cmd^2)        (thruster energy;       k_thr  < 0)
r_s:    k_s   * (mean(da^2) + mean(d2a^2))  (action smoothness;     k_s    < 0)
r_bias: k_bias * sum_i w_i * bias_ema_i^2   (sustained offset;   default off)

joint1 anti-drift is handled constraint-side (joint1_constraint_arm in config.py),
not by a reward term -- the reward-side centering penalty was removed 2026-07.
"""

from __future__ import annotations

import math
from collections.abc import Callable
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

    lin_ratio is 0 in every shipped config (the linear penalty caused a dead
    zone); the kernel keeps the term so the field can still be set for ablations.

    Saturating penalty options (active if coef > 0; convention is at most one of
    tanh/arctan, but the two `if` branches are independent, not code-enforced --
    both stack additively if both coefs are > 0):
      tanh:   coef * eps * tanh(|e|/eps)    -- sech^2-decay, grad at 0 = coef
      arctan: coef * eps * (2/pi) * atan(|e|/eps) -- 1/(1+x^2)-decay,
              grad at 0 = (2/pi)*coef ~= 0.637*coef (heavier/Cauchy tail: manages
              far errors longer than tanh's lighter exp-like tail)
    Shipped config uses ONLY tanh (on r_yaw, tanh_coef=0.3); arctan_coef is never
    set nonzero. arctan is kept as an unused heavy-tail alternative -- a candidate
    for future experiments that need a saturating term with a longer reach (e.g.
    to fill the r_att dead zone), not dead code.
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
class RewardTermCfg:
    """Single extra reward term: value function + dt-scaled weight.

    Mirrors ConstraintTermCfg (mdp/constraints.py) so experiments add reward
    terms cfg-side (``env_cfg.reward.extra_terms = [*terms, RewardTermCfg(...)]``)
    instead of editing RewardManager.compute(). ``func(robot, env, **params)``
    returns the UNSCALED per-env value, shape (num_envs,); the manager applies
    ``weight * dt`` exactly like every builtin term.
    """

    func: Callable = lambda _r, _e: torch.zeros(1)
    params: dict = {}
    weight: float = 0.0
    name: str = ""


@configclass
class ALBCRewardCfg:
    """Tracking reward config. Two tracking terms (att_rp, yaw_vel) + penalty terms."""

    att_rp: TrackingTermCfg = TrackingTermCfg(k=9.0, sigma=0.10, quad_ratio=0.833)
    att_roll_weight: float = 1.5  # roll weight in err_sq (weak TAM actuation: 0.007m vs pitch 0.145m)
    yaw_vel: TrackingTermCfg = TrackingTermCfg(k=3.5, sigma=0.10, quad_ratio=1.0)
    k_tau: float = -0.01  # joint torque penalty
    k_thr: float = -0.35  # thruster energy penalty
    k_s: float = -0.1  # action smoothness penalty
    termination_penalty: float = 0.0
    # EMA bias penalty (r11_emabias): penalize sustained per-env tracking offset that
    # per-step reward cannot see. bias_ema = a * bias_ema + (1-a) * err per axis.
    # Default k_bias=0 disables; r11_emabias overrides to nonzero.
    k_bias: float = 0.0
    bias_ema_alpha: float = 0.99  # effective window ~100 steps = 2 s at 50 Hz
    # Per-axis weights for bias penalty so roll (weak authority) gets stronger bias signal.
    bias_weights: tuple[float, float, float] = (1.5, 1.0, 1.0)
    # Extra experiment terms appended cfg-side (registry pattern; see RewardTermCfg).
    extra_terms: list[RewardTermCfg] = []


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
    """r_s = mean(da^2) + mean(d2a^2). First + second order action difference.

    Reads the COMMANDED action triple (_cmd_actions/_prev_cmd_actions/
    _prev_prev_cmd_actions), not the delayed/applied triple (_actions/...):
    the actor cannot observe control-action latency, so its smoothness penalty
    must be computed on what it actually output, not on what DelayBuffer
    clamps/repeats during reset-transient warmup. Off (control_delay_steps=(0,0))
    -> both triples are identical every step, so this is byte-identical to the
    pre-latency-DR reward.
    """
    da = env._cmd_actions - env._prev_cmd_actions
    d2a = env._cmd_actions - 2.0 * env._prev_cmd_actions + env._prev_prev_cmd_actions
    return da.pow(2).mean(dim=-1) + d2a.pow(2).mean(dim=-1)


def bias_ema_penalty(env: ALBCEnv) -> torch.Tensor:
    """r_bias = sum_i w_i * bias_ema_i^2. Sustained-offset penalty.

    Uses env._bias_ema (3D, ungated EMA of [roll, pitch, yaw_rate] tracking errors)
    updated each step. Squared form so reward gradient grows with offset; per-axis
    weights let roll (weak TAM authority) receive a stronger anti-bias signal than yaw.
    """
    w = env._reward_manager._bias_w
    return (env._bias_ema.pow(2) * w).sum(dim=-1)


# --- Reward Manager ---


class RewardManager:
    """Computes the tracking reward (builtin registry + cfg extras) with dt-scaling.

    Builtin terms live in _BUILTIN_TERMS below; experiments append extra terms
    via ALBCRewardCfg.extra_terms (mirrors the ALBCConstraintCfg.terms registry)
    so a new reward term needs no edit to this class.
    """

    # (name, weight getter, value fn(robot, env)) -- one row per builtin term.
    _BUILTIN_TERMS: tuple[tuple[str, Callable, Callable], ...] = (
        ("att_rp", lambda c: c.att_rp.k, lambda robot, env: att_rp_tracking(env)),
        ("yaw_vel", lambda c: c.yaw_vel.k, lambda robot, env: yaw_vel_tracking(env)),
        ("torque", lambda c: c.k_tau, joint_torque),
        ("thruster", lambda c: c.k_thr, lambda robot, env: thruster_energy(env)),
        ("smoothness", lambda c: c.k_s, lambda robot, env: action_smoothness(env)),
        ("bias", lambda c: c.k_bias, lambda robot, env: bias_ema_penalty(env)),
    )

    def __init__(self, cfg: ALBCRewardCfg, num_envs: int, device: str) -> None:
        self._cfg = cfg
        self._buf = torch.zeros(num_envs, dtype=torch.float32, device=device)
        self._extra_terms = [(t.name or t.func.__name__, t) for t in cfg.extra_terms]
        self._names = [n for n, _, _ in self._BUILTIN_TERMS] + [n for n, _ in self._extra_terms]
        self._episode_sums = {n: torch.zeros(num_envs, dtype=torch.float32, device=device) for n in self._names}
        # Preallocated per-axis bias weights (used by bias_ema_penalty each step).
        self._bias_w = torch.tensor(cfg.bias_weights, dtype=torch.float32, device=device)

    def compute(self, robot: Articulation, dt: float, env: ALBCEnv, **_ctx: Any) -> torch.Tensor:
        """Compute total reward (dt-scaled)."""
        cfg = self._cfg
        self._buf.zero_()

        for name, weight_of, func in self._BUILTIN_TERMS:
            scaled = func(robot, env) * weight_of(cfg) * dt
            self._buf += scaled
            self._episode_sums[name] += scaled
        for name, term in self._extra_terms:
            scaled = term.func(robot, env, **term.params) * term.weight * dt
            self._buf += scaled
            self._episode_sums[name] += scaled

        return self._buf

    def reset(self, env_ids: torch.Tensor) -> dict[str, float]:
        """Reset episode sums, return means before reset."""
        sums = {n: self._episode_sums[n][env_ids].mean().item() for n in self._names}
        for n in self._names:
            self._episode_sums[n][env_ids] = 0.0
        return sums
