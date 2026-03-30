# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Encoder Latent Z Sensitivity Analysis.

Loads a trained encoder checkpoint and sweeps individual DR parameters
to verify that z responds continuously and meaningfully to physical parameter changes.

Supports:
    - Hero Agent 19D encoder (EmpiricalNormalization)
    - Constrained ALBC 23D/27D/28D encoder (EmpiricalNorm or static min-max)
    - Offline encoder checkpoints (enc_obs_lower/upper at top level)
    - Online encoder checkpoints (_enc_obs_lower/_enc_obs_upper in model_state_dict)

Architecture and sweep ranges are imported from hero_agent modules via common.py
-- no hardcoded constants.

Usage:
    python scripts/analysis/encoder_z_sweep.py --checkpoint <path_to_model.pt>
    python scripts/analysis/encoder_z_sweep.py --checkpoint <path> --num_points 200
"""

from __future__ import annotations

import argparse
import os
from dataclasses import dataclass

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import torch
import torch.nn as nn
from common import (
    SweepParam,
    build_nominal_obs,
    build_sweep_params,
    build_sweep_params_from_checkpoint,
    get_encoder_architecture_from_checkpoint,
)

# ---------------------------------------------------------------------------
# Encoder reconstruction (pure PyTorch, no Isaac Sim)
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
        latent_dim: Output dimension (e.g., 13).
        input_dim: Input dimension (e.g., 19).
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
# Normalization
# ---------------------------------------------------------------------------


@dataclass
class NormMode:
    """Normalization mode for the encoder."""

    mode: str  # "empirical" or "static_minmax"
    mean: torch.Tensor  # (1, D) for empirical
    std: torch.Tensor  # (1, D) for empirical
    lower: torch.Tensor | None = None  # (D,) for static_minmax
    upper: torch.Tensor | None = None  # (D,) for static_minmax


def load_encoder(
    ckpt_path: str,
) -> tuple[nn.Sequential, NormMode, int]:
    """Load encoder MLP and normalizer from checkpoint.

    Architecture is inferred from checkpoint weight shapes.
    Detects static min-max normalization (constrained ALBC 23D) vs
    EmpiricalNormalization (hero_agent) from checkpoint keys.

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
        norm = NormMode(
            mode="static_minmax",
            mean=torch.zeros(1, arch.input_dim),
            std=torch.ones(1, arch.input_dim),
            lower=lower.float(),
            upper=upper.float(),
        )
    else:
        norm = NormMode(
            mode="empirical",
            mean=state_dict.get(
                "encoder_obs_normalizer._mean", torch.zeros(1, arch.input_dim),
            ),
            std=state_dict.get(
                "encoder_obs_normalizer._std", torch.ones(1, arch.input_dim),
            ),
        )

    return encoder, norm, arch.latent_dim


def normalize_obs(x: torch.Tensor, norm: NormMode) -> torch.Tensor:
    """Apply normalization based on mode."""
    if norm.mode == "static_minmax":
        assert norm.lower is not None and norm.upper is not None
        return (2.0 * x - norm.upper - norm.lower) / (norm.upper - norm.lower)
    return ((x - norm.mean) / (norm.std + 1e-8)).clamp(-5.0, 5.0)


# ---------------------------------------------------------------------------
# Sweep logic
# ---------------------------------------------------------------------------


def sweep_parameter(
    encoder: nn.Sequential,
    norm: NormMode,
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
        normed = normalize_obs(batch, norm)
        z = encoder(normed)  # activation is built into MLP

    return values.numpy(), z.detach().numpy()


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_per_parameter(
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


def plot_sensitivity_heatmap(
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
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(description="Encoder z sensitivity sweep analysis")
    parser.add_argument(
        "--checkpoint", type=str, required=True,
        help="Path to encoder checkpoint (.pt file)",
    )
    parser.add_argument(
        "--num_points", type=int, default=100,
        help="Number of sweep points per parameter (default: 100)",
    )
    parser.add_argument(
        "--output_dir", type=str, default=None,
        help="Output directory (default: <checkpoint_dir>/encoder_analysis)",
    )
    args = parser.parse_args()

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
    encoder, norm, latent_dim = load_encoder(ckpt_path)

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

    # Get nominal obs and sweep params
    enc_lower_np = norm.lower.numpy() if norm.lower is not None else None
    enc_upper_np = norm.upper.numpy() if norm.upper is not None else None

    try:
        nominal_np = build_nominal_obs()
        sweep_params = build_sweep_params()
        if len(nominal_np) != ckpt_dim:
            print(f"[WARN] Config dim ({len(nominal_np)}) != checkpoint dim ({ckpt_dim}).")
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
    except RuntimeError:
        print("[INFO] Isaac Lab not available.")
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
        values, z = sweep_parameter(
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
    plot_per_parameter(all_results, nominal, output_dir, latent_dim, activation)

    print(f"Generating heatmap             -> {heatmap_path}")
    plot_sensitivity_heatmap(all_results, heatmap_path, latent_dim)

    print(f"\nDone! Output: {output_dir}")


if __name__ == "__main__":
    main()
