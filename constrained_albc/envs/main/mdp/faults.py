# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pure (Isaac-Sim-free) fault-injection helpers for the ALBC env.

A fault is an actuator / sensor FAILURE injected per-env at reset and held fixed for
the episode -- distinct from domain randomization (a physical-parameter spread). The
NUMERICAL core lives here as pure torch functions so it is unit-testable on plain torch
(no sim, no GPU): the env (albc_env.py) only decides WHEN to call them and WHERE to
write the resulting buffers.

Three faults (see FaultInjectionCfg):
    thruster health [N,6]  -- per-thruster, applied inside the marinelab ThrusterModel
    sensor noise    [N]    -- per-env extra obs-noise scale, applied in _get_observations
    joint health    [N]    -- per-env effort-limit scale, applied at reset

Toggle-off contract: every apply_* function returns its input UNCHANGED when the fault
buffer is None, so a fault-disabled env is byte-identical to the fault-free env.

ONE deliberate exception: ``apply_always_dead`` ignores ``cfg.enable`` entirely. Its
channels are structurally absent from the actuator set rather than failing, so they must
stay dead on the fault-disabled path too. Its toggle is its own empty tuple, not `enable`
-- do not "fix" it to respect the flag. See PLAN §4 item 10.
"""
from __future__ import annotations

import torch


def apply_always_dead(health: torch.Tensor, cfg) -> torch.Tensor:
    """Force ``cfg.thruster_always_dead`` channels to health exactly 0.0, IN PLACE.

    These are firmware ESC channels that are STRUCTURALLY ABSENT from the policy's
    actuator set -- not a fault. So this applies in EVERY env, on every path
    (fixed-health override, Bernoulli sampler, and the fault-disabled baseline), and
    it does NOT consult ``cfg.enable``: a policy must never see a pinned-dead channel
    alive. Retrain-simtoreal-2026-09 PLAN §4 item 10 / decision/159 결정 2 pins
    ``(0, 3)`` = m0, m3 (the vertical/heave pair, config.py ESC wiring comment).

    ``()`` (the default) is a no-op that touches nothing and draws no RNG, so a cfg
    leaving it empty is byte-identical to the pre-item-10 code. getattr-guarded like
    ``thruster_dead_frac`` / ``thruster_fixed_health`` so cfgs predating the field
    fall through unchanged.
    """
    always_dead = getattr(cfg, "thruster_always_dead", ())
    num_thrusters = health.shape[1]
    for i in always_dead:
        if not 0 <= i < num_thrusters:
            raise ValueError(
                f"thruster_always_dead index {i} out of range for num_thrusters={num_thrusters}"
            )
        health[:, i] = 0.0
    return health


def sample_thruster_health(
    num_envs: int,
    num_thrusters: int,
    cfg,
    device: str | torch.device,
    generator: torch.Generator | None = None,
    severity: torch.Tensor | None = None,
) -> torch.Tensor:
    """Sample per-env per-thruster health [N, num_thrusters].

    Each thruster independently fails with probability ``cfg.thruster_fail_prob``; a
    failed thruster is fully dead (health exactly 0.0) with probability
    ``cfg.thruster_dead_frac`` (default 0.0), else it keeps a residual health drawn
    uniformly from ``cfg.thruster_health_range``. Healthy thrusters stay at exactly 1.0.
    With ``thruster_dead_frac == 0`` no extra random draw happens, so the output is
    bit-identical to the pre-dead-atom sampler for the same generator state.

    Deterministic override: when ``cfg.thruster_fixed_health`` is set (a length-
    ``num_thrusters`` sequence in [0, 1]), that vector is returned for EVERY env and
    the Bernoulli sampling is skipped -- used to kill a specific thruster across all
    envs (FTC-m4 eval instrument). getattr-guarded so cfgs predating the field
    fall through to the Bernoulli path unchanged.

    ``severity``: optional per-env DORAEMON fault-severity scale [N] in [0, 1]
    (FaultDR-AB curriculum knob, see config.py fault_severity_range). When given,
    the effective fail probability is ``severity * cfg.thruster_fail_prob``
    (scaled BEFORE the Bernoulli compare) instead of the flat ``cfg.thruster_fail_prob``.
    ``severity=None`` (default) is byte-identical to the pre-curriculum behavior --
    every existing caller that does not pass it is unaffected. At severity=0 the
    fail probability is 0 for every thruster, so ``torch.where`` returns all ones
    regardless of ``cfg.thruster_fail_prob``.

    Finally ``apply_always_dead`` pins ``cfg.thruster_always_dead`` to 0.0 on BOTH
    paths (fixed and Bernoulli), last, so a structurally-absent channel outranks
    every sampled value. Empty tuple (default) = no-op, no extra RNG.
    """
    fixed = getattr(cfg, "thruster_fixed_health", None)
    if fixed is not None:
        if len(fixed) != num_thrusters:
            raise ValueError(
                f"thruster_fixed_health has {len(fixed)} entries, expected num_thrusters={num_thrusters}"
            )
        vec = torch.tensor(fixed, device=device, dtype=torch.float32)
        return apply_always_dead(vec.unsqueeze(0).expand(num_envs, num_thrusters).clone(), cfg)

    shape = (num_envs, num_thrusters)
    fail_prob = cfg.thruster_fail_prob if severity is None else severity.unsqueeze(-1) * cfg.thruster_fail_prob
    fail = torch.rand(shape, device=device, generator=generator) < fail_prob
    lo, hi = cfg.thruster_health_range
    residual = torch.rand(shape, device=device, generator=generator) * (hi - lo) + lo
    dead_frac = getattr(cfg, "thruster_dead_frac", 0.0)
    if dead_frac > 0.0:
        dead = torch.rand(shape, device=device, generator=generator) < dead_frac
        residual = torch.where(dead, torch.zeros_like(residual), residual)
    health = torch.where(fail, residual, torch.ones(shape, device=device))
    return apply_always_dead(health, cfg)


def sample_uniform_per_env(
    num_envs: int,
    range_tuple: tuple[float, float],
    device: str | torch.device,
    generator: torch.Generator | None = None,
) -> torch.Tensor:
    """Sample a per-env scalar [N] uniformly in ``range_tuple`` (sensor scale / joint health)."""
    lo, hi = range_tuple
    return torch.rand(num_envs, device=device, generator=generator) * (hi - lo) + lo


def apply_sensor_noise(
    obs: torch.Tensor,
    scale: torch.Tensor | None,
    base_std: torch.Tensor,
    noise: torch.Tensor | None = None,
) -> torch.Tensor:
    """Add per-env extra sensor noise on top of the always-on noise model.

    ``extra = scale[:, None] * noise * base_std`` where ``noise`` defaults to a fresh
    standard-normal sample (overridable for deterministic testing). The result is a NEW
    tensor (obs is never mutated in place).

    Returns ``obs`` UNCHANGED (the same object) when ``scale is None`` -- the toggle-off
    path: a fault-disabled env gets no extra noise and stays byte-identical.
    """
    if scale is None:
        return obs
    if noise is None:
        noise = torch.randn_like(obs)
    return obs + scale.unsqueeze(-1) * noise * base_std


def apply_joint_health(
    effort_limit: torch.Tensor,
    health: torch.Tensor | None,
) -> torch.Tensor:
    """Scale per-env joint effort limit by health [N] (broadcast over joints).

    ``effort_limit`` shape (N, num_joints); ``health`` shape (N,). Returns the
    UNCHANGED input when ``health is None`` (toggle-off byte-identical path).
    """
    if health is None:
        return effort_limit
    return effort_limit * health.unsqueeze(-1)
