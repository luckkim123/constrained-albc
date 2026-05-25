# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Consolidated logging utilities for constrained ALBC.

Provides all TB/WandB metric functions:
    - flush_metrics: Core logging utilities
    - log_dr_metrics: Domain randomization parameters
    - log_encoder_metrics: Encoder z health
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

import torch

if TYPE_CHECKING:
    from ..albc_env import ALBCEnv

logger = logging.getLogger(__name__)


# =============================================================================
# Core Logging Utilities
# =============================================================================


def flush_metrics(
    writer: Any,
    metrics: dict[str, float],
    step: int,
    logger_type: str = "tensorboard",
    wandb_extras: dict[str, Any] | None = None,
) -> None:
    """Flush accumulated metrics dict to TensorBoard and/or WandB in a single call.

    Scalars are always written via ``writer.add_scalar()`` so that TensorBoard
    records are never skipped -- even when the logger backend is WandB (RSL-RL's
    ``WandbSummaryWriter.add_scalar`` writes to both TB and WandB).

    Non-scalar WandB data (histograms, images, etc.) can be passed via
    *wandb_extras* and will be sent in a single ``wandb.log()`` call together
    with scalars.

    Args:
        writer: TensorBoard SummaryWriter (or RSL-RL WandbSummaryWriter).
        metrics: Dict of {tag: scalar_value} to log.
        step: Training step for x-axis.
        logger_type: Backend type ("tensorboard" or "wandb").
        wandb_extras: Optional dict of non-scalar WandB objects (e.g. Histogram).
            Ignored when logger_type is not "wandb".
    """
    if not metrics and not wandb_extras:
        return

    # Always record scalars via writer.add_scalar (works for both TB and WandB writers)
    for tag, value in metrics.items():
        writer.add_scalar(tag, value, step)

    # Send non-scalar extras (histograms, etc.) directly to WandB
    if logger_type == "wandb" and wandb_extras:
        wandb = _get_wandb()
        if wandb is not None:
            wandb.log(wandb_extras, step=step, commit=False)


def _get_wandb() -> Any | None:
    """Import wandb or return None if unavailable."""
    try:
        import wandb

        return wandb
    except ImportError:
        return None


# =============================================================================
# Domain Randomization Metrics (5 essential metrics)
# =============================================================================


def log_dr_metrics(
    extras: dict,
    env: ALBCEnv,
) -> None:
    """Log essential domain randomization parameter statistics.

    Metrics kept (5):
        - DR/buoyancy_force_mean: critical for ALBC torque capacity
        - DR/inertia_roll_mean, DR/inertia_pitch_mean: per-axis rotational dynamics
        - DR/payload_mass_mean: when payload enabled
        - DR/ocean_current_mag_mean: when ocean current enabled

    Args:
        extras: Environment extras dictionary (must have "log" key).
        env: ALBCEnv instance with _hydro, _buoy_hydro, etc.
    """
    log = extras["log"]

    with torch.no_grad():
        hydro = env._hydro
        log["DR/buoyancy_force_mean"] = hydro.buoyancy_force.mean().item()
        inertia = hydro.rigid_body_inertia  # (num_envs, 3) = Ixx, Iyy, Izz
        log["DR/inertia_roll_mean"] = inertia[:, 0].mean().item()
        log["DR/inertia_pitch_mean"] = inertia[:, 1].mean().item()

        # Payload (if enabled)
        if env._payload_mass is not None:
            log["DR/payload_mass_mean"] = env._payload_mass.mean().item()

        # Ocean current (always present as the shared OceanCurrent component)
        current_mag = torch.linalg.norm(hydro.current.velocity_w[:, :3], dim=-1)
        log["DR/ocean_current_mag_mean"] = current_mag.mean().item()


# =============================================================================
# Encoder Metrics (4 z-latent health metrics)
# =============================================================================


def log_encoder_metrics(
    writer: Any,
    policy: Any,
    env: Any,
    iteration: int,
    device: str | torch.device,
    logger_type: str = "tensorboard",
) -> None:
    """Log encoder z-latent health metrics (z_mean, z_std, z_min, z_max)."""
    if not hasattr(policy, "encoder"):
        return

    metrics: dict[str, float] = {}
    with torch.no_grad():
        obs = env.get_observations().to(device)
        z = policy._encode(obs)

        metrics["Encoder/z_mean"] = z.mean().item()
        metrics["Encoder/z_std"] = z.std().item()
        metrics["Encoder/z_min"] = z.min().item()
        metrics["Encoder/z_max"] = z.max().item()

    flush_metrics(writer, metrics, iteration, logger_type)
