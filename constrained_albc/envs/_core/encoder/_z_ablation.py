# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Pure z-ablation arithmetic, shared by ActorCriticEncoder._encode.

Kept separate from the network module so the toggle logic is unit-testable
without instantiating rsl_rl networks or building a TensorDict observation.
"""

from __future__ import annotations

import torch

_VALID_MODES = (None, "zero", "mean")


def validate_ablation_mode(mode: str | None) -> None:
    """Raise ValueError unless mode is one of None / "zero" / "mean"."""
    if mode not in _VALID_MODES:
        raise ValueError(
            f"z_ablation mode must be one of {_VALID_MODES}, got {mode!r}"
        )


def apply_z_ablation(
    z: torch.Tensor,
    mode: str | None,
    cached: torch.Tensor | None,
) -> torch.Tensor:
    """Return z, zeros, or the cached mean vector, per ablation mode.

    Args:
        z: encoder output (batch, latent_dim) -- the un-ablated latent.
        mode: None (passthrough) | "zero" | "mean".
        cached: (1, latent_dim) cached nominal z, required for "mean".

    Returns:
        Tensor of the same shape/dtype/device as z.
    """
    if mode is None:
        return z
    if mode == "zero":
        return torch.zeros_like(z)
    if mode == "mean":
        if cached is None:
            raise ValueError(
                "z_ablation 'mean' requires a cached nominal z (call "
                "set_z_ablation with nominal_obs first)"
            )
        return cached.to(dtype=z.dtype, device=z.device).expand_as(z)
    raise ValueError(f"unknown z_ablation mode {mode!r}")
