"""Encoder Latent Z Sensitivity Analysis.

Loads a trained Phase 1 encoder checkpoint and sweeps individual DR parameters
to verify that z responds continuously and meaningfully to physical parameter changes.

Usage:
    python scripts/analysis/encoder_z_sweep.py [--checkpoint PATH] [--num_points N]

No Isaac Sim dependency -- pure PyTorch analysis.
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

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LATEST_CHECKPOINT = (
    "logs/rsl_rl/hero_agent_albc_encoder/2026-02-28_23-24-28/model_4999.pt"
)

# Nominal privileged obs (20D) assembled from env.yaml hydro/buoy configs.
# These are the *unscaled* nominal values (DR scale = 1.0).
#
# 20D structure:
#   Main hydro (5D): volume, CoG_xyz, CoB_z
#   Buoy hydro (5D): volume, CoG_xyz, CoB_z
#   Main inertia (2D): Ixx, Iyy
#   Buoy inertia (2D): Ixx, Iyy
#   Payload (4D): mass, cog_offset_xyz
#   Added mass surge (2D): main, buoy
NOMINAL_20D = [
    # Main body hydro (5D): volume, CoG(3), CoB_z(1)
    0.00827,                    # [0]  main volume
    0.0, 0.0, -0.05,           # [1:4] main CoG xyz
    0.0,                        # [4]  main CoB z
    # Buoy body hydro (5D): volume, CoG(3), CoB_z(1)
    0.00268,                    # [5]  buoy volume
    0.0, 0.0, 0.0,             # [6:9] buoy CoG xyz
    0.0,                        # [9]  buoy CoB z
    # Main inertia (2D): Ixx, Iyy (no Izz)
    0.0994, 0.0994,            # [10:12] main inertia
    # Buoy inertia (2D): Ixx, Iyy (no Izz)
    0.00278, 0.00278,          # [12:14] buoy inertia
    # Payload (4D): mass, cog_offset xyz
    0.5,                        # [14] payload mass
    0.0, 0.0, -0.015,          # [15:18] payload cog offset
    # Added mass surge (2D): main, buoy
    5.76,                       # [18] main added mass surge
    1.5,                        # [19] buoy added mass surge
]


@dataclass
class SweepParam:
    """Definition of a single parameter to sweep."""

    name: str
    dim_idx: int
    low: float
    high: float
    unit: str = ""


# Key parameters to sweep: volume, inertia, payload, added mass
SWEEP_PARAMS = [
    SweepParam("Main Volume", 0, 0.00827 * 0.9, 0.00827 * 1.1, "m^3"),
    SweepParam("Buoy Volume", 5, 0.00268 * 0.9, 0.00268 * 1.1, "m^3"),
    SweepParam("Main CoG Z", 3, -0.05 - 0.02, -0.05 + 0.02, "m"),
    SweepParam("Main Inertia Ixx", 10, 0.0994 * 0.75, 0.0994 * 1.3, "kg*m^2"),
    SweepParam("Main Inertia Iyy", 11, 0.0994 * 0.75, 0.0994 * 1.3, "kg*m^2"),
    SweepParam("Buoy Inertia Ixx", 12, 0.00278 * 0.75, 0.00278 * 1.3, "kg*m^2"),
    SweepParam("Buoy Inertia Iyy", 13, 0.00278 * 0.75, 0.00278 * 1.3, "kg*m^2"),
    SweepParam("Payload Mass", 14, 0.0, 1.5, "kg"),
    SweepParam("Payload CoG Z", 17, -0.03, 0.0, "m"),
    SweepParam("Main Added Mass Surge", 18, 5.76 * 0.5, 5.76 * 1.5, "kg"),
    SweepParam("Buoy Added Mass Surge", 19, 1.5 * 0.5, 1.5 * 1.5, "kg"),
]

# Encoder architecture constants (from rsl_rl_ppo_cfg.py)
PRIVILEGED_DIM = 20
ENCODER_HIDDEN_DIMS = [256, 128, 64]
ENCODER_LATENT_DIM = 13


# ---------------------------------------------------------------------------
# Encoder reconstruction (no Isaac Sim dependency)
# ---------------------------------------------------------------------------


def build_encoder_mlp(activation: str = "tanh") -> nn.Sequential:
    """Reconstruct the encoder MLP: 20D -> [256,128,64] -> 13D.

    For tanh mode (default): last layer has tanh activation (built into MLP).
    For sigmoid mode: no last activation (sigmoid applied externally).

    Layer indices (tanh): 0(Linear) 1(ELU) 2(Linear) 3(ELU) 4(Linear) 5(ELU) 6(Linear) 7(Tanh)
    Layer indices (sigmoid): 0(Linear) 1(ELU) 2(Linear) 3(ELU) 4(Linear) 5(ELU) 6(Linear)
    """
    layers: list[nn.Module] = [
        nn.Linear(PRIVILEGED_DIM, ENCODER_HIDDEN_DIMS[0]),
        nn.ELU(),
        nn.Linear(ENCODER_HIDDEN_DIMS[0], ENCODER_HIDDEN_DIMS[1]),
        nn.ELU(),
        nn.Linear(ENCODER_HIDDEN_DIMS[1], ENCODER_HIDDEN_DIMS[2]),
        nn.ELU(),
        nn.Linear(ENCODER_HIDDEN_DIMS[2], ENCODER_LATENT_DIM),
    ]
    if activation == "tanh":
        layers.append(nn.Tanh())
    return nn.Sequential(*layers)


def activate_z(raw: torch.Tensor, activation: str = "tanh",
               z_min: float = 0.01, z_max: float = 2.0) -> torch.Tensor:
    """Apply output activation to raw encoder output."""
    if activation == "tanh":
        return torch.tanh(raw)
    return z_min + torch.sigmoid(raw) * (z_max - z_min)


def load_encoder(ckpt_path: str, activation: str = "tanh") -> tuple[nn.Sequential, torch.Tensor, torch.Tensor]:
    """Load encoder MLP and normalizer statistics from checkpoint.

    Returns:
        encoder: The encoder MLP in eval mode.
        norm_mean: (1, D) running mean from EmpiricalNormalization.
        norm_std: (1, D) running std from EmpiricalNormalization.
    """
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state_dict = ckpt["model_state_dict"]

    # Extract encoder weights
    encoder = build_encoder_mlp(activation)
    encoder_state = {
        k.removeprefix("encoder."): v
        for k, v in state_dict.items()
        if k.startswith("encoder.")
    }
    encoder.load_state_dict(encoder_state)
    encoder.eval()

    # Extract normalizer statistics (fallback to identity if absent)
    norm_mean = state_dict.get("encoder_obs_normalizer._mean", torch.zeros(1, PRIVILEGED_DIM))
    norm_std = state_dict.get("encoder_obs_normalizer._std", torch.ones(1, PRIVILEGED_DIM))

    if norm_mean.shape[-1] != PRIVILEGED_DIM:
        raise ValueError(
            f"Checkpoint privileged dim {norm_mean.shape[-1]} != expected {PRIVILEGED_DIM}. "
            "Use the correct checkpoint or update PRIVILEGED_DIM."
        )

    return encoder, norm_mean, norm_std


def normalize_obs(x: torch.Tensor, mean: torch.Tensor, std: torch.Tensor) -> torch.Tensor:
    """Apply EmpiricalNormalization: (x - mean) / (std + eps), clamped to [-5, 5]."""
    return ((x - mean) / (std + 1e-8)).clamp(-5.0, 5.0)


# ---------------------------------------------------------------------------
# Sweep logic
# ---------------------------------------------------------------------------


def sweep_parameter(
    encoder: nn.Sequential,
    norm_mean: torch.Tensor,
    norm_std: torch.Tensor,
    nominal: torch.Tensor,
    param: SweepParam,
    activation: str = "tanh",
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Sweep a single parameter and return (values, z_responses).

    Args:
        encoder: Loaded encoder MLP.
        norm_mean: Normalizer running mean.
        norm_std: Normalizer running std.
        nominal: (D,) nominal privileged observation.
        param: Which parameter to sweep.
        activation: "tanh" or "sigmoid".
        num_points: Number of sweep points.

    Returns:
        values: (N,) sweep values as numpy array.
        z: (N, 13) z responses as numpy array.
    """
    values = torch.linspace(param.low, param.high, num_points)
    batch = nominal.unsqueeze(0).expand(num_points, -1).clone()
    batch[:, param.dim_idx] = values

    with torch.no_grad():
        normed = normalize_obs(batch, norm_mean, norm_std)
        raw = encoder(normed)
        # For tanh mode, tanh is already in the MLP, so raw is already activated.
        # For sigmoid mode, we need to apply sigmoid externally.
        if activation == "sigmoid":
            z = activate_z(raw, activation)
        else:
            z = raw  # Already tanh'd

    return values.numpy(), z.numpy()


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_per_parameter(
    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]],
    nominal: torch.Tensor,
    output_dir: str,
    activation: str = "tanh",
    z_dim: int = ENCODER_LATENT_DIM,
) -> None:
    """Create one figure per parameter, with a subplot for each z dimension."""
    n_cols = 4
    n_rows = (z_dim + n_cols - 1) // n_cols  # 4 rows for 13 dims

    y_lo, y_hi = (-1.1, 1.1) if activation == "tanh" else (-0.1, 2.1)

    for param, values, z in all_results:
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(4 * n_cols, 3 * n_rows))
        axes_flat = np.array(axes).flatten()

        nom_val = nominal[param.dim_idx].item()
        unit_str = f" ({param.unit})" if param.unit else ""

        for j in range(z_dim):
            ax = axes_flat[j]
            z_range = z[:, j].max() - z[:, j].min()

            ax.plot(values, z[:, j], color="C0", linewidth=1.5)
            ax.axvline(nom_val, color="red", linestyle="--", alpha=0.6, linewidth=1)
            ax.set_ylim(y_lo, y_hi)
            ax.set_title(f"z_{j}  (range={z_range:.3f})", fontsize=9, fontweight="bold")
            ax.grid(True, alpha=0.3)

            if j >= z_dim - n_cols:
                ax.set_xlabel(f"{param.name}{unit_str}", fontsize=8)
            if j % n_cols == 0:
                ax.set_ylabel("z", fontsize=9)

        # Remove unused subplots
        for j in range(z_dim, len(axes_flat)):
            fig.delaxes(axes_flat[j])

        fig.suptitle(
            f"z response to {param.name}{unit_str}\n(red dashed = nominal)",
            fontsize=12,
            fontweight="bold",
        )
        fig.tight_layout()

        safe_name = param.name.lower().replace(" ", "_")
        fig.savefig(os.path.join(output_dir, f"sweep_{safe_name}.png"), dpi=150, bbox_inches="tight")
        plt.close(fig)


