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
import torch
import torch.nn as nn

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

LATEST_CHECKPOINT = (
    "logs/rsl_rl/hero_agent_albc_encoder/2026-02-24_15-27-22/model_1499.pt"
)

# Nominal privileged obs (26D) assembled from env.yaml hydro/buoy configs.
# These are the *unscaled* nominal values (DR scale = 1.0).
NOMINAL_26D = [
    # Main body hydro (7D): volume, CoG(3), CoB(3)
    0.00827,                    # [0]  main volume
    0.0, 0.0, -0.05,           # [1:4] main CoG
    0.0, 0.0, 0.0,             # [4:7] main CoB
    # Buoy body hydro (7D): volume, CoG(3), CoB(3)
    0.00268,                    # [7]  buoy volume
    0.0, 0.0, 0.0,             # [8:11] buoy CoG
    0.0, 0.0, 0.0,             # [11:14] buoy CoB
    # Main dynamics (4D): inertia Ixx/Iyy/Izz, body_mass
    0.0994, 0.0994, 0.0372,    # [14:17] main inertia
    9.18,                       # [17] main body mass
    # Buoy dynamics (4D): inertia Ixx/Iyy/Izz, body_mass
    0.00278, 0.00278, 0.00336, # [18:21] buoy inertia
    0.93,                       # [21] buoy body mass
    # Payload (4D): mass, cog_offset xyz
    0.5,                        # [22] payload mass
    0.0, 0.0, -0.015,          # [23:26] payload cog offset
]


@dataclass
class SweepParam:
    """Definition of a single parameter to sweep."""

    name: str
    dim_idx: int
    low: float
    high: float
    unit: str = ""


# Key parameters to sweep: volume, mass, inertia, payload
SWEEP_PARAMS = [
    SweepParam("Main Volume", 0, 0.00827 * 0.9, 0.00827 * 1.1, "m^3"),
    SweepParam("Buoy Volume", 7, 0.00268 * 0.9, 0.00268 * 1.1, "m^3"),
    SweepParam("Main Body Mass", 17, 9.18 * 0.9, 9.18 * 1.1, "kg"),
    SweepParam("Buoy Body Mass", 21, 0.93 * 0.9, 0.93 * 1.1, "kg"),
    SweepParam("Main Inertia Ixx", 14, 0.0994 * 0.75, 0.0994 * 1.3, "kg*m^2"),
    SweepParam("Main Inertia Iyy", 15, 0.0994 * 0.75, 0.0994 * 1.3, "kg*m^2"),
    SweepParam("Main Inertia Izz", 16, 0.0372 * 0.75, 0.0372 * 1.3, "kg*m^2"),
    SweepParam("Buoy Inertia Ixx", 18, 0.00278 * 0.75, 0.00278 * 1.3, "kg*m^2"),
    SweepParam("Buoy Inertia Iyy", 19, 0.00278 * 0.75, 0.00278 * 1.3, "kg*m^2"),
    SweepParam("Buoy Inertia Izz", 20, 0.00336 * 0.75, 0.00336 * 1.3, "kg*m^2"),
    SweepParam("Payload Mass", 22, 0.0, 1.5, "kg"),
]


# ---------------------------------------------------------------------------
# Encoder reconstruction (no Isaac Sim dependency)
# ---------------------------------------------------------------------------


def build_encoder_mlp() -> nn.Sequential:
    """Reconstruct the encoder MLP: 26D -> [256,128,64] -> 13D with ELU + Tanh.

    Matches the rsl_rl MLP structure with last_activation='tanh'.
    Layer indices: 0(Linear) 1(ELU) 2(Linear) 3(ELU) 4(Linear) 5(ELU) 6(Linear) 7(Tanh)
    """
    return nn.Sequential(
        nn.Linear(26, 256),
        nn.ELU(),
        nn.Linear(256, 128),
        nn.ELU(),
        nn.Linear(128, 64),
        nn.ELU(),
        nn.Linear(64, 13),
        nn.Tanh(),
    )


