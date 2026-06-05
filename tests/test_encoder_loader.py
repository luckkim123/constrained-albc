# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the consolidated encoder loader in _encoder/_shared.py.

Pins the LayerNorm-detection fix: a checkpoint carrying
_encoder_output_norm.weight must load WITH the LayerNorm layer present.
Pattern: synthetic state_dict, no GPU.
"""

from __future__ import annotations

import os
import sys

import torch
import torch.nn as nn

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from _encoder._shared import build_encoder_mlp, load_encoder_from_state_dict  # noqa: E402


def _make_state_dict(hidden, latent, in_dim, with_ln):
    """Build a state_dict matching build_encoder_mlp's layer indexing."""
    mlp = build_encoder_mlp(hidden, latent, in_dim, "softsign", output_norm=with_ln)
    sd = {f"encoder.{k}": v for k, v in mlp.state_dict().items()}
    if with_ln:
        # Mirror how training saves LN separately as _encoder_output_norm.*
        ln_idx = len(hidden) * 2 + 1
        sd["_encoder_output_norm.weight"] = sd.pop(f"encoder.{ln_idx}.weight")
        sd["_encoder_output_norm.bias"] = sd.pop(f"encoder.{ln_idx}.bias")
    return sd


def test_loader_detects_layernorm_checkpoint():
    hidden, latent, in_dim = [16, 8], 4, 23
    sd = _make_state_dict(hidden, latent, in_dim, with_ln=True)

    class _Arch:
        hidden_dims = hidden
        latent_dim = latent
        input_dim = in_dim
        output_activation = "softsign"

    enc = load_encoder_from_state_dict(sd, _Arch())
    # LayerNorm must be present in the reconstructed module
    assert any(isinstance(m, nn.LayerNorm) for m in enc.modules())


def test_loader_handles_no_layernorm_checkpoint():
    hidden, latent, in_dim = [16, 8], 4, 23
    sd = _make_state_dict(hidden, latent, in_dim, with_ln=False)

    class _Arch:
        hidden_dims = hidden
        latent_dim = latent
        input_dim = in_dim
        output_activation = "softsign"

    enc = load_encoder_from_state_dict(sd, _Arch())
    assert not any(isinstance(m, nn.LayerNorm) for m in enc.modules())
