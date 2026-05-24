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
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
from common import (  # type: ignore[import-not-found]
    SweepParam,
    build_sweep_params_from_checkpoint,
    get_encoder_architecture_from_checkpoint,
    resolve_run_path,
)
from torch.utils.data import DataLoader, TensorDataset, random_split

# ---------------------------------------------------------------------------
# Shared encoder reconstruction (superset: supports output_norm + softsign)
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# debug subcommand helpers
# ---------------------------------------------------------------------------


def _load_encoder_from_ckpt(ckpt_data: dict, arch) -> nn.Sequential:
    """Build and load encoder MLP from checkpoint state dict (debug mode)."""
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


def _print_weight_stats(ckpt_data: dict, key_filter: str = "") -> None:
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


def _compare_weights(label_a: str, ckpt_a: dict, label_b: str, ckpt_b: dict) -> None:
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


def _forward_pass_test(
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

    z_range = "[-1, 1]" if arch.output_activation == "tanh" else "unbounded"
    saturated = (z.abs() > 0.99).float().mean().item() * 100 if arch.output_activation == "tanh" else 0.0

    print(f"\n  [{label}] Forward pass (batch={batch_size}, input_dim={arch.input_dim}):")
    print(f"    z shape: {list(z.shape)}, expected range: {z_range}")
    print(f"    z mean={z.mean().item():.6f} std={z.std().item():.6f}")
    print(f"    z min={z.min().item():.6f}  max={z.max().item():.6f}")

    if arch.output_activation == "tanh":
        print(f"    saturation (|z|>0.99): {saturated:.1f}%")

    # Per-dimension stats
    print("    Per-dim ranges:")
    for j in range(arch.latent_dim):
        zj = z[:, j]
        print(
            f"      z_{j:2d}: mean={zj.mean().item():+.4f} "
            f"std={zj.std().item():.4f} "
            f"[{zj.min().item():+.4f}, {zj.max().item():+.4f}]"
        )


def _check_optimizer_state(ckpt_data: dict) -> None:
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


def _check_normalizer(ckpt_data: dict) -> None:
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


def _check_gradient_flow(encoder: nn.Sequential, arch) -> None:
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
# sweep subcommand helpers
# ---------------------------------------------------------------------------


@dataclass
class _NormMode:
    """Normalization mode for the encoder."""

    mode: str  # "empirical" or "static_minmax"
    mean: torch.Tensor  # (1, D) for empirical
    std: torch.Tensor  # (1, D) for empirical
    lower: torch.Tensor | None = None  # (D,) for static_minmax
    upper: torch.Tensor | None = None  # (D,) for static_minmax


def _load_encoder_for_sweep(
    ckpt_path: str,
) -> tuple[nn.Sequential, _NormMode, int]:
    """Load encoder MLP and normalizer from checkpoint for z-sweep.

    Architecture is inferred from checkpoint weight shapes.
    Detects static min-max normalization (constrained_full_albc 23D) vs
    EmpiricalNormalization from checkpoint keys.

    Returns:
        encoder: The encoder MLP in eval mode.
        norm: Normalization mode with bounds or running stats.
        latent_dim: Encoder output dimension.
    """
    arch = get_encoder_architecture_from_checkpoint(ckpt_path)

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state_dict = ckpt["model_state_dict"]

    encoder_state = {
        k.removeprefix("encoder."): v
        for k, v in state_dict.items()
        if k.startswith("encoder.")
    }

    # Detect pre-softsign LayerNorm from checkpoint
    has_output_norm = "_encoder_output_norm.weight" in state_dict
    encoder = build_encoder_mlp(
        arch.hidden_dims, arch.latent_dim, arch.input_dim, arch.output_activation,
        output_norm=has_output_norm,
    )
    if has_output_norm:
        # LayerNorm sits after last Linear, before activation in the Sequential
        ln_idx = len(arch.hidden_dims) * 2 + 1
        encoder_state[f"{ln_idx}.weight"] = state_dict["_encoder_output_norm.weight"]
        encoder_state[f"{ln_idx}.bias"] = state_dict["_encoder_output_norm.bias"]
        print("[INFO] Detected pre-softsign LayerNorm in checkpoint.")
    encoder.load_state_dict(encoder_state)
    encoder.eval()

    # Detect normalization mode: static min-max or EmpiricalNorm
    # Static bounds can be in model_state_dict (online) or top-level (offline)
    lower_key = "_enc_obs_lower"
    upper_key = "_enc_obs_upper"
    lower = state_dict.get(lower_key, ckpt.get("enc_obs_lower"))
    upper = state_dict.get(upper_key, ckpt.get("enc_obs_upper"))

    if lower is not None and upper is not None:
        norm = _NormMode(
            mode="static_minmax",
            mean=torch.zeros(1, arch.input_dim),
            std=torch.ones(1, arch.input_dim),
            lower=lower.float(),
            upper=upper.float(),
        )
    else:
        norm = _NormMode(
            mode="empirical",
            mean=state_dict.get(
                "encoder_obs_normalizer._mean", torch.zeros(1, arch.input_dim),
            ),
            std=state_dict.get(
                "encoder_obs_normalizer._std", torch.ones(1, arch.input_dim),
            ),
        )

    return encoder, norm, arch.latent_dim


def _normalize_obs(x: torch.Tensor, norm: _NormMode) -> torch.Tensor:
    """Apply normalization based on mode."""
    if norm.mode == "static_minmax":
        assert norm.lower is not None and norm.upper is not None
        return (2.0 * x - norm.upper - norm.lower) / (norm.upper - norm.lower)
    return ((x - norm.mean) / (norm.std + 1e-8)).clamp(-5.0, 5.0)


def _sweep_parameter(
    encoder: nn.Sequential,
    norm: _NormMode,
    nominal: torch.Tensor,
    param: SweepParam,
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Sweep a single parameter and return (values, z_responses).

    Returns:
        values: (N,) sweep values as numpy array.
        z: (N, latent_dim) z responses as numpy array.
    """
    values = torch.linspace(param.low, param.high, num_points)
    batch = nominal.unsqueeze(0).expand(num_points, -1).clone()
    batch[:, param.dim_idx] = values

    with torch.no_grad():
        normed = _normalize_obs(batch, norm)
        z = encoder(normed)  # activation is built into MLP

    return values.numpy(), z.detach().numpy()


def _plot_per_parameter(
    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]],
    nominal: torch.Tensor,
    output_dir: str,
    latent_dim: int,
    activation: str = "tanh",
) -> None:
    """Create one figure per parameter, with a subplot for each z dimension."""
    n_cols = 4
    n_rows = (latent_dim + n_cols - 1) // n_cols

    y_lo, y_hi = (-1.1, 1.1) if activation in ("tanh", "softsign") else (-0.1, 2.1)

    for param, values, z in all_results:
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows))
        axes_flat = np.array(axes).flatten()

        nom_val = nominal[param.dim_idx].item()
        unit_str = f" ({param.unit})" if param.unit else ""

        for j in range(latent_dim):
            ax = axes_flat[j]
            z_range = z[:, j].max() - z[:, j].min()

            ax.plot(values, z[:, j], color="C0", linewidth=1.5)
            ax.axvline(nom_val, color="red", linestyle="--", alpha=0.6, linewidth=1)
            ax.set_ylim(y_lo, y_hi)
            ax.set_title(f"z_{j}  (range={z_range:.3f})", fontsize=9, fontweight="bold")
            ax.grid(True, alpha=0.3)

            if j >= latent_dim - n_cols:
                ax.set_xlabel(f"{param.name}{unit_str}", fontsize=8)
            if j % n_cols == 0:
                ax.set_ylabel("z", fontsize=9)

        for j in range(latent_dim, len(axes_flat)):
            fig.delaxes(axes_flat[j])

        fig.suptitle(
            f"z response to {param.name}{unit_str}\n(red dashed = nominal)",
            fontsize=12, fontweight="bold",
        )
        fig.tight_layout()

        safe_name = param.name.lower().replace(" ", "_")
        fig.savefig(
            os.path.join(output_dir, f"sweep_{safe_name}.png"),
            dpi=150, bbox_inches="tight",
        )
        plt.close(fig)


def _plot_sensitivity_heatmap(
    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]],
    output_path: str,
    latent_dim: int,
) -> None:
    """Create a heatmap showing sensitivity magnitude per parameter per z dim."""
    n_params = len(all_results)
    sensitivity = np.zeros((n_params, latent_dim))

    param_names = []
    for i, (param, _values, z) in enumerate(all_results):
        param_names.append(param.name)
        for j in range(latent_dim):
            sensitivity[i, j] = z[:, j].max() - z[:, j].min()

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(sensitivity.T, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(n_params))
    ax.set_xticklabels(param_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(latent_dim))
    ax.set_yticklabels([f"z_{j}" for j in range(latent_dim)], fontsize=9)
    ax.set_xlabel("DR Parameter", fontsize=11)
    ax.set_ylabel("Latent Dimension", fontsize=11)
    ax.set_title(
        "Encoder Sensitivity Heatmap (z range over DR sweep)",
        fontsize=13, fontweight="bold",
    )

    for i in range(n_params):
        for j in range(latent_dim):
            val = sensitivity[i, j]
            color = "white" if val > sensitivity.max() * 0.6 else "black"
            ax.text(i, j, f"{val:.2f}", ha="center", va="center", fontsize=7, color=color)

    fig.colorbar(im, ax=ax, label="z range (max - min)", shrink=0.8)
    fig.tight_layout()
    fig.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# train subcommand helpers
# ---------------------------------------------------------------------------


class _OfflineEncoder(nn.Module):
    """Encoder + value head for offline training.

    Architecture matches ActorCriticEncoder._encode() exactly:
    - Static min-max normalization: (2*x - upper - lower) / (upper - lower) -> [-1, 1]
    - MLP: [256, 128, 64] with ELU activation
    - softsign output -> z in (-1, 1)

    Value head: Linear(policy_obs_dim + encoder_latent_dim, 1)
    """

    def __init__(
        self,
        privileged_dim: int = 23,
        policy_obs_dim: int = 14,
        encoder_hidden_dims: tuple[int, ...] = (256, 128, 64),
        encoder_latent_dim: int = 13,
        priv_obs_lower: torch.Tensor | None = None,
        priv_obs_upper: torch.Tensor | None = None,
    ):
        super().__init__()
        self.privileged_dim = privileged_dim
        self.policy_obs_dim = policy_obs_dim
        self.encoder_latent_dim = encoder_latent_dim

        # Static min-max normalization bounds
        if priv_obs_lower is not None and priv_obs_upper is not None:
            self.register_buffer("_enc_obs_lower", priv_obs_lower.float())
            self.register_buffer("_enc_obs_upper", priv_obs_upper.float())
        else:
            self.register_buffer("_enc_obs_lower", torch.zeros(privileged_dim))
            self.register_buffer("_enc_obs_upper", torch.ones(privileged_dim))

        # Encoder MLP (must match ActorCriticEncoder.encoder structure)
        layers: list[nn.Module] = []
        in_dim = privileged_dim
        for h_dim in encoder_hidden_dims:
            layers.append(nn.Linear(in_dim, h_dim))
            layers.append(nn.ELU())
            in_dim = h_dim
        layers.append(nn.Linear(in_dim, encoder_latent_dim))
        self.encoder = nn.Sequential(*layers)

        # Value prediction head (disposable -- only encoder weights are saved)
        self.value_head = nn.Linear(policy_obs_dim + encoder_latent_dim, 1)

    def _normalize_privileged(self, p_t: torch.Tensor) -> torch.Tensor:
        """Static min-max normalization to [-1, 1]."""
        upper: torch.Tensor = self._enc_obs_upper  # type: ignore[assignment]
        lower: torch.Tensor = self._enc_obs_lower  # type: ignore[assignment]
        return (2 * p_t - upper - lower) / (upper - lower + 1e-8)

    def encode(self, p_t: torch.Tensor) -> torch.Tensor:
        """Encode privileged info to z. Matches ActorCriticEncoder._encode()."""
        p_norm = self._normalize_privileged(p_t)
        return F.softsign(self.encoder(p_norm))

    def forward(
        self, p_t: torch.Tensor, o_t: torch.Tensor
    ) -> tuple[torch.Tensor, torch.Tensor]:
        """Forward pass: encode privileged, predict value.

        Args:
            p_t: Privileged observations (N, 23).
            o_t: Policy observations (N, 14).

        Returns:
            (V_hat, z): Value prediction (N, 1) and latent z (N, 13).
        """
        z = self.encode(p_t)
        v_hat = self.value_head(torch.cat([o_t, z], dim=-1))
        return v_hat, z


def _compute_empirical_bounds(
    data: torch.Tensor, margin: float = 0.1
) -> tuple[torch.Tensor, torch.Tensor]:
    """Compute min/max bounds with margin from data.

    Args:
        data: (N, D) tensor.
        margin: Fractional margin to add (0.1 = 10%).

    Returns:
        (lower, upper) bounds tensors of shape (D,).
    """
    data_min = data.min(dim=0).values
    data_max = data.max(dim=0).values
    data_range = data_max - data_min + 1e-8
    lower = data_min - margin * data_range
    upper = data_max + margin * data_range
    return lower, upper


def _run_train(
    data_path: str,
    output_path: str,
    epochs: int = 500,
    batch_size: int = 4096,
    lr: float = 3e-4,
    weight_decay: float = 1e-4,
    val_fraction: float = 0.1,
    device: str = "cuda" if torch.cuda.is_available() else "cpu",
) -> None:
    """Train offline encoder with value prediction bottleneck."""
    print(f"Loading data from {data_path}...")
    data = torch.load(data_path, weights_only=False)

    policy_obs = data["policy_obs"].float()
    privileged = data["privileged"].float()
    v_critic = data["V_critic"].float()

    n_samples = policy_obs.shape[0]
    print(f"  Samples: {n_samples}")
    print(f"  policy_obs: {policy_obs.shape}, privileged: {privileged.shape}")
    print(f"  V_critic range: [{v_critic.min():.3f}, {v_critic.max():.3f}]")

    # Compute empirical bounds for static normalization
    lower, upper = _compute_empirical_bounds(privileged)
    print(f"  Privileged bounds: lower={lower.tolist()}")
    print(f"  Privileged bounds: upper={upper.tolist()}")

    # Train/val split
    dataset = TensorDataset(policy_obs, privileged, v_critic)
    n_val = int(n_samples * val_fraction)
    n_train = n_samples - n_val
    train_ds, val_ds = random_split(dataset, [n_train, n_val])
    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True, drop_last=True)
    val_loader = DataLoader(val_ds, batch_size=batch_size, shuffle=False)

    print(f"  Train: {n_train}, Val: {n_val}")

    # Build model
    model = _OfflineEncoder(
        privileged_dim=privileged.shape[1],
        policy_obs_dim=policy_obs.shape[1],
        priv_obs_lower=lower,
        priv_obs_upper=upper,
    ).to(device)
    print(f"  Model params: {sum(p.numel() for p in model.parameters()):,}")

    optimizer = torch.optim.Adam(model.parameters(), lr=lr, weight_decay=weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=epochs)

    best_val_loss = float("inf")
    best_state = None

    for epoch in range(epochs):
        # Training
        model.train()
        train_loss_sum = 0.0
        train_count = 0
        for o_t_batch, p_t_batch, v_batch in train_loader:
            o_t_batch = o_t_batch.to(device)
            p_t_batch = p_t_batch.to(device)
            v_batch = v_batch.to(device)

            v_hat, z = model(p_t_batch, o_t_batch)
            loss = F.mse_loss(v_hat.squeeze(-1), v_batch)

            optimizer.zero_grad()
            loss.backward()
            optimizer.step()

            train_loss_sum += loss.item() * o_t_batch.shape[0]
            train_count += o_t_batch.shape[0]

        scheduler.step()
        train_loss = train_loss_sum / max(train_count, 1)

        # Validation
        model.eval()
        val_loss_sum = 0.0
        val_count = 0
        z_stats = {"mean": 0.0, "std": 0.0}
        with torch.no_grad():
            for o_t_batch, p_t_batch, v_batch in val_loader:
                o_t_batch = o_t_batch.to(device)
                p_t_batch = p_t_batch.to(device)
                v_batch = v_batch.to(device)

                v_hat, z = model(p_t_batch, o_t_batch)
                loss = F.mse_loss(v_hat.squeeze(-1), v_batch)
                val_loss_sum += loss.item() * o_t_batch.shape[0]
                val_count += o_t_batch.shape[0]

                z_stats["mean"] += z.mean().item() * o_t_batch.shape[0]
                z_stats["std"] += z.std(dim=0).mean().item() * o_t_batch.shape[0]

        val_loss = val_loss_sum / max(val_count, 1)
        z_stats["mean"] /= max(val_count, 1)
        z_stats["std"] /= max(val_count, 1)

        if val_loss < best_val_loss:
            best_val_loss = val_loss
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

        if epoch % 50 == 0 or epoch == epochs - 1:
            print(
                f"  Epoch {epoch:4d}/{epochs}: "
                f"train_loss={train_loss:.6f}, val_loss={val_loss:.6f}, "
                f"z_mean={z_stats['mean']:.3f}, z_std={z_stats['std']:.3f}, "
                f"lr={scheduler.get_last_lr()[0]:.2e}"
            )

    # Save best encoder weights
    if best_state is None:
        best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}

    # Extract only encoder weights (not value_head)
    encoder_state_dict = {
        k.replace("encoder.", ""): v
        for k, v in best_state.items()
        if k.startswith("encoder.")
    }

    output_dir = os.path.dirname(output_path)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    save_dict = {
        "encoder_state_dict": encoder_state_dict,
        "enc_obs_lower": lower,
        "enc_obs_upper": upper,
        "val_loss": best_val_loss,
        "metadata": {
            "data_path": data_path,
            "epochs": epochs,
            "n_train": n_train,
            "n_val": n_val,
            "encoder_hidden_dims": [256, 128, 64],
            "encoder_latent_dim": 13,
            "privileged_dim": privileged.shape[1],
            "policy_obs_dim": policy_obs.shape[1],
        },
    }
    torch.save(save_dict, output_path)
    print(f"\nSaved encoder to {output_path}")
    print(f"  Best val_loss: {best_val_loss:.6f}")
    print(f"  Encoder state_dict keys: {list(encoder_state_dict.keys())}")


# ---------------------------------------------------------------------------
# Subcommand entry points
# ---------------------------------------------------------------------------


def cmd_debug(args: argparse.Namespace) -> None:
    """Encoder weight/gradient/forward-pass debug."""
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
    encoder = _load_encoder_from_ckpt(ckpt, arch)

    # Get normalizer tensors
    sd = ckpt["model_state_dict"]
    norm_mean = sd.get("encoder_obs_normalizer._mean", None)
    norm_std = sd.get("encoder_obs_normalizer._std", None)

    # --- Weight stats ---
    print(f"\n{'=' * 70}")
    print("ENCODER WEIGHT STATISTICS")
    print(f"{'=' * 70}")
    _print_weight_stats(ckpt, "encoder.")

    # --- Normalizer ---
    _check_normalizer(ckpt)

    # --- Forward pass ---
    print(f"\n{'=' * 70}")
    print("ENCODER FORWARD PASS")
    print(f"{'=' * 70}")
    _forward_pass_test(encoder, arch, Path(ckpt_path).stem, norm_mean, norm_std)

    # --- Gradient flow ---
    _check_gradient_flow(encoder, arch)

    # --- Optimizer state ---
    _check_optimizer_state(ckpt)

    # --- Baseline comparison ---
    if args.baseline:
        if not os.path.isfile(args.baseline):
            print(f"\nWARNING: Baseline not found: {args.baseline}")
        else:
            baseline_ckpt = torch.load(args.baseline, map_location="cpu", weights_only=False)
            _compare_weights(
                Path(args.baseline).stem, baseline_ckpt,
                Path(ckpt_path).stem, ckpt,
            )

            baseline_encoder = _load_encoder_from_ckpt(baseline_ckpt, arch)
            _forward_pass_test(baseline_encoder, arch, f"baseline ({Path(args.baseline).stem})")

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

    print("\nAnalysis complete.")


def cmd_sweep(args: argparse.Namespace) -> None:
    """Per-dimension z sensitivity sweep."""
    ckpt_path = args.checkpoint
    if not os.path.isabs(ckpt_path):
        ckpt_path = os.path.join("/workspace/isaaclab", ckpt_path)

    # Prefer best_model.pt in same directory
    best_path = os.path.join(os.path.dirname(ckpt_path), "best_model.pt")
    if os.path.isfile(best_path) and not ckpt_path.endswith("best_model.pt"):
        print("[INFO] Found best_model.pt, using it instead.")
        ckpt_path = best_path

    output_dir = args.output_dir or os.path.join(os.path.dirname(ckpt_path), "encoder_analysis")
    os.makedirs(output_dir, exist_ok=True)

    # Load encoder (architecture inferred from checkpoint)
    print(f"Loading encoder from: {ckpt_path}")
    encoder, norm, latent_dim = _load_encoder_for_sweep(ckpt_path)

    # Get architecture info for activation type
    arch = get_encoder_architecture_from_checkpoint(ckpt_path)
    ckpt_dim = arch.input_dim
    activation = arch.output_activation
    if activation in ("tanh", "softsign"):
        z_range_str = f"[-1, 1] ({activation})"
    else:
        z_range_str = "unbounded (no output activation)"

    # Report normalization mode
    print(f"Normalization: {norm.mode}")
    if norm.mode == "static_minmax":
        assert norm.lower is not None and norm.upper is not None
        print(f"  lower[:5]: {norm.lower[:5].tolist()}")
        print(f"  upper[:5]: {norm.upper[:5].tolist()}")

    # Get nominal obs and sweep params from checkpoint normalizer bounds
    enc_lower_np = norm.lower.numpy() if norm.lower is not None else None
    enc_upper_np = norm.upper.numpy() if norm.upper is not None else None

    if norm.mode == "static_minmax":
        assert norm.lower is not None and norm.upper is not None
        nominal_np = ((norm.lower + norm.upper) / 2.0).numpy()
        print("  Using static bounds midpoint as nominal.")
    else:
        nominal_np = norm.mean.squeeze().numpy()
        print("  Using normalizer mean as nominal.")
    sweep_params = build_sweep_params_from_checkpoint(
        ckpt_dim, nominal_np, enc_lower_np, enc_upper_np,
    )

    nominal = torch.tensor(nominal_np, dtype=torch.float32)

    print(f"Checkpoint dim: {ckpt_dim}D, Latent dim: {latent_dim}D")
    print(f"z range: {z_range_str}")
    print(f"Sweeping {len(sweep_params)} parameters with {args.num_points} points each...\n")

    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]] = []
    for param in sweep_params:
        values, z = _sweep_parameter(
            encoder, norm, nominal, param, args.num_points,
        )

        z_ranges = z.max(axis=0) - z.min(axis=0)
        active_dims = np.sum(z_ranges > 0.05)
        print(
            f"  {param.name:25s} | "
            f"sweep [{param.low:.5f}, {param.high:.5f}] | "
            f"active z dims (range>0.05): {active_dims:2d}/{latent_dim} | "
            f"max z range: {z_ranges.max():.4f}"
        )
        all_results.append((param, values, z))

    # Generate plots
    heatmap_path = os.path.join(output_dir, "z_sensitivity_heatmap.png")

    print(f"\nGenerating per-parameter plots -> {output_dir}/sweep_*.png")
    _plot_per_parameter(all_results, nominal, output_dir, latent_dim, activation)

    print(f"Generating heatmap             -> {heatmap_path}")
    _plot_sensitivity_heatmap(all_results, heatmap_path, latent_dim)

    print(f"\nDone! Output: {output_dir}")


def cmd_train(args: argparse.Namespace) -> None:
    """Offline encoder training with value prediction bottleneck."""
    _run_train(
        data_path=args.data,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
    )


# ---------------------------------------------------------------------------
# Argument parsing
# ---------------------------------------------------------------------------


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


if __name__ == "__main__":
    main()
