# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Shared constants and utilities for Full-DOF ALBC analysis scripts.

Provides DR constants, checkpoint-based encoder architecture inference,
and sweep parameter builders derived from checkpoint normalizer bounds.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

# ---------------------------------------------------------------------------
# DR constants (no Isaac Lab dependency)
# ---------------------------------------------------------------------------

# In-distribution DR levels. "ood" (out-of-distribution stress, eval.py --ood)
# is NOT part of the in-dist set but IS a renderable level: its scale/color
# entries below let plots index DR_SCALE[lvl]/DR_COLORS[lvl] without a KeyError
# when an eval ran with --ood. Plot level lists are derived from the actual
# all_data keys (see eval_plots.generate_plots), not from DR_LEVELS, so a
# 4-level eval still draws exactly 4.
DR_LEVELS: list[str] = ["none", "soft", "medium", "hard"]
# Canonical render order including the optional out-of-distribution level.
DR_RENDER_ORDER: list[str] = ["none", "soft", "medium", "hard", "ood"]
DR_SCALE: dict[str, float] = {"none": 0.0, "soft": 0.3, "medium": 0.6, "hard": 1.0, "ood": 1.0}
DR_COLORS: dict[str, str] = {
    "none": "#2196F3",
    "soft": "#4CAF50",
    "medium": "#FF9800",
    "hard": "#F44336",
    "ood": "#E91E63",  # magenta -- distinct from the in-dist gradient (out-of-range)
}


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
    max_idx = max(int(k.split(".")[1]) for k in enc_keys if len(k.split(".")) >= 3 and k.split(".")[1].isdigit())
    # Expected without output activation: (n_hidden + 1) Linears * 2 - 1
    # (each Linear except last has an activation after it)
    n_linears = len(linear_weights)
    expected_max_without_act = (n_linears - 1) * 2  # last Linear index
    has_output_act = max_idx > expected_max_without_act

    if has_output_act:
        activation = "tanh"
    elif input_dim >= 15 and (
        "_enc_obs_lower" in sd or "_enc_obs_upper" in sd or input_dim >= 23
    ):
        # Constrained ALBC encoder: softsign is applied functionally in _encode(),
        # not as a module in the MLP. Detect via static bounds or input dim >= 23.
        # 15D reduced encoder also uses softsign (has _enc_obs_lower/upper buffers).
        activation = "softsign"
    else:
        activation = "none"

    return EncoderArchitecture(
        hidden_dims=hidden_dims,
        latent_dim=latent_dim,
        input_dim=input_dim,
        output_activation=activation,
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


def _build_constrained_albc_27d_sweep(
    nm_priv: np.ndarray, offset: int = 0,
) -> list[SweepParam]:
    """Build sweep params for constrained ALBC 27D privileged obs.

    27D structure (indices relative to privileged start):
         0: Main volume, 1: Main CoG_z, 2: Main CoB_z
         3: Buoy volume, 4: Buoy CoG_z, 5: Buoy CoB_z
         6: Main Ixx, 7: Main Iyy, 8: Buoy Ixx, 9: Buoy Iyy
        10: Payload mass, 11-13: Payload CoG xyz
        14: Main added mass surge
        15: Joint Kp, 16: Joint Kd, 17: Joint effort limit
        18-19: Lin damping roll/pitch, 20-21: Quad damping roll/pitch
        22: Body mass, 23: Action latency
        24: Static friction, 25: Viscous friction
        26: Water density

    Args:
        nm_priv: (27,) normalizer mean for the privileged portion.
        offset: Index offset to add (253 for full 280D input, 0 for standalone).
    """
    p = nm_priv
    o = offset
    return [
        SweepParam("Main Volume", o + 0, p[0] * 0.9, p[0] * 1.1, "m^3"),
        SweepParam("Main CoG Z", o + 1, p[1] - 0.02, p[1] + 0.02, "m"),
        SweepParam("Main CoB Z", o + 2, p[2] - 0.02, p[2] + 0.02, "m"),
        SweepParam("Buoy Volume", o + 3, p[3] * 0.9, p[3] * 1.1, "m^3"),
        SweepParam("Buoy CoG Z", o + 4, p[4] - 0.02, p[4] + 0.02, "m"),
        SweepParam("Buoy CoB Z", o + 5, p[5] - 0.02, p[5] + 0.02, "m"),
        SweepParam("Main Ixx", o + 6, p[6] * 0.75, p[6] * 1.3, "kg*m^2"),
        SweepParam("Main Iyy", o + 7, p[7] * 0.75, p[7] * 1.3, "kg*m^2"),
        SweepParam("Buoy Ixx", o + 8, p[8] * 0.75, p[8] * 1.3, "kg*m^2"),
        SweepParam("Buoy Iyy", o + 9, p[9] * 0.75, p[9] * 1.3, "kg*m^2"),
        SweepParam("Payload Mass", o + 10, 0.0, 1.0, "kg"),
        SweepParam("Payload CoG X", o + 11, -0.10, 0.10, "m"),
        SweepParam("Payload CoG Y", o + 12, -0.10, 0.10, "m"),
        SweepParam("Payload CoG Z", o + 13, -0.03, 0.0, "m"),
        SweepParam("Added Mass Surge", o + 14, p[14] * 0.85, p[14] * 1.15, "kg"),
        SweepParam("Joint Stiffness", o + 15, 40.0, 120.0, "Nm/rad"),
        SweepParam("Joint Damping", o + 16, 0.5, 5.0, "Nm*s/rad"),
        SweepParam("Effort Limit", o + 17, 0.7 * 9.5, 1.0 * 9.5, "Nm"),
        SweepParam("Lin Damp Roll", o + 18, p[18] * 0.5, p[18] * 1.5, ""),
        SweepParam("Lin Damp Pitch", o + 19, p[19] * 0.5, p[19] * 1.5, ""),
        SweepParam("Quad Damp Roll", o + 20, p[20] * 0.5, p[20] * 1.5, ""),
        SweepParam("Quad Damp Pitch", o + 21, p[21] * 0.5, p[21] * 1.5, ""),
        SweepParam("Body Mass", o + 22, p[22] * 0.9, p[22] * 1.1, "kg"),
        SweepParam("Action Latency", o + 23, 0.0, 4.0, "steps"),
        SweepParam("Static Friction", o + 24, 0.0, 0.03, ""),
        SweepParam("Viscous Friction", o + 25, 0.0, 0.2, ""),
        SweepParam("Water Density", o + 26, 995.0, 1025.0, "kg/m^3"),
    ]


def _build_constrained_albc_28d_sweep(
    nm_priv: np.ndarray, offset: int = 0,
) -> list[SweepParam]:
    """Build sweep params for constrained ALBC 28D privileged obs (legacy).

    Same as 27D but with yaw quad damping at index 26, water density at 27.
    """
    p = nm_priv
    o = offset
    params = _build_constrained_albc_27d_sweep(p, o)
    # Replace last entry (Water Density at 26) with Yaw Quad Damp, then add Water Density at 27
    params[-1] = SweepParam("Yaw Quad Damp", o + 26, p[26] * 0.5, p[26] * 1.5, "")
    params.append(SweepParam("Water Density", o + 27, 995.0, 1025.0, "kg/m^3"))
    return params


def _build_constrained_albc_23d_sweep(
    lower: np.ndarray, upper: np.ndarray, offset: int = 0,
) -> list[SweepParam]:
    """Build sweep params for constrained ALBC 23D privileged obs.

    23D structure:
         0-5:  Hydrodynamics (main vol, CoG_z, CoB_z, buoy vol, CoG_z, CoB_z)
         6-9:  Inertia (main Ixx, Iyy, buoy Ixx, Iyy)
        10-13: Damping (lin roll, lin pitch, quad roll, quad pitch)
        14-15: Body (mass, added_mass_surge)
        16-19: Payload (mass, cog_x, cog_y, cog_z)
        20-22: Actuator+Env (stiffness, damping, water_density)

    Uses static min-max bounds (lower/upper) from checkpoint as sweep ranges.
    """
    o = offset
    names = [
        "Main Volume", "Main CoG Z", "Main CoB Z", "Buoy Volume", "Buoy CoG Z", "Buoy CoB Z",
        "Main Ixx", "Main Iyy", "Buoy Ixx", "Buoy Iyy",
        "Lin Damp Roll", "Lin Damp Pitch", "Quad Damp Roll", "Quad Damp Pitch",
        "Body Mass", "Added Mass Surge",
        "Payload Mass", "Payload CoG X", "Payload CoG Y", "Payload CoG Z",
        "Joint Stiffness", "Joint Damping", "Water Density",
    ]
    units = [
        "m^3", "m", "m", "m^3", "m", "m",
        "kg*m^2", "kg*m^2", "kg*m^2", "kg*m^2",
        "", "", "", "",
        "kg", "kg",
        "kg", "m", "m", "m",
        "Nm/rad", "Nm*s/rad", "kg/m^3",
    ]
    return [
        SweepParam(names[i], o + i, float(lower[i]), float(upper[i]), units[i])
        for i in range(23)
    ]


def _build_constrained_albc_24d_sweep(
    lower: np.ndarray, upper: np.ndarray, offset: int = 0,
) -> list[SweepParam]:
    """Build sweep params for the current constrained ALBC 24D privileged obs.

    Layout is authoritative from envs/main/mdp/observations.py:compute_privileged_obs
    (24D). Differs from the legacy 23D table: inertia/damping are collapsed to single
    representative dims and ocean-current velocity (3D) is appended.

        Hydrodynamics (7D):  [0] main vol, [1:4] main CoG xyz, [4:7] main CoB xyz
        Dynamic Response (5D): [7] main Ixx, [8] lin damp roll, [9] quad damp roll,
                               [10] body mass, [11] added mass surge
        Payload (4D):        [12] payload mass, [13:16] payload CoG offset xyz
        Actuator (4D):       [16] joint stiffness Kp, [17] joint damping Kd,
                             [18] thrust coeff, [19] time const up
        Environment (4D):    [20] water density, [21:24] ocean current vel xyz

    Uses static min-max bounds (lower/upper) from checkpoint as sweep ranges.
    """
    o = offset
    names = [
        "Main Volume", "Main CoG X", "Main CoG Y", "Main CoG Z",
        "Main CoB X", "Main CoB Y", "Main CoB Z",
        "Main Ixx", "Lin Damp Roll", "Quad Damp Roll", "Body Mass", "Added Mass Surge",
        "Payload Mass", "Payload CoG X", "Payload CoG Y", "Payload CoG Z",
        "Joint Stiffness", "Joint Damping", "Thrust Coeff", "Time Const Up",
        "Water Density", "Ocean Current X", "Ocean Current Y", "Ocean Current Z",
    ]
    units = [
        "m^3", "m", "m", "m",
        "m", "m", "m",
        "kg*m^2", "", "", "kg", "kg",
        "kg", "m", "m", "m",
        "Nm/rad", "Nm*s/rad", "", "s",
        "kg/m^3", "m/s", "m/s", "m/s",
    ]
    return [
        SweepParam(names[i], o + i, float(lower[i]), float(upper[i]), units[i])
        for i in range(24)
    ]


def _build_reduced_encoder_sweep(
    input_dim: int,
    lower: np.ndarray,
    upper: np.ndarray,
) -> list[SweepParam]:
    """Build sweep params for reduced encoder input using bounds directly.

    Parameter names are mapped from the full 23D naming table via _enc_obs_indices
    stored in the checkpoint. Falls back to generic dim_N names if no mapping.
    """
    # Full 23D parameter name/unit table
    _NAMES_23D = [
        "Main Volume", "Main CoG Z", "Main CoB Z", "Buoy Volume", "Buoy CoG Z", "Buoy CoB Z",
        "Main Ixx", "Main Iyy", "Buoy Ixx", "Buoy Iyy",
        "Lin Damp Roll", "Lin Damp Pitch", "Quad Damp Roll", "Quad Damp Pitch",
        "Body Mass", "Added Mass Surge",
        "Payload Mass", "Payload CoG X", "Payload CoG Y", "Payload CoG Z",
        "Joint Stiffness", "Joint Damping", "Water Density",
    ]
    _UNITS_23D = [
        "m^3", "m", "m", "m^3", "m", "m",
        "kg*m^2", "kg*m^2", "kg*m^2", "kg*m^2",
        "", "", "", "",
        "kg", "kg",
        "kg", "m", "m", "m",
        "Nm/rad", "Nm*s/rad", "kg/m^3",
    ]
    # Known index mappings (from rsl_rl_ppo_cfg.py _ENC_OBS_INDICES_15D)
    _KNOWN_INDICES = {
        15: [0, 1, 2, 3, 10, 11, 12, 13, 14, 15, 16, 17, 18, 20, 21],
    }
    indices = _KNOWN_INDICES.get(input_dim)
    params = []
    for i in range(input_dim):
        if indices is not None and indices[i] < len(_NAMES_23D):
            name = _NAMES_23D[indices[i]]
            unit = _UNITS_23D[indices[i]]
        else:
            name = f"dim_{i}"
            unit = ""
        params.append(SweepParam(name, i, float(lower[i]), float(upper[i]), unit))
    return params


def build_sweep_params_from_checkpoint(
    input_dim: int,
    norm_mean: np.ndarray,
    enc_obs_lower: np.ndarray | None = None,
    enc_obs_upper: np.ndarray | None = None,
) -> list[SweepParam]:
    """Build sweep params using checkpoint normalizer mean as nominal center.

    Supports:
      - legacy 19D privileged-only encoder input
      - constrained_albc 27D or 28D privileged-only encoder input
      - constrained_albc 280D full concatenated encoder input
        (policy_obs(13) + history(240) + privileged(27))

    DR ranges are hardcoded from the respective DomainRandomizationCfg defaults.

    Args:
        input_dim: Encoder input dimension.
        norm_mean: (D,) normalizer running mean from checkpoint.
        enc_obs_lower: Static min-max lower bounds (for 23D constrained ALBC).
        enc_obs_upper: Static min-max upper bounds (for 23D constrained ALBC).
    """
    # --- Constrained ALBC with static min-max bounds ---
    if enc_obs_lower is not None and enc_obs_upper is not None:
        if input_dim == 24:
            return _build_constrained_albc_24d_sweep(enc_obs_lower, enc_obs_upper)
        if input_dim == 23:
            return _build_constrained_albc_23d_sweep(enc_obs_lower, enc_obs_upper)
        # Reduced encoder (e.g. 15D): build sweep from bounds directly
        return _build_reduced_encoder_sweep(input_dim, enc_obs_lower, enc_obs_upper)

    nm = norm_mean.flatten()

    # --- Full concatenated input (policy_obs + history + privileged) ---
    # Detect by input_dim >> 28. Privileged portion is at the end.
    if input_dim >= 100:
        # Detect privileged dim: water density (~1010) at end -> constrained ALBC 27D
        if nm[-1] > 500:
            priv_dim = 27
        else:
            priv_dim = 19
        offset = input_dim - priv_dim
        nm_priv = nm[offset:]
        if priv_dim == 27:
            return _build_constrained_albc_27d_sweep(nm_priv, offset)
        # Legacy 19D privileged input at end of full concatenated input
        return [
            SweepParam("Main Volume", offset + 0, nm_priv[0] * 0.9, nm_priv[0] * 1.1, "m^3"),
            SweepParam("Buoy Volume", offset + 5, nm_priv[5] * 0.9, nm_priv[5] * 1.1, "m^3"),
            SweepParam("Main CoG Z", offset + 3, nm_priv[3] - 0.06, nm_priv[3] + 0.06, "m"),
            SweepParam("Main Ixx", offset + 10, nm_priv[10] * 0.75, nm_priv[10] * 1.3, "kg*m^2"),
            SweepParam("Main Iyy", offset + 11, nm_priv[11] * 0.75, nm_priv[11] * 1.3, "kg*m^2"),
            SweepParam("Buoy Ixx", offset + 12, nm_priv[12] * 0.75, nm_priv[12] * 1.3, "kg*m^2"),
            SweepParam("Buoy Iyy", offset + 13, nm_priv[13] * 0.75, nm_priv[13] * 1.3, "kg*m^2"),
            SweepParam("Payload Mass", offset + 14, 0.0, 2.0, "kg"),
            SweepParam("Payload CoG Z", offset + 17, -0.03, 0.0, "m"),
            SweepParam("Added Mass Surge", offset + 18, nm_priv[18] * 0.85, nm_priv[18] * 1.15, "kg"),
        ]

    if input_dim in (27, 28):
        return _build_constrained_albc_27d_sweep(nm, offset=0) if input_dim == 27 \
            else _build_constrained_albc_28d_sweep(nm, offset=0)

    # Legacy 19D privileged input (existing structure):
    #  0-4: Main hydro (volume, CoG_xyz, CoB_z)
    #  5-9: Buoy hydro (volume, CoG_xyz, CoB_z)
    # 10-11: Main Ixx, Iyy, 12-13: Buoy Ixx, Iyy
    # 14-17: Payload (mass, CoG xyz), 18: Added mass surge
    return [
        SweepParam("Main Volume", 0, nm[0] * 0.9, nm[0] * 1.1, "m^3"),
        SweepParam("Buoy Volume", 5, nm[5] * 0.9, nm[5] * 1.1, "m^3"),
        SweepParam("Main CoG Z", 3, nm[3] - 0.06, nm[3] + 0.06, "m"),
        SweepParam("Main Ixx", 10, nm[10] * 0.75, nm[10] * 1.3, "kg*m^2"),
        SweepParam("Main Iyy", 11, nm[11] * 0.75, nm[11] * 1.3, "kg*m^2"),
        SweepParam("Buoy Ixx", 12, nm[12] * 0.75, nm[12] * 1.3, "kg*m^2"),
        SweepParam("Buoy Iyy", 13, nm[13] * 0.75, nm[13] * 1.3, "kg*m^2"),
        SweepParam("Payload Mass", 14, 0.0, 2.0, "kg"),
        SweepParam("Payload CoG Z", 17, -0.03, 0.0, "m"),
        SweepParam("Added Mass Surge", 18, nm[18] * 0.85, nm[18] * 1.15, "kg"),
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


def resolve_run_path(run_spec: str, logs_root: str = "logs/rsl_rl") -> Path:
    """Resolve a run specifier to a Path holding tb events / checkpoints.

    Delegates to ``paths.resolve_run`` (run_id design #5), so a run is now found whether
    it lives in the run_id tree (``experiments/<run_id>/``) or the legacy ``logs/rsl_rl``
    layout. Returns the run's ``tb_dir`` -- for a run_id tree that is ``<run>/train`` (where
    tfevents + checkpoints live), for a legacy run it is the run dir itself -- so existing
    callers (monitor: ``load_tb_scalars``; encoder debug: ``glob model_*.pt``) keep working.

    Accepts a full path, an integer index (0 = latest), or a substring match.
    """
    from paths import resolve_run  # sibling import (analysis/ on sys.path via the entrypoint)

    return resolve_run(run_spec, legacy_logs_root=logs_root).tb_dir
