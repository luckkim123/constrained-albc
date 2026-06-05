#!/usr/bin/env python3
"""OMX encoder z-sweep adapter (sim-free, CPU-only) for Constrained ALBC.

No omx core path reads encoder latent sensitivity. This adapter exposes the
per-DR-parameter z-sweep required by repo rule 03-analysis-quality.md
("Encoder 학습 여부를 TB aggregate만으로 단정 금지 ... per-dim z sensitivity
sweep 필수"). It ASSEMBLES three sim-free engine functions and computes only
the z-range (max-min) sensitivity -- it owns no model logic, so its single
computed quantity is guarded against drift by test_matches_engine_z_ranges.
Runs on CPU (map_location='cpu', tiny MLP); no Isaac Sim, no GPU.

Usage:
    python3 encoder_adapter.py sweep <checkpoint.pt> [--num-points 100]
                                     [--plots <output_dir>]
"""
from __future__ import annotations

import argparse
import importlib
import json
import os
import sys

# One-line sys.path shim to reach the sim-free analysis package.
# Verified 2026-06-05: putting analysis/ on sys.path is sufficient because
# _encoder/ and common are importable there (findings/analysis_refactor_2026_06_05...).
_ANALYSIS_DIR = os.environ.get(
    "ALBC_ANALYSIS_DIR",
    "/workspace/constrained-albc/constrained_albc/analysis",
)
if _ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, _ANALYSIS_DIR)


def _engine():
    """Import the sim-free engine modules lazily (keeps import errors local)."""
    sweep = importlib.import_module("_encoder.sweep")
    common = importlib.import_module("common")
    return sweep, common


def sweep_sensitivity(ckpt_path: str, num_points: int = 100) -> dict:
    """Per-DR-parameter z-range sensitivity, assembled from engine functions.

    Delegates loading + param-derivation + per-param forward to the engine;
    computes only z_range = z.max(0) - z.min(0). Returns a JSON-able dict:
        {checkpoint, input_dim, latent_dim, activation, norm_mode,
         params: [{name, dim_idx, low, high, unit, z_range:[...latent_dim],
                   active_dims}]}
    """
    import torch
    sweep, common = _engine()

    encoder, norm, latent_dim = sweep._load_encoder_for_sweep(ckpt_path)
    arch = common.get_encoder_architecture_from_checkpoint(ckpt_path)

    enc_lower = norm.lower.numpy() if norm.lower is not None else None
    enc_upper = norm.upper.numpy() if norm.upper is not None else None
    if norm.mode == "static_minmax":
        nominal_np = ((norm.lower + norm.upper) / 2.0).numpy()
    else:
        nominal_np = norm.mean.squeeze().numpy()
    params = common.build_sweep_params_from_checkpoint(
        arch.input_dim, nominal_np, enc_lower, enc_upper,
    )
    nominal = torch.tensor(nominal_np, dtype=torch.float32)

    out_params = []
    for p in params:
        _values, z = sweep._sweep_parameter(encoder, norm, nominal, p, num_points)
        z_range = (z.max(axis=0) - z.min(axis=0))  # the ONLY computed quantity
        out_params.append({
            "name": p.name,
            "dim_idx": int(p.dim_idx),
            "low": float(p.low),
            "high": float(p.high),
            "unit": p.unit,
            "z_range": [float(r) for r in z_range],
            "active_dims": int((z_range > 0.05).sum()),
        })

    return {
        "checkpoint": ckpt_path,
        "input_dim": int(arch.input_dim),
        "latent_dim": int(latent_dim),
        "activation": arch.output_activation,
        "norm_mode": norm.mode,
        "params": out_params,
    }


def _write_plots(ckpt_path: str, num_points: int, output_dir: str) -> None:
    """Regenerate heatmap + per-param PNGs by delegating to the engine plotters."""
    import torch
    sweep, common = _engine()

    os.makedirs(output_dir, exist_ok=True)
    encoder, norm, latent_dim = sweep._load_encoder_for_sweep(ckpt_path)
    arch = common.get_encoder_architecture_from_checkpoint(ckpt_path)
    enc_lower = norm.lower.numpy() if norm.lower is not None else None
    enc_upper = norm.upper.numpy() if norm.upper is not None else None
    if norm.mode == "static_minmax":
        nominal_np = ((norm.lower + norm.upper) / 2.0).numpy()
    else:
        nominal_np = norm.mean.squeeze().numpy()
    params = common.build_sweep_params_from_checkpoint(
        arch.input_dim, nominal_np, enc_lower, enc_upper)
    nominal = torch.tensor(nominal_np, dtype=torch.float32)

    all_results = []
    for p in params:
        values, z = sweep._sweep_parameter(encoder, norm, nominal, p, num_points)
        all_results.append((p, values, z))

    sweep._plot_per_parameter(
        all_results, nominal, output_dir, latent_dim, arch.output_activation)
    sweep._plot_sensitivity_heatmap(
        all_results, os.path.join(output_dir, "sweep_heatmap.png"), latent_dim)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OMX sim-free encoder z-sweep adapter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sw = sub.add_parser("sweep", help="per-DR-param per-dim z-range sensitivity")
    sw.add_argument("checkpoint", help="path to a model_*.pt checkpoint")
    sw.add_argument("--num-points", type=int, default=100,
                    help="sweep points per parameter (default 100)")
    sw.add_argument("--plots", default=None,
                    help="if set, also write heatmap + per-param PNGs to this dir")
    args = parser.parse_args(argv)

    if args.cmd == "sweep":
        # Redirect stdout to stderr during engine calls so any engine [INFO]
        # prints do not corrupt the JSON output on stdout.
        _real_stdout = sys.stdout
        sys.stdout = sys.stderr
        try:
            out = sweep_sensitivity(args.checkpoint, num_points=args.num_points)
            if args.plots:
                _write_plots(args.checkpoint, args.num_points, args.plots)
                out["plots_dir"] = args.plots
        finally:
            sys.stdout = _real_stdout
        print(json.dumps(out))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