def plot_sensitivity_heatmap(
    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]],
    output_path: str,
) -> None:
    """Create a heatmap showing sensitivity magnitude (z range) per parameter per z dim."""
    n_params = len(all_results)
    sensitivity = np.zeros((n_params, ENCODER_LATENT_DIM))

    param_names = []
    for i, (param, _values, z) in enumerate(all_results):
        param_names.append(param.name)
        for j in range(ENCODER_LATENT_DIM):
            sensitivity[i, j] = z[:, j].max() - z[:, j].min()

    fig, ax = plt.subplots(figsize=(16, 6))
    im = ax.imshow(sensitivity.T, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(n_params))
    ax.set_xticklabels(param_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(ENCODER_LATENT_DIM))
    ax.set_yticklabels([f"z_{j}" for j in range(ENCODER_LATENT_DIM)], fontsize=9)
    ax.set_xlabel("DR Parameter", fontsize=11)
    ax.set_ylabel("Latent Dimension", fontsize=11)
    ax.set_title(
        "Encoder Sensitivity Heatmap (z range over DR sweep)",
        fontsize=13,
        fontweight="bold",
    )

    # Annotate cells with values
    for i in range(n_params):
        for j in range(ENCODER_LATENT_DIM):
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
        "--checkpoint",
        type=str,
        default=LATEST_CHECKPOINT,
        help="Path to encoder checkpoint (.pt file)",
    )
    parser.add_argument(
        "--num_points",
        type=int,
        default=100,
        help="Number of sweep points per parameter",
    )
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="Output directory (default: same as checkpoint dir + /encoder_analysis)",
    )
    parser.add_argument(
        "--activation",
        type=str,
        default="tanh",
        choices=["tanh", "sigmoid"],
        help="Encoder output activation (default: tanh)",
    )
    args = parser.parse_args()

    ckpt_path = args.checkpoint
    if not os.path.isabs(ckpt_path):
        ckpt_path = os.path.join("/workspace/isaaclab", ckpt_path)

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(ckpt_path), "encoder_analysis")
    os.makedirs(output_dir, exist_ok=True)

    activation = args.activation
    z_range_str = "[-1, 1] (tanh)" if activation == "tanh" else "[0.01, 2.0] (sigmoid)"

    print(f"Loading encoder from: {ckpt_path}")
    encoder, norm_mean, norm_std = load_encoder(ckpt_path, activation)
    nominal = torch.tensor(NOMINAL_20D, dtype=torch.float32)

    print(f"Nominal obs ({PRIVILEGED_DIM}D): {nominal.numpy()}")
    print(f"Normalizer mean: {norm_mean.squeeze().numpy()}")
    print(f"Normalizer std:  {norm_std.squeeze().numpy()}")
    print(f"z range: {z_range_str}")
    print(f"Sweeping {len(SWEEP_PARAMS)} parameters with {args.num_points} points each...\n")

    all_results = []
    for param in SWEEP_PARAMS:
        values, z = sweep_parameter(encoder, norm_mean, norm_std, nominal, param, activation, args.num_points)

        # Print per-param summary
        z_ranges = z.max(axis=0) - z.min(axis=0)
        active_dims = np.sum(z_ranges > 0.05)
        print(
            f"  {param.name:25s} | "
            f"sweep [{param.low:.5f}, {param.high:.5f}] | "
            f"active z dims (range>0.05): {active_dims:2d}/{ENCODER_LATENT_DIM} | "
            f"max z range: {z_ranges.max():.4f}"
        )
        all_results.append((param, values, z))

    # Generate plots
    heatmap_path = os.path.join(output_dir, "z_sensitivity_heatmap.png")

    print(f"\nGenerating per-parameter plots -> {output_dir}/sweep_*.png")
    plot_per_parameter(all_results, nominal, output_dir, activation)

    print(f"Generating heatmap             -> {heatmap_path}")
    plot_sensitivity_heatmap(all_results, heatmap_path)

    print(f"\nDone! Output: {output_dir}")


if __name__ == "__main__":
    main()
