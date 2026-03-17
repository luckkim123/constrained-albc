# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared constants and utilities for Hero Agent analysis scripts.

Imports authoritative values from hero_agent modules to eliminate
hardcoded constants. Provides checkpoint-based fallback for
environments without Isaac Lab installed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# DR constants (no Isaac Lab dependency)
# ---------------------------------------------------------------------------

DR_LEVELS: list[str] = ["none", "soft", "medium", "hard"]
DR_SCALE: dict[str, float] = {"none": 0.0, "soft": 0.3, "medium": 0.6, "hard": 1.0}
DR_COLORS: dict[str, str] = {
    "none": "#2196F3",
    "soft": "#4CAF50",
    "medium": "#FF9800",
    "hard": "#F44336",
}

# ---------------------------------------------------------------------------
# Isaac Lab imports (graceful fallback)
# ---------------------------------------------------------------------------

_ISAAC_AVAILABLE = False

try:
    from isaaclab_assets.robots.uuv import (
        HeroAgentBuoyHydrodynamicsCfg,
        HeroAgentHydrodynamicsCfg,
    )
    from isaaclab_tasks.direct.hero_agent.agents.rsl_rl_ppo_cfg import (
        _RslRlPpoEncoderBaseCfg,
    )
    from isaaclab_tasks.direct.hero_agent.config import DomainRandomizationCfg

    _ISAAC_AVAILABLE = True
except ImportError:
    pass


# ---------------------------------------------------------------------------
# Encoder architecture
# ---------------------------------------------------------------------------


@dataclass
class EncoderArchitecture:
    """Encoder MLP architecture descriptor."""

    hidden_dims: list[int] = field(default_factory=lambda: [256, 128, 64])
    latent_dim: int = 13
    input_dim: int = 19
    output_activation: str = "tanh"


def get_encoder_architecture() -> EncoderArchitecture:
    """Return encoder architecture from Isaac Lab config.

    Raises RuntimeError if Isaac Lab is not importable.
    """
    if not _ISAAC_AVAILABLE:
        raise RuntimeError(
            "Isaac Lab modules not importable. "
            "Use get_encoder_architecture_from_checkpoint() instead, "
            "or run via ./isaaclab.sh -p."
        )
    cfg = _RslRlPpoEncoderBaseCfg()
    return EncoderArchitecture(
        hidden_dims=list(cfg.encoder_hidden_dims),
        latent_dim=cfg.encoder_latent_dim,
        input_dim=cfg.privileged_dim,
        output_activation=cfg.encoder_output_activation,
    )


def get_encoder_architecture_from_checkpoint(ckpt_path: str) -> EncoderArchitecture:
    """Infer encoder architecture from checkpoint weight shapes.

    Works without Isaac Lab. Detects dims and activation from state dict.
    """
    import torch

    ckpt = torch.load(ckpt_path, map_location="cpu", weights_only=False)
    sd = ckpt["model_state_dict"]

    # Collect encoder Linear layer weights (skip activation layers)
    enc_keys = sorted(k for k in sd if k.startswith("encoder."))
    linear_weights = [k for k in enc_keys if k.endswith(".weight")]

    if not linear_weights:
        raise ValueError(f"No encoder weights found in {ckpt_path}")

    input_dim = sd[linear_weights[0]].shape[1]
    hidden_dims = [sd[k].shape[0] for k in linear_weights[:-1]]
    latent_dim = sd[linear_weights[-1]].shape[0]

    # Detect output activation: count total named modules
    # With tanh: ..., Linear, Tanh (extra module at end)
    # Without:  ..., Linear (no extra module)
    max_idx = max(
        int(k.split(".")[1]) for k in enc_keys if len(k.split(".")) >= 3 and k.split(".")[1].isdigit()
    )
    # Expected without output activation: (n_hidden + 1) Linears * 2 - 1
    # (each Linear except last has an activation after it)
    n_linears = len(linear_weights)
    expected_max_without_act = (n_linears - 1) * 2  # last Linear index
    has_output_act = max_idx > expected_max_without_act

    return EncoderArchitecture(
        hidden_dims=hidden_dims,
        latent_dim=latent_dim,
        input_dim=input_dim,
        output_activation="tanh" if has_output_act else "none",
    )


# ---------------------------------------------------------------------------
# Nominal observations and sweep parameters
# ---------------------------------------------------------------------------


@dataclass
class SweepParam:
    """Definition of a single parameter to sweep."""

    name: str
    dim_idx: int
    low: float
    high: float
    unit: str = ""


def build_nominal_obs() -> np.ndarray:
    """Assemble nominal privileged observation from hydro configs.

    19D structure:
        Main hydro (5): volume, CoG_xyz, CoB_z
        Buoy hydro (5): volume, CoG_xyz, CoB_z
        Main inertia (2): Ixx, Iyy
        Buoy inertia (2): Ixx, Iyy
        Payload (4): mass, cog_offset_xyz
        Main added mass surge (1)

    Raises RuntimeError if Isaac Lab is not importable.
    """
    if not _ISAAC_AVAILABLE:
        raise RuntimeError(
            "Isaac Lab modules not importable. "
            "Cannot build nominal obs without physics configs."
        )
    main = HeroAgentHydrodynamicsCfg()
    buoy = HeroAgentBuoyHydrodynamicsCfg()
    cfg = _RslRlPpoEncoderBaseCfg()

    obs = [
        # Main body hydro (5D)
        main.volume,
        *main.center_of_gravity,
        main.center_of_buoyancy[2],
        # Buoy hydro (5D)
        buoy.volume,
        *buoy.center_of_gravity,
        buoy.center_of_buoyancy[2],
        # Main inertia (2D)
        main.rigid_body_inertia[0],
        main.rigid_body_inertia[1],
        # Buoy inertia (2D)
        buoy.rigid_body_inertia[0],
        buoy.rigid_body_inertia[1],
        # Payload (4D) -- nominal values
        0.5,
        0.0,
        0.0,
        -0.015,
        # Main added mass surge (1D)
        main.added_mass[0],
    ]
    return np.array(obs[: cfg.privileged_dim], dtype=np.float32)


