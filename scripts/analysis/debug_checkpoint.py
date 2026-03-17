# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Debug encoder checkpoint: weight statistics, forward pass, gradient flow.

Loads one or two checkpoints and compares encoder weights, runs a forward pass
through the encoder MLP, and checks optimizer state for encoder parameters.

Architecture and activation are inferred from checkpoint (no hardcoded constants).

Usage:
    python scripts/analysis/debug_checkpoint.py --checkpoint <path_to_model.pt>

    # Compare two checkpoints (e.g., init vs trained)
    python scripts/analysis/debug_checkpoint.py \
        --checkpoint <path_to_model_1100.pt> \
        --baseline <path_to_model_0.pt>

    # Use run index (0=latest)
    python scripts/analysis/debug_checkpoint.py --run 0
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
import torch.nn as nn

from common import get_encoder_architecture_from_checkpoint, resolve_run_path


# ---------------------------------------------------------------------------
# Encoder reconstruction (same as encoder_z_sweep.py, self-contained here)
# ---------------------------------------------------------------------------


def build_encoder_mlp(
    hidden_dims: list[int],
    latent_dim: int,
    input_dim: int,
    output_activation: str = "tanh",
) -> nn.Sequential:
    """Reconstruct the encoder MLP from architecture parameters."""
    layers: list[nn.Module] = []
    prev_dim = input_dim
    for dim in hidden_dims:
        layers.append(nn.Linear(prev_dim, dim))
        layers.append(nn.ELU())
        prev_dim = dim
    layers.append(nn.Linear(prev_dim, latent_dim))
    if output_activation == "tanh":
        layers.append(nn.Tanh())
    return nn.Sequential(*layers)


def load_encoder_from_ckpt(ckpt_data: dict, arch) -> nn.Sequential:
    """Build and load encoder MLP from checkpoint state dict."""
    sd = ckpt_data["model_state_dict"]
    encoder_state = {
        k.removeprefix("encoder."): v
        for k, v in sd.items()
        if k.startswith("encoder.")
    }
    encoder = build_encoder_mlp(
        arch.hidden_dims, arch.latent_dim, arch.input_dim, arch.output_activation,
    )
    encoder.load_state_dict(encoder_state)
    encoder.eval()
    return encoder


# ---------------------------------------------------------------------------
# Analysis routines
# ---------------------------------------------------------------------------


def print_weight_stats(ckpt_data: dict, key_filter: str = "") -> None:
    """Print weight statistics for all matching keys."""
    sd = ckpt_data["model_state_dict"]
    keys = sorted(k for k in sd if key_filter in k)
    for key in keys:
        t = sd[key]
        if t.dim() == 0:
            print(f"  {key}: {t.item():.6f}")
        else:
            print(
                f"  {key}: mean={t.mean().item():.6f} std={t.std().item():.6f} "
                f"min={t.min().item():.6f} max={t.max().item():.6f} shape={list(t.shape)}"
            )


def compare_weights(label_a: str, ckpt_a: dict, label_b: str, ckpt_b: dict) -> None:
    """Compare weights between two checkpoints."""
    sd_a = ckpt_a["model_state_dict"]
    sd_b = ckpt_b["model_state_dict"]
    common_keys = sorted(set(sd_a.keys()) & set(sd_b.keys()))

    print(f"\n{'=' * 70}")
    print(f"WEIGHT COMPARISON: {label_a} vs {label_b}")
    print(f"{'=' * 70}")

    changed = []
    for key in common_keys:
        a, b = sd_a[key], sd_b[key]
        if a.shape != b.shape:
            print(f"  SHAPE MISMATCH: {key}: {list(a.shape)} vs {list(b.shape)}")
            continue
        diff = (a - b).abs().max().item()
        if diff > 1e-7:
            changed.append((key, diff))

    if not changed:
        print("  ALL weights are IDENTICAL!")
    else:
        print(f"  {len(changed)} / {len(common_keys)} weights changed:")
        for key, diff in changed:
            print(f"    {key}: max_diff={diff:.8f}")