def load_encoder(ckpt_path: str) -> tuple[nn.Sequential, torch.Tensor, torch.Tensor]:
    """Load encoder MLP and normalizer statistics from checkpoint.

    Returns:
        encoder: The encoder MLP in eval mode.
        norm_mean: (1, 26) running mean from EmpiricalNormalization.
        norm_std: (1, 26) running std from EmpiricalNormalization.
    """
    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    state_dict = ckpt["model_state_dict"]

    # Extract encoder weights
    encoder = build_encoder_mlp()
    encoder_state = {
        k.removeprefix("encoder."): v
        for k, v in state_dict.items()
        if k.startswith("encoder.")
    }
    encoder.load_state_dict(encoder_state)
    encoder.eval()

    # Extract normalizer statistics
    norm_mean = state_dict["encoder_obs_normalizer._mean"]  # (1, 26)
    norm_std = state_dict["encoder_obs_normalizer._std"]  # (1, 26)

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
    num_points: int = 100,
) -> tuple[np.ndarray, np.ndarray]:
    """Sweep a single parameter and return (values, z_responses).

    Args:
        encoder: Loaded encoder MLP.
        norm_mean: Normalizer running mean.
        norm_std: Normalizer running std.
        nominal: (26,) nominal privileged observation.
        param: Which parameter to sweep.
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
        z = encoder(normed)

    return values.numpy(), z.numpy()


# ---------------------------------------------------------------------------
# Plotting
# ---------------------------------------------------------------------------


def plot_per_parameter(
    all_results: list[tuple[SweepParam, np.ndarray, np.ndarray]],
    nominal: torch.Tensor,
    output_dir: str,
    z_dim: int = 13,
) -> None:
    """Create one figure per parameter, with a subplot for each z dimension."""
    n_cols = 4
    n_rows = (z_dim + n_cols - 1) // n_cols  # 4 rows for 13 dims

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
            ax.set_ylim(-1.1, 1.1)
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
    sensitivity = np.zeros((n_params, 13))

    param_names = []
    for i, (param, _values, z) in enumerate(all_results):
        param_names.append(param.name)
        for j in range(13):
            sensitivity[i, j] = z[:, j].max() - z[:, j].min()

    fig, ax = plt.subplots(figsize=(14, 6))
    im = ax.imshow(sensitivity.T, aspect="auto", cmap="YlOrRd", interpolation="nearest")

    ax.set_xticks(range(n_params))
    ax.set_xticklabels(param_names, rotation=45, ha="right", fontsize=9)
    ax.set_yticks(range(13))
    ax.set_yticklabels([f"z_{j}" for j in range(13)], fontsize=9)
    ax.set_xlabel("DR Parameter", fontsize=11)
    ax.set_ylabel("Latent Dimension", fontsize=11)
    ax.set_title(
        "Encoder Sensitivity Heatmap (z range over DR sweep)",
        fontsize=13,
        fontweight="bold",
    )

    # Annotate cells with values
    for i in range(n_params):
        for j in range(13):
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
    args = parser.parse_args()

    ckpt_path = args.checkpoint
    if not os.path.isabs(ckpt_path):
        ckpt_path = os.path.join("/workspace/isaaclab", ckpt_path)

    output_dir = args.output_dir
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(ckpt_path), "encoder_analysis")
    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading encoder from: {ckpt_path}")
    encoder, norm_mean, norm_std = load_encoder(ckpt_path)
    nominal = torch.tensor(NOMINAL_26D, dtype=torch.float32)

    print(f"Nominal obs (26D): {nominal.numpy()}")
    print(f"Normalizer mean: {norm_mean.squeeze().numpy()}")
    print(f"Normalizer std:  {norm_std.squeeze().numpy()}")
    print(f"Sweeping {len(SWEEP_PARAMS)} parameters with {args.num_points} points each...\n")

    all_results = []
    for param in SWEEP_PARAMS:
        values, z = sweep_parameter(encoder, norm_mean, norm_std, nominal, param, args.num_points)

        # Print per-param summary
        z_ranges = z.max(axis=0) - z.min(axis=0)
        active_dims = np.sum(z_ranges > 0.05)
        print(
            f"  {param.name:20s} | "
            f"sweep [{param.low:.5f}, {param.high:.5f}] | "
            f"active z dims (range>0.05): {active_dims:2d}/13 | "
            f"max z range: {z_ranges.max():.4f}"
        )
        all_results.append((param, values, z))

    # Generate plots
    heatmap_path = os.path.join(output_dir, "z_sensitivity_heatmap.png")

    print(f"\nGenerating per-parameter plots -> {output_dir}/sweep_*.png")
    plot_per_parameter(all_results, nominal, output_dir)

    print(f"Generating heatmap             -> {heatmap_path}")
    plot_sensitivity_heatmap(all_results, heatmap_path)

    print("\nDone!")


if __name__ == "__main__":
    main()
