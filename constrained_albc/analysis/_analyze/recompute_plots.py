# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Matplotlib plot helpers for the recompute subcommand (split from recompute.py)."""

from __future__ import annotations

import json
import os

import numpy as np

from .recompute_metrics import (
    _RC_DR_LEVELS,
    _RC_DR_SCALE,
    _extract,
    _extract_scalar,
)

_RC_DR_COLORS = {"none": "tab:blue", "soft": "tab:green", "medium": "tab:orange", "hard": "tab:red"}
_AXIS_PALETTE = {"vx": "tab:blue", "vy": "tab:orange", "vz": "tab:green",
                 "roll": "tab:blue", "pitch": "tab:orange"}


# ---------------- Plot helpers ----------------

def _level_xlabels():
    return [f"{lvl}\n(DR {int(_RC_DR_SCALE[lvl]*100)}%)" for lvl in _RC_DR_LEVELS]


def _bars_single(ax, values: list[float], ylabel: str, title: str, *,
                 ref_line: float | None = None):
    xs = np.arange(len(_RC_DR_LEVELS))
    ax.bar(xs, values, color=[_RC_DR_COLORS[lv] for lv in _RC_DR_LEVELS],
           edgecolor="black", linewidth=0.4, alpha=0.85)
    ax.set_xticks(xs); ax.set_xticklabels(_level_xlabels(), fontsize=8)
    ax.set_ylabel(ylabel); ax.grid(True, alpha=0.3)
    ax.set_title(title, fontsize=10)
    if ref_line is not None:
        ax.axhline(ref_line, color="red", ls=":", lw=0.8, alpha=0.7)


def _bars_grouped(ax, per_axis: dict[str, list[float]], ylabel: str, title: str, *,
                  ref_line: float | None = None):
    names = list(per_axis.keys())
    n = len(names)
    xs = np.arange(len(_RC_DR_LEVELS)); w = 0.8 / n
    for i, ax_n in enumerate(names):
        offset = (i - (n - 1) / 2) * w
        ax.bar(xs + offset, per_axis[ax_n], w, label=ax_n,
               color=_AXIS_PALETTE.get(ax_n),
               edgecolor="black", linewidth=0.4, alpha=0.9)
    ax.set_xticks(xs); ax.set_xticklabels(_level_xlabels(), fontsize=8)
    ax.set_ylabel(ylabel); ax.grid(True, alpha=0.3)
    ax.set_title(title, fontsize=10)
    ax.legend(fontsize=8, loc="best")
    if ref_line is not None:
        ax.axhline(ref_line, color="red", ls=":", lw=0.8, alpha=0.7)


# ---------------- Unified 3x2 summary plots ----------------