def forward_pass_test(
    encoder: nn.Sequential, arch, label: str,
    norm_mean: torch.Tensor | None = None,
    norm_std: torch.Tensor | None = None,
) -> None:
    """Run encoder forward pass with random input and print z statistics."""
    torch.manual_seed(42)
    batch_size = 32
    test_input = torch.randn(batch_size, arch.input_dim) * 0.1

    with torch.no_grad():
        if norm_mean is not None and norm_std is not None:
            normed = ((test_input - norm_mean) / (norm_std + 1e-8)).clamp(-5.0, 5.0)
        else:
            normed = test_input
        z = encoder(normed)

    z_range = f"[-1, 1]" if arch.output_activation == "tanh" else "unbounded"
    saturated = (z.abs() > 0.99).float().mean().item() * 100 if arch.output_activation == "tanh" else 0.0

    print(f"\n  [{label}] Forward pass (batch={batch_size}, input_dim={arch.input_dim}):")
    print(f"    z shape: {list(z.shape)}, expected range: {z_range}")
    print(f"    z mean={z.mean().item():.6f} std={z.std().item():.6f}")
    print(f"    z min={z.min().item():.6f}  max={z.max().item():.6f}")

    if arch.output_activation == "tanh":
        print(f"    saturation (|z|>0.99): {saturated:.1f}%")

    # Per-dimension stats
    print(f"    Per-dim ranges:")
    for j in range(arch.latent_dim):
        zj = z[:, j]
        print(
            f"      z_{j:2d}: mean={zj.mean().item():+.4f} "
            f"std={zj.std().item():.4f} "
            f"[{zj.min().item():+.4f}, {zj.max().item():+.4f}]"
        )


def check_optimizer_state(ckpt_data: dict) -> None:
    """Check optimizer state for encoder parameter updates."""
    print(f"\n{'=' * 70}")
    print("OPTIMIZER STATE")
    print(f"{'=' * 70}")

    if "optimizer_state_dict" not in ckpt_data:
        print("  No optimizer_state_dict in checkpoint.")
        return

    opt = ckpt_data["optimizer_state_dict"]
    param_groups = opt.get("param_groups", [])
    print(f"  Param groups: {len(param_groups)}")
    for i, pg in enumerate(param_groups):
        lr = pg.get("lr", "?")
        wd = pg.get("weight_decay", "?")
        n_params = len(pg.get("params", []))
        print(f"    Group {i}: lr={lr}, weight_decay={wd}, #params={n_params}")

    state = opt.get("state", {})

    # Optimizer state is keyed by param index (position among Parameters only,
    # excluding buffers like normalizer stats). Find encoder params by matching
    # param_group integer IDs against learnable parameter names.
    sd = ckpt_data["model_state_dict"]
    param_keys = [k for k in sd if k.endswith((".weight", ".bias", "log_std", "std"))]
    encoder_param_keys = [(j, k) for j, k in enumerate(param_keys) if "encoder" in k]

    # Also check via param_groups for which group encoder params belong to
    for i, pg in enumerate(param_groups):
        pg_ids = pg.get("params", [])
        enc_in_group = [pid for pid in pg_ids if pid < len(param_keys) and "encoder" in param_keys[pid]]
        if enc_in_group:
            print(f"\n  Encoder params in group {i} (lr={pg.get('lr')}): {len(enc_in_group)} params")

    if encoder_param_keys:
        idx, key_name = encoder_param_keys[0]
        if idx in state:
            s = state[idx]
            print(f"\n  Encoder param[{idx}] ({key_name}):")
            print(f"    optimizer state keys: {list(s.keys())}")
            if "exp_avg" in s:
                ea = s["exp_avg"]
                print(f"    exp_avg: |mean|={ea.abs().mean().item():.8f} max={ea.abs().max().item():.8f}")
            if "exp_avg_sq" in s:
                eas = s["exp_avg_sq"]
                print(f"    exp_avg_sq: mean={eas.mean().item():.8f} max={eas.max().item():.8f}")
            if "step" in s:
                print(f"    step: {s['step']}")
        else:
            print(f"\n  WARNING: Encoder param[{idx}] ({key_name}) NOT in optimizer state!")
            print(f"  Available state keys (first 20): {sorted(state.keys())[:20]}")
    else:
        print("  No encoder parameters found in model state dict.")


def check_normalizer(ckpt_data: dict) -> None:
    """Check encoder observation normalizer statistics."""
    sd = ckpt_data["model_state_dict"]
    mean_key = "encoder_obs_normalizer._mean"
    std_key = "encoder_obs_normalizer._std"
    count_key = "encoder_obs_normalizer._count"

    print(f"\n{'=' * 70}")
    print("ENCODER OBS NORMALIZER")
    print(f"{'=' * 70}")

    if mean_key not in sd:
        print("  No encoder_obs_normalizer found in checkpoint.")
        return

    mean = sd[mean_key].squeeze()
    std = sd[std_key].squeeze()
    count = sd.get(count_key, torch.tensor(-1))

    print(f"  count: {count.item()}")
    print(f"  mean ({mean.shape[0]}D): {mean.numpy()}")
    print(f"  std  ({std.shape[0]}D): {std.numpy()}")

    # Flag dimensions with near-zero std (could cause div-by-zero)
    low_std = (std < 1e-4).nonzero(as_tuple=True)[0].tolist()
    if low_std:
        print(f"  WARNING: Near-zero std at dims: {low_std}")


