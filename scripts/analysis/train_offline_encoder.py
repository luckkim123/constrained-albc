#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Train offline encoder with value prediction bottleneck.

Pure PyTorch -- no Isaac Sim required. Takes collected rollout data (.pt)
and trains an encoder MLP to compress privileged info (23D) into z (13D)
such that cat([o_t, z]) predicts the critic value.

Architecture:
    Encoder: p_t(23D) -> static_minmax_norm -> MLP[256,128,64](ELU) -> softsign -> z(13D)
    Value head: cat([o_t(14D), z(13D)]) -> Linear(27, 1) -> V_hat
    Loss: MSE(V_hat, V_critic_target)

The value head does NOT include history -- this forces z to encode dynamics
information that o_t alone cannot provide.

Usage:
    python3 scripts/analysis/train_offline_encoder.py \
        --data logs/offline_encoder/rollout_data.pt \
        --output logs/offline_encoder/encoder.pt \
        --epochs 500
"""

import argparse
import os

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.utils.data import DataLoader, TensorDataset, random_split


class OfflineEncoder(nn.Module):
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
        return (2 * p_t - self._enc_obs_upper - self._enc_obs_lower) / (
            self._enc_obs_upper - self._enc_obs_lower + 1e-8
        )

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


def compute_empirical_bounds(
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


def train(
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
    lower, upper = compute_empirical_bounds(privileged)
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
    model = OfflineEncoder(
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


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train offline encoder with value prediction bottleneck.")
    parser.add_argument("--data", type=str, required=True, help="Path to collected rollout data (.pt)")
    parser.add_argument("--output", type=str, required=True, help="Output encoder checkpoint path (.pt)")
    parser.add_argument("--epochs", type=int, default=500, help="Number of training epochs.")
    parser.add_argument("--batch_size", type=int, default=4096, help="Batch size.")
    parser.add_argument("--lr", type=float, default=3e-4, help="Learning rate.")
    parser.add_argument("--device", type=str, default="cuda" if torch.cuda.is_available() else "cpu")
    args = parser.parse_args()

    train(
        data_path=args.data,
        output_path=args.output,
        epochs=args.epochs,
        batch_size=args.batch_size,
        lr=args.lr,
        device=args.device,
    )