def _plot_unified_grouped(run_dir: str, metrics: dict, *,
                          axes: list[str], ss_unit: str, title: str, filename: str,
                          data_subdir: str = "eval_dr") -> str:
    """Generic 3x2 summary plot for a group with multiple axes (att, lin_vel)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surv = [metrics.get(lv, {}).get("survival_pct", float("nan")) for lv in _RC_DR_LEVELS]

    ss_err = _extract(metrics, axes, "ss_error")
    ss_jit = _extract(metrics, axes, "ss_jitter")
    rise   = _extract(metrics, axes, "rise_time")
    os_os  = _extract(metrics, axes, "os_env_mean")
    us_us  = _extract(metrics, axes, "us_env_mean")

    fig, axs = plt.subplots(3, 2, figsize=(13, 12))
    _bars_grouped(axs[0, 0], ss_err, ss_unit, f"SS Error ({ss_unit})")
    _bars_grouped(axs[0, 1], ss_jit, ss_unit, f"SS Jitter (std, {ss_unit})")
    _bars_grouped(axs[1, 0], rise,    "s",    "Rise Time (10 -> 90%)")
    _bars_grouped(axs[1, 1], os_os,   "%",    "Overshoot (per-env mean)", ref_line=20)
    _bars_grouped(axs[2, 0], us_us,   "%",    "Undershoot (per-env mean, target miss)")
    _bars_single(axs[2, 1], surv,     "%",    "Survival (env alive at eval end)", ref_line=100)

    fig.suptitle(title, fontsize=13)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    path = os.path.join(run_dir, data_subdir, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_unified_single(run_dir: str, metrics: dict, *,
                         ax_name: str, ss_unit: str, title: str, filename: str,
                         data_subdir: str = "eval_dr") -> str:
    """Generic 3x2 summary plot for a single-axis group (yaw)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    surv   = [metrics.get(lv, {}).get("survival_pct", float("nan")) for lv in _RC_DR_LEVELS]
    ss_err = _extract_scalar(metrics, ax_name, "ss_error")
    ss_jit = _extract_scalar(metrics, ax_name, "ss_jitter")
    rise   = _extract_scalar(metrics, ax_name, "rise_time")
    os_os  = _extract_scalar(metrics, ax_name, "os_env_mean")
    us_us  = _extract_scalar(metrics, ax_name, "us_env_mean")

    fig, axs = plt.subplots(3, 2, figsize=(13, 12))
    _bars_single(axs[0, 0], ss_err, ss_unit, f"SS Error ({ss_unit})")
    _bars_single(axs[0, 1], ss_jit, ss_unit, f"SS Jitter (std, {ss_unit})")
    _bars_single(axs[1, 0], rise,    "s",    "Rise Time (10 -> 90%)")
    _bars_single(axs[1, 1], os_os,   "%",    "Overshoot (per-env mean)", ref_line=20)
    _bars_single(axs[2, 0], us_us,   "%",    "Undershoot (per-env mean, target miss)")
    _bars_single(axs[2, 1], surv,    "%",    "Survival (env alive at eval end)", ref_line=100)

    fig.suptitle(title, fontsize=13)
    plt.tight_layout(rect=(0, 0, 1, 0.97))
    path = os.path.join(run_dir, data_subdir, filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _make_summary_att(run_dir: str, metrics: dict, data_subdir: str = "eval_dr") -> str:
    """Attitude summary: roll+pitch grouped; SS shown per-axis (roll/pitch)."""
    return _plot_unified_grouped(
        run_dir, metrics,
        axes=["roll", "pitch"], ss_unit="deg",
        title="Attitude Summary (per-env metrics)",
        filename="summary_attitude.png", data_subdir=data_subdir)


def _make_summary_lin_vel(run_dir: str, metrics: dict, data_subdir: str = "eval_dr") -> str:
    return _plot_unified_grouped(
        run_dir, metrics,
        axes=["vx", "vy", "vz"], ss_unit="m/s",
        title="Linear Velocity Summary (per-env metrics)",
        filename="summary_linvel.png", data_subdir=data_subdir)


def _make_summary_yaw(run_dir: str, metrics: dict, data_subdir: str = "eval_dr") -> str:
    return _plot_unified_single(
        run_dir, metrics,
        ax_name="yaw", ss_unit="rad/s",
        title="Yaw Summary (per-env metrics)",
        filename="summary_yaw.png", data_subdir=data_subdir)


# ---------------- Text + JSON outputs ----------------

def _print_run_summary(run_name: str, metrics: dict) -> None:
    print(f"\n{'='*120}")
    print(f"Enhanced summary: {run_name}")
    print("="*120)
    print(f"{'Level':<8} {'Axis':<6} "
          f"{'SS':>9} {'Jit':>7} {'RT(s)':>7} "
          f"{'OS':>6} {'US':>6} {'OS_med':>7} {'OS_q90':>7} {'n>20%':>6}")
    print("-"*120)
    for level in _RC_DR_LEVELS:
        if level not in metrics: continue
        for ax in ("roll","pitch","vx","vy","vz","yaw"):
            m = metrics[level][ax]
            print(f"{level:<8} {ax:<6} "
                  f"{m['ss_error']:>9.3f} {m['ss_jitter']:>7.3f} {m['rise_time']:>7.3f} "
                  f"{m['os_env_mean']:>6.1f} {m['us_env_mean']:>6.1f} "
                  f"{m['os_env_median']:>7.1f} {m['os_env_q90']:>7.1f} {m['n_gt20']:>6.1f}")
        print()


def _write_run_json(run_dir: str, metrics: dict, data_subdir: str = "eval_dr") -> None:
    out = os.path.join(run_dir, data_subdir, "summary.json")
    # GAP 1 (2c): attach generalization_gap = ood - hard when an OOD level is
    # present. A 4-level (no-ood) summary gains NO new key (byte-identical). Build
    # a shallow copy so the caller's in-memory metrics dict (used for plotting)
    # is not mutated.
    from .recompute_metrics import _compute_generalization_gap

    payload = metrics
    gap = _compute_generalization_gap(metrics)
    if gap:
        payload = dict(metrics)
        payload["generalization_gap"] = gap
    with open(out, "w") as f:
        json.dump(payload, f, indent=2,
                  default=lambda o: None if (isinstance(o, float) and np.isnan(o)) else o)
    print(f"  Saved {out}")


def _multirun_comparison_plot(runs: dict, output_path: str) -> None:
    """Single-figure 4-way comparison at hard DR across 6 axes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    axes_order = ("roll", "pitch", "vx", "vy", "vz", "yaw")
    colors = {"Control": "black", "Exp-L1": "tab:red", "Tanh": "tab:blue", "Arctan": "tab:green"}
    fig, ax = plt.subplots(1, 6, figsize=(22, 5))
    x_run = np.arange(len(runs)); names = list(runs); w = 0.25
    for i, axn in enumerate(axes_order):
        for j, n in enumerate(names):
            m = runs[n].get("hard", {}).get(axn, {})
            ax[i].bar(j - w, m.get("os_env_mean",   0), w, color=colors.get(n, "grey"), alpha=1.0)
            ax[i].bar(j,     m.get("us_env_mean",   0), w, color=colors.get(n, "grey"), alpha=0.55)
            ax[i].bar(j + w, m.get("os_env_q90",    0), w, color=colors.get(n, "grey"), alpha=0.25)
        ax[i].axhline(20, color="red", ls=":", lw=1)
        ax[i].set_xticks(x_run); ax[i].set_xticklabels(names, rotation=30)
        ax[i].set_title(f"{axn} (hard DR)")
        if i == 0: ax[i].set_ylabel("% (OS mean | US mean | OS q90)")
        ax[i].grid(alpha=0.3)
    fig.suptitle("Per-env @ hard DR: OS mean (solid) | US mean (mid) | OS q90 (light). Red = 20%.",
                 fontsize=12)
    plt.tight_layout(rect=(0, 0, 1, 0.98))
    plt.savefig(output_path, dpi=110, bbox_inches="tight"); plt.close()
    print(f"  Saved {output_path}")


def _process_and_write(run_dir: str, data_subdir: str = "eval_dr") -> dict:
    """Recompute per-env metrics from <run_dir>/<data_subdir>/data_*.npz and write
    summary.json + summary_*.png into the same dir.

    data_subdir defaults to "eval_dr" for the legacy `analyze.py recompute` layout.
    The run-id-tree static eval passes the actual timestamped data folder name
    (e.g. "static_2026-05-26_04-59-47") so outputs land beside the .npz files
    instead of a non-existent eval_dr/ sibling.
    """
    from .recompute_metrics import _process_run

    print(f"\nProcessing: {run_dir} (data in {data_subdir}/)")
    metrics = _process_run(run_dir, data_subdir=data_subdir)
    _print_run_summary(os.path.basename(run_dir), metrics)
    _write_run_json(run_dir, metrics, data_subdir=data_subdir)
    if metrics:
        print(f"  Saved {_make_summary_att(run_dir, metrics, data_subdir=data_subdir)}")
        print(f"  Saved {_make_summary_lin_vel(run_dir, metrics, data_subdir=data_subdir)}")
        print(f"  Saved {_make_summary_yaw(run_dir, metrics, data_subdir=data_subdir)}")
    return metrics