def check_gradient_flow(encoder: nn.Sequential, arch) -> None:
    """Check gradient flow through encoder."""
    print(f"\n{'=' * 70}")
    print("GRADIENT FLOW TEST")
    print(f"{'=' * 70}")

    encoder.train()
    test_input = torch.randn(8, arch.input_dim, requires_grad=True)
    z = encoder(test_input)
    loss = z.sum()
    loss.backward()

    if test_input.grad is not None:
        print(f"  Input grad norm: {test_input.grad.norm().item():.6f}")
    else:
        print("  Input grad: None (no gradient)")
    for name, param in encoder.named_parameters():
        if param.grad is not None:
            print(f"  {name}: grad_norm={param.grad.norm().item():.6f}")
        else:
            print(f"  {name}: NO GRADIENT")
    encoder.eval()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Debug encoder checkpoint analysis")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--checkpoint", type=str, help="Path to checkpoint .pt file")
    group.add_argument("--run", type=str, help="Run path, index (0=latest), or substring match")
    parser.add_argument("--baseline", type=str, default=None, help="Optional baseline checkpoint for comparison")
    parser.add_argument("--model", type=str, default="model_latest.pt", help="Model filename when using --run")
    args = parser.parse_args()

    # Resolve checkpoint path
    if args.run is not None:
        run_path = resolve_run_path(args.run)
        ckpt_path = str(run_path / args.model)
        if not os.path.isfile(ckpt_path):
            # Fall back to any .pt file
            pt_files = sorted(Path(run_path).glob("model_*.pt"))
            if pt_files:
                ckpt_path = str(pt_files[-1])
            else:
                raise FileNotFoundError(f"No model files in {run_path}")
    else:
        ckpt_path = args.checkpoint

    if not os.path.isfile(ckpt_path):
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")

    # Infer architecture
    arch = get_encoder_architecture_from_checkpoint(ckpt_path)
    print(f"Checkpoint: {ckpt_path}")
    print(f"Architecture: input={arch.input_dim}D -> {arch.hidden_dims} -> {arch.latent_dim}D")
    print(f"Output activation: {arch.output_activation}")

    # Load checkpoint
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    encoder = load_encoder_from_ckpt(ckpt, arch)

    # Get normalizer tensors
    sd = ckpt["model_state_dict"]
    norm_mean = sd.get("encoder_obs_normalizer._mean", None)
    norm_std = sd.get("encoder_obs_normalizer._std", None)

    # --- Weight stats ---
    print(f"\n{'=' * 70}")
    print(f"ENCODER WEIGHT STATISTICS")
    print(f"{'=' * 70}")
    print_weight_stats(ckpt, "encoder.")

    # --- Normalizer ---
    check_normalizer(ckpt)

    # --- Forward pass ---
    print(f"\n{'=' * 70}")
    print("ENCODER FORWARD PASS")
    print(f"{'=' * 70}")
    forward_pass_test(encoder, arch, Path(ckpt_path).stem, norm_mean, norm_std)

    # --- Gradient flow ---
    check_gradient_flow(encoder, arch)

    # --- Optimizer state ---
    check_optimizer_state(ckpt)

    # --- Baseline comparison ---
    if args.baseline:
        if not os.path.isfile(args.baseline):
            print(f"\nWARNING: Baseline not found: {args.baseline}")
        else:
            baseline_ckpt = torch.load(args.baseline, map_location="cpu", weights_only=False)
            compare_weights(
                Path(args.baseline).stem, baseline_ckpt,
                Path(ckpt_path).stem, ckpt,
            )

            baseline_encoder = load_encoder_from_ckpt(baseline_ckpt, arch)
            forward_pass_test(baseline_encoder, arch, f"baseline ({Path(args.baseline).stem})")

    # --- All keys summary ---
    print(f"\n{'=' * 70}")
    print("ALL STATE DICT KEYS")
    print(f"{'=' * 70}")
    for key in sorted(sd.keys()):
        t = sd[key]
        if isinstance(t, torch.Tensor):
            print(f"  {key}: {list(t.shape)}")
        else:
            print(f"  {key}: {type(t).__name__}")

    print(f"\nAnalysis complete.")


if __name__ == "__main__":
    main()
