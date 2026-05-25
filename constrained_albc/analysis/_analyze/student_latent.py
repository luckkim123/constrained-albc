# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`student_latent` subcommand: per-dim latent diagnostics (merged from analyze_student_latent.py)."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np

_SL_DR_LEVELS = ["none", "soft", "medium", "hard"]


def _sl_load_level(diag_dir: Path, level: str) -> tuple[np.ndarray, np.ndarray] | None:
    f = Path(diag_dir) / f"latent_log_{level}.npz"
    if not f.exists():
        return None
    z = np.load(f)
    return z["l_hat"], z["l_true"]


def _sl_summarize(l_hat: np.ndarray, l_true: np.ndarray) -> dict:
    err = l_hat - l_true
    per_dim_mse = (err ** 2).mean(axis=(0, 1))
    per_dim_envvar_true = l_true.var(axis=1).mean(axis=0)
    per_dim_envvar_hat = l_hat.var(axis=1).mean(axis=0)
    per_dim_tvar_true = l_true.var(axis=0).mean(axis=0)
    per_dim_tvar_hat = l_hat.var(axis=0).mean(axis=0)
    return {
        "overall_mse": float((err ** 2).mean()),
        "per_dim_mse": per_dim_mse.tolist(),
        "per_dim_envvar_true": per_dim_envvar_true.tolist(),
        "per_dim_envvar_hat": per_dim_envvar_hat.tolist(),
        "per_dim_tvar_true": per_dim_tvar_true.tolist(),
        "per_dim_tvar_hat": per_dim_tvar_hat.tolist(),
        "per_dim_bias": err.mean(axis=(0, 1)).tolist(),
    }


def _sl_plot_comparison(diag_dirs: list, out_path: Path) -> None:
    """Plot per-dim MSE and envvar ratio across DR levels for all runs."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    _fig, axes = plt.subplots(3, 4, figsize=(20, 12))

    for col, level in enumerate(_SL_DR_LEVELS):
        for di, d in enumerate(diag_dirs):
            res = _sl_load_level(d, level)
            if res is None:
                continue
            l_hat, l_true = res
            s = _sl_summarize(l_hat, l_true)

            dims = np.arange(len(s["per_dim_mse"]))

            # Row 0: per-dim MSE
            axes[0, col].bar(dims + di * 0.3, s["per_dim_mse"], width=0.3,
                             label=Path(d).parent.name, alpha=0.8)

            # Row 1: envvar_hat / envvar_true
            ratio = np.array(s["per_dim_envvar_hat"]) / (np.array(s["per_dim_envvar_true"]) + 1e-8)
            axes[1, col].bar(dims + di * 0.3, ratio, width=0.3,
                             label=Path(d).parent.name, alpha=0.8)

            # Row 2: per-dim bias
            axes[2, col].bar(dims + di * 0.3, s["per_dim_bias"], width=0.3,
                             label=Path(d).parent.name, alpha=0.8)

        axes[0, col].set_title(f"{level.upper()}: per-dim MSE")
        axes[0, col].set_xlabel("latent dim")
        axes[0, col].set_ylabel("MSE")
        axes[0, col].legend(fontsize=7)
        axes[0, col].grid(alpha=0.3)

        axes[1, col].set_title(f"{level.upper()}: envvar ratio (hat/true)")
        axes[1, col].axhline(1.0, color="k", lw=0.5, ls="--")
        axes[1, col].set_xlabel("latent dim")
        axes[1, col].set_ylabel("ratio")
        axes[1, col].legend(fontsize=7)
        axes[1, col].grid(alpha=0.3)

        axes[2, col].set_title(f"{level.upper()}: per-dim bias")
        axes[2, col].axhline(0.0, color="k", lw=0.5, ls="--")
        axes[2, col].set_xlabel("latent dim")
        axes[2, col].set_ylabel("mean error")
        axes[2, col].legend(fontsize=7)
        axes[2, col].grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig(out_path, dpi=100, bbox_inches="tight")
    plt.close()
    print(f"[plot] saved {out_path}")


def cmd_student_latent(ns: argparse.Namespace) -> int:
    """Entry point for the student_latent subcommand."""
    diag_dirs = [Path(p) for p in ns.diag_dirs]

    all_results: dict = {}
    for d in diag_dirs:
        name = d.parent.name if d.name == "latent_diagnostic" else d.name
        print(f"\n{'=' * 70}\n{name}\n{'=' * 70}")
        all_results[name] = {}
        for level in _SL_DR_LEVELS:
            res = _sl_load_level(d, level)
            if res is None:
                print(f"  [{level}] missing")
                continue
            l_hat, l_true = res
            T, E, D = l_hat.shape
            s = _sl_summarize(l_hat, l_true)
            all_results[name][level] = s

            print(f"\n  [{level}] T={T} E={E} D={D}  overall_MSE={s['overall_mse']:.5f}")
            print("    per-dim MSE:       " + " ".join(f"{v:.4f}" for v in s["per_dim_mse"]))
            print("    l_true env-var:    " + " ".join(f"{v:.4f}" for v in s["per_dim_envvar_true"]))
            print("    l_hat  env-var:    " + " ".join(f"{v:.4f}" for v in s["per_dim_envvar_hat"]))
            print("    l_true time-var:   " + " ".join(f"{v:.4f}" for v in s["per_dim_tvar_true"]))
            print("    l_hat  time-var:   " + " ".join(f"{v:.4f}" for v in s["per_dim_tvar_hat"]))
            print("    per-dim bias:      " + " ".join(f"{v:+.4f}" for v in s["per_dim_bias"]))

    # Save merged JSON
    out_dir = diag_dirs[0].parent if len(diag_dirs) == 1 else Path("/tmp")
    out_json = out_dir / "latent_analysis.json"
    with open(out_json, "w") as f:
        json.dump(all_results, f, indent=2)
    print(f"\n[json] saved {out_json}")

    # Plot comparison
    if len(diag_dirs) >= 1:
        out_png = out_dir / "latent_analysis.png"
        _sl_plot_comparison(diag_dirs, out_png)

    return 0
