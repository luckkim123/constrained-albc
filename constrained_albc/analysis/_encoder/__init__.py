# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Encoder inspection & training tools for constrained_full_albc (pure Python).

Subcommands:
    debug   --checkpoint        encoder weight/gradient/forward-pass debug
    sweep   --checkpoint        per-dimension z sensitivity sweep (analysis-quality required)
    train   --data --output     offline encoder training (value-prediction bottleneck)

Usage:
    python3 scripts/analysis/encoder_tools.py debug --run 0
    python3 scripts/analysis/encoder_tools.py sweep --checkpoint logs/.../model_4999.pt
    python3 scripts/analysis/encoder_tools.py train --data rollouts.pt --output enc.pt

The CLI is invoked through the encoder_tools.py shim, which puts the analysis
directory on sys.path (so `from common import ...` resolves) before calling main().
"""

from __future__ import annotations

import argparse

import torch

from .debug import cmd_debug
from .sweep import cmd_sweep
from .train import cmd_train


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Encoder inspection & training tools for constrained_full_albc."
    )
    subparsers = parser.add_subparsers(dest="mode", required=True)

    # --- debug ---
    p_debug = subparsers.add_parser(
        "debug",
        help="Encoder weight/gradient/forward-pass debug.",
    )
    group = p_debug.add_mutually_exclusive_group(required=True)
    group.add_argument("--checkpoint", type=str, help="Path to checkpoint .pt file")
    group.add_argument("--run", type=str, help="Run path, index (0=latest), or substring match")
    p_debug.add_argument(
        "--baseline", type=str, default=None,
        help="Optional baseline checkpoint for comparison",
    )
    p_debug.add_argument(
        "--model", type=str, default="model_latest.pt",
        help="Model filename when using --run",
    )
    p_debug.set_defaults(func=cmd_debug)

    # --- sweep ---
    p_sweep = subparsers.add_parser(
        "sweep",
        help="Per-dimension z sensitivity sweep (analysis-quality required).",
    )
    p_sweep.add_argument(
        "--checkpoint", type=str, required=True,
        help="Path to encoder checkpoint (.pt file)",
    )
    p_sweep.add_argument(
        "--num_points", type=int, default=100,
        help="Number of sweep points per parameter (default: 100)",
    )
    p_sweep.add_argument(
        "--output_dir", type=str, default=None,
        help="Output directory (default: <checkpoint_dir>/encoder_analysis)",
    )
    p_sweep.set_defaults(func=cmd_sweep)

    # --- train ---
    p_train = subparsers.add_parser(
        "train",
        help="Offline encoder training (value-prediction bottleneck).",
    )
    p_train.add_argument("--data", type=str, required=True, help="Path to collected rollout data (.pt)")
    p_train.add_argument("--output", type=str, required=True, help="Output encoder checkpoint path (.pt)")
    p_train.add_argument("--epochs", type=int, default=500, help="Number of training epochs.")
    p_train.add_argument("--batch_size", type=int, default=4096, help="Batch size.")
    p_train.add_argument("--lr", type=float, default=3e-4, help="Learning rate.")
    p_train.add_argument(
        "--device", type=str,
        default="cuda" if torch.cuda.is_available() else "cpu",
        help="Compute device (default: cuda if available, else cpu)",
    )
    p_train.set_defaults(func=cmd_train)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)
