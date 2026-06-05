# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Shared encoder reconstruction for the encoder_tools subcommands.

Superset builder used by both `debug` and `sweep`: supports the pre-softsign
LayerNorm and the softsign/tanh output activations used by ALBC.
"""

from __future__ import annotations

import torch
import torch.nn as nn


class _Softsign(nn.Module):
    """Softsign activation: x / (1 + |x|). Output in (-1, 1)."""

    def forward(self, x: torch.Tensor) -> torch.Tensor:
        return torch.nn.functional.softsign(x)


def build_encoder_mlp(
    hidden_dims: list[int],
    latent_dim: int,
    input_dim: int,
    output_activation: str = "tanh",
    output_norm: bool = False,
) -> nn.Sequential:
    """Reconstruct the encoder MLP from architecture parameters.

    Args:
        hidden_dims: List of hidden layer sizes (e.g., [256, 128, 64]).
        latent_dim: Output dimension (e.g., 9).
        input_dim: Input dimension (e.g., 23).
        output_activation: "tanh", "softsign", or "none".
        output_norm: If True, insert LayerNorm before the output activation.
    """
    layers: list[nn.Module] = []
    prev_dim = input_dim
    for dim in hidden_dims:
        layers.append(nn.Linear(prev_dim, dim))
        layers.append(nn.ELU())
        prev_dim = dim
    layers.append(nn.Linear(prev_dim, latent_dim))
    if output_norm:
        layers.append(nn.LayerNorm(latent_dim))
    if output_activation == "tanh":
        layers.append(nn.Tanh())
    elif output_activation == "softsign":
        layers.append(_Softsign())
    return nn.Sequential(*layers)


def load_encoder_from_state_dict(state_dict: dict, arch) -> nn.Sequential:
    """Reconstruct + load the encoder MLP from a checkpoint state_dict.

    Detects pre-softsign LayerNorm (saved separately as
    _encoder_output_norm.*) and injects it at the correct Sequential index.
    This is the single correct loader; debug.py and sweep.py both call it.

    Args:
        state_dict: Full model_state_dict from the checkpoint (not pre-filtered).
        arch: Object with hidden_dims, latent_dim, input_dim, output_activation.

    Returns:
        Encoder MLP in eval mode.
    """
    encoder_state = {
        k.removeprefix("encoder."): v
        for k, v in state_dict.items()
        if k.startswith("encoder.")
    }
    has_output_norm = "_encoder_output_norm.weight" in state_dict
    encoder = build_encoder_mlp(
        arch.hidden_dims,
        arch.latent_dim,
        arch.input_dim,
        arch.output_activation,
        output_norm=has_output_norm,
    )
    if has_output_norm:
        ln_idx = len(arch.hidden_dims) * 2 + 1
        encoder_state[f"{ln_idx}.weight"] = state_dict["_encoder_output_norm.weight"]
        encoder_state[f"{ln_idx}.bias"] = state_dict["_encoder_output_norm.bias"]
    encoder.load_state_dict(encoder_state)
    encoder.eval()
    return encoder
