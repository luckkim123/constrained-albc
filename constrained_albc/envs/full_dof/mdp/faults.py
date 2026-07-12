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

Three faults (see FaultInjectionCfg in main/config.py, where the full fault contract lives):
    thruster health [N,6]  -- per-thruster, applied inside the marinelab ThrusterModel
    sensor noise    [N]    -- per-env extra obs-noise scale, applied in _get_observations
    joint health    [N]    -- per-env effort-limit scale, applied at reset

Ported verbatim from main/mdp/faults.py for the DORAEMON obs-noise DR layer. In this
full_dof tree only apply_sensor_noise is currently wired up (albc_env.py); the other
functions are kept for parity with main.

Toggle-off contract: every apply_* function returns its input UNCHANGED when the fault
buffer is None, so a fault-disabled env is byte-identical to the fault-free env.
"""
from __future__ import annotations

import torch


def sample_thruster_health(
    num_envs: int,
    num_thrusters: int,
    cfg,
    device: str | torch.device,
    generator: torch.Generator | None = None,
) -> torch.Tensor:
    """Sample per-env per-thruster health [N, num_thrusters].

    Each thruster independently fails with probability ``cfg.thruster_fail_prob``; a
    failed thruster keeps a residual health drawn uniformly from
    ``cfg.thruster_health_range`` (0 = dead). Healthy thrusters stay at exactly 1.0.
    """
    shape = (num_envs, num_thrusters)
    fail = torch.rand(shape, device=device, generator=generator) < cfg.thruster_fail_prob
    lo, hi = cfg.thruster_health_range
    residual = torch.rand(shape, device=device, generator=generator) * (hi - lo) + lo
    return torch.where(fail, residual, torch.ones(shape, device=device))


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