def build_sweep_params() -> list[SweepParam]:
    """Build sweep parameter definitions from DR config and hydro configs.

    Sweep ranges are derived from DomainRandomizationCfg defaults
    applied to nominal hydro values.

    Raises RuntimeError if Isaac Lab is not importable.
    """
    if not _ISAAC_AVAILABLE:
        raise RuntimeError(
            "Isaac Lab modules not importable. "
            "Cannot build sweep params without DR config."
        )
    dr = DomainRandomizationCfg()
    main = HeroAgentHydrodynamicsCfg()
    buoy = HeroAgentBuoyHydrodynamicsCfg()

    return [
        SweepParam(
            "Main Volume", 0,
            main.volume * dr.volume_scale[0],
            main.volume * dr.volume_scale[1], "m^3",
        ),
        SweepParam(
            "Buoy Volume", 5,
            buoy.volume * dr.volume_scale[0],
            buoy.volume * dr.volume_scale[1], "m^3",
        ),
        SweepParam(
            "Main CoG Z", 3,
            main.center_of_gravity[2] + dr.cog_offset_z[0],
            main.center_of_gravity[2] + dr.cog_offset_z[1], "m",
        ),
        SweepParam(
            "Main Inertia Ixx", 10,
            main.rigid_body_inertia[0] * dr.inertia_scale[0],
            main.rigid_body_inertia[0] * dr.inertia_scale[1], "kg*m^2",
        ),
        SweepParam(
            "Main Inertia Iyy", 11,
            main.rigid_body_inertia[1] * dr.inertia_scale[0],
            main.rigid_body_inertia[1] * dr.inertia_scale[1], "kg*m^2",
        ),
        SweepParam(
            "Buoy Inertia Ixx", 12,
            buoy.rigid_body_inertia[0] * dr.inertia_scale[0],
            buoy.rigid_body_inertia[0] * dr.inertia_scale[1], "kg*m^2",
        ),
        SweepParam(
            "Buoy Inertia Iyy", 13,
            buoy.rigid_body_inertia[1] * dr.inertia_scale[0],
            buoy.rigid_body_inertia[1] * dr.inertia_scale[1], "kg*m^2",
        ),
        SweepParam(
            "Payload Mass", 14,
            dr.payload_mass_range[0],
            dr.payload_mass_range[1], "kg",
        ),
        SweepParam(
            "Payload CoG Z", 17,
            dr.payload_cog_offset_z[0],
            dr.payload_cog_offset_z[1], "m",
        ),
        SweepParam(
            "Main Added Mass Surge", 18,
            main.added_mass[0] * dr.added_mass_scale[0],
            main.added_mass[0] * dr.added_mass_scale[1], "kg",
        ),
    ]


# ---------------------------------------------------------------------------
# TensorBoard utilities
# ---------------------------------------------------------------------------


def load_tb_scalars(log_dir: str) -> dict[str, list[tuple[int, float]]]:
    """Load all scalar metrics from TensorBoard event files.

    Returns:
        Dict mapping tag -> list of (step, value) tuples.
    """
    from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

    ea = EventAccumulator(log_dir)
    ea.Reload()
    data = {}
    for tag in ea.Tags().get("scalars", []):
        events = ea.Scalars(tag)
        data[tag] = [(e.step, e.value) for e in events]
    return data


def smooth(values: np.ndarray, window: int = 15) -> np.ndarray:
    """Simple moving average smoothing."""
    if len(values) < window:
        return values
    kernel = np.ones(window) / window
    return np.convolve(values, kernel, mode="same")


def find_hero_agent_runs(
    logs_root: str = "/workspace/isaaclab/logs/rsl_rl",
) -> list[Path]:
    """Find Hero Agent training runs, sorted newest first."""
    root = Path(logs_root)
    if not root.exists():
        return []
    runs: list[Path] = []
    for exp_dir in sorted(root.iterdir()):
        if not exp_dir.is_dir() or not exp_dir.name.startswith("hero_agent"):
            continue
        for run_dir in sorted(exp_dir.iterdir(), reverse=True):
            if run_dir.is_dir() and list(run_dir.glob("events.out.tfevents.*")):
                runs.append(run_dir)
    runs.sort(key=lambda p: p.name, reverse=True)
    return runs


def resolve_run_path(run_spec: str, logs_root: str = "/workspace/isaaclab/logs/rsl_rl") -> Path:
    """Resolve a run specifier to a Path.

    Accepts:
        - Full path to run directory
        - Integer index (0 = latest)
        - Substring match against run names
    """
    path = Path(run_spec)
    if path.exists():
        return path

    runs = find_hero_agent_runs(logs_root)
    if not runs:
        raise FileNotFoundError(f"No Hero Agent runs found in {logs_root}")

    # Try as integer index
    try:
        idx = int(run_spec)
        if idx >= len(runs):
            raise IndexError(f"Run index {idx} out of range ({len(runs)} runs)")
        return runs[idx]
    except ValueError:
        pass

    # Try substring match
    matches = [r for r in runs if run_spec in str(r)]
    if matches:
        return matches[0]

    raise FileNotFoundError(f"No run matching '{run_spec}'")
