# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Post-hoc analysis of constrained_full_albc eval outputs.

Subcommands:
    recompute  <run>            npz -> enhanced_summary.json (pipeline prerequisite)
    eval_dr    <runs> --labels  heavy-tail / sample-mean divergence metrics
    switching  <runs> --labels  summary_switching.json analysis
    table      <run>            Table 1 attitude SS error PNG

Pure Python (no Isaac Sim). Run with plain python3.

Usage:
    python3 scripts/analysis/analyze.py recompute logs/.../run_dir
    python3 scripts/analysis/analyze.py eval_dr 0 1 --labels A B
    python3 scripts/analysis/analyze.py table 0
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
from common import DR_LEVELS

# ===========================================================================
# Shared helpers
# ===========================================================================

def _load_npz(path: str) -> dict[str, np.ndarray]:
    """Load a .npz file and return as a plain dict."""
    return dict(np.load(path))



# ===========================================================================
# recompute subcommand
# (merged from recompute_eval_summary.py)
# ===========================================================================

# Local DR constants (recompute_eval_summary.py defined its own, not from common)
_RC_DR_LEVELS = ["none", "soft", "medium", "hard"]
_RC_DR_SCALE  = {"none": 0.0, "soft": 0.3, "medium": 0.6, "hard": 1.0}
_RC_DR_COLORS = {"none": "tab:blue", "soft": "tab:green", "medium": "tab:orange", "hard": "tab:red"}

_AX_LIN = [("lin_vel_x", "target_vx", "vx"),
           ("lin_vel_y", "target_vy", "vy"),
           ("lin_vel_z", "target_vz", "vz")]
_AX_YAW = ("yaw_rate", "target_yaw_rate", "yaw")
_AX_ATT = [("actual_roll_deg",  "target_roll_deg",  "roll"),
           ("actual_pitch_deg", "target_pitch_deg", "pitch")]

_AXIS_PALETTE = {"vx": "tab:blue", "vy": "tab:orange", "vz": "tab:green",
                 "roll": "tab:blue", "pitch": "tab:orange"}


# ---------------- Segment detection ----------------

def _find_segments(data: dict) -> list[tuple[int, int]]:
    n = len(data["time"])
    change = np.zeros(n, dtype=bool)
    for key in ["target_roll_deg", "target_pitch_deg",
                "target_vx", "target_vy", "target_vz", "target_yaw_rate"]:
        change[1:] |= np.abs(np.diff(data[key])) > 1e-6
    idx = np.where(change)[0]
    bounds = [0] + list(idx) + [n]
    return list(zip(bounds[:-1], bounds[1:]))


def _classify_segment(data: dict, s: int) -> str:
    if s == 0:
        return "init"
    eps = 1e-6
    att = (abs(data["target_roll_deg"][s]  - data["target_roll_deg"][s-1])  > eps or
           abs(data["target_pitch_deg"][s] - data["target_pitch_deg"][s-1]) > eps)
    lin = any(abs(data[k][s] - data[k][s-1]) > eps
              for k in ("target_vx", "target_vy", "target_vz"))
    yaw = abs(data["target_yaw_rate"][s] - data["target_yaw_rate"][s-1]) > eps
    if att and not lin and not yaw: return "attitude"
    if lin and not att and not yaw: return "lin_vel"
    if yaw and not att and not lin: return "yaw"
    if att or lin or yaw:           return "mixed"
    return "zero"


def _is_target_zero(data: dict, s: int) -> bool:
    eps = 1e-6
    return all(abs(data[k][s]) < eps for k in
               ("target_roll_deg","target_pitch_deg",
                "target_vx","target_vy","target_vz","target_yaw_rate"))


# ---------------- Per-env metric helpers (single axis, single segment) ----------------

def _per_env_peak_metrics(actual: np.ndarray, alive: np.ndarray,
                          prev_tgt: float, cur_tgt: float,
                          peak_window: int) -> dict:
    """Per-env overshoot and undershoot stats for a single axis segment.

    Returns both the env-to-env mean AND std so that dispersion across the
    64 envs is preserved (callers later average the per-segment stds across
    segments, mirroring how means are aggregated).
    """
    nan_out = {"os_env_mean": float("nan"), "os_env_std": float("nan"),
               "os_env_median": float("nan"),
               "os_env_q90": float("nan"), "us_env_mean": float("nan"),
               "us_env_std": float("nan"),
               "n_gt20": float("nan"), "n_gt40": float("nan"),
               "n_us_lt_minus20": float("nan")}
    step_mag = abs(cur_tgt - prev_tgt)
    if step_mag < 1e-4: return nan_out

    sign = 1.0 if cur_tgt > prev_tgt else -1.0
    w = min(peak_window, actual.shape[0])
    window = np.where(alive[:w], actual[:w], np.nan)
    peak_env = np.nanmax(window, axis=0) if sign > 0 else np.nanmin(window, axis=0)
    os_signed = sign * (peak_env - cur_tgt) / step_mag * 100.0
    valid = ~np.isnan(os_signed)
    if valid.sum() == 0: return nan_out
    os_clip = np.clip(os_signed[valid], 0.0, None)
    us_clip = np.clip(-os_signed[valid], 0.0, None)
    return {
        "os_env_mean":     float(np.mean(os_clip)),
        "os_env_std":      float(np.std(os_clip)),
        "os_env_median":   float(np.median(os_clip)),
        "os_env_q90":      float(np.percentile(os_clip, 90)),
        "us_env_mean":     float(np.mean(us_clip)),
        "us_env_std":      float(np.std(us_clip)),
        "n_gt20":          int(np.sum(os_clip > 20.0)),
        "n_gt40":          int(np.sum(os_clip > 40.0)),
        "n_us_lt_minus20": int(np.sum(os_signed[valid] < -20.0)),
    }


def _per_env_rise_time(actual: np.ndarray, alive: np.ndarray,
                       prev_tgt: float, cur_tgt: float,
                       dt: float) -> tuple[float, float]:
    """Per-env 10 -> 90 percent rise time.

    Returns (mean_across_envs, std_across_envs).
    """
    step_mag = abs(cur_tgt - prev_tgt)
    if step_mag < 1e-4: return float("nan"), float("nan")
    sign = 1.0 if cur_tgt > prev_tgt else -1.0
    thresh_10 = prev_tgt + sign * 0.1 * step_mag
    thresh_90 = prev_tgt + sign * 0.9 * step_mag

    _, N = actual.shape
    vals = np.where(alive, actual, np.nan)
    # crosses thresh_10 when sign * (v - thresh_10) >= 0
    crossed_10 = (sign * (vals - thresh_10)) >= 0
    crossed_90 = (sign * (vals - thresh_90)) >= 0
    rt = np.full(N, np.nan)
    for n in range(N):
        i10 = np.argmax(crossed_10[:, n]) if crossed_10[:, n].any() else None
        i90 = np.argmax(crossed_90[:, n]) if crossed_90[:, n].any() else None
        if i10 is not None and i90 is not None and i90 >= i10:
            rt[n] = (i90 - i10) * dt
    if not np.isfinite(rt).any():
        return float("nan"), float("nan")
    return float(np.nanmean(rt)), float(np.nanstd(rt))


def _per_env_ss_stats(actual: np.ndarray, alive: np.ndarray, cur_tgt: float
                      ) -> tuple[float, float, float, float]:
    """Per-env SS error and SS jitter over last 50 percent of the segment.

    Returns (ss_err_mean, ss_err_std, ss_jit_mean, ss_jit_std), each across envs.
    SS error per env: mean |actual - target| over last 50% of segment.
    SS jitter per env: std of |actual - target| over last 50% of segment.
    """
    ss_start = actual.shape[0] // 2
    ss_actual = actual[ss_start:]
    ss_alive = alive[ss_start:]
    ss_err_abs = np.abs(ss_actual - cur_tgt)
    masked = np.where(ss_alive, ss_err_abs, np.nan)
    per_env_mean = np.nanmean(masked, axis=0)
    per_env_std  = np.nanstd(masked, axis=0)
    has_mean = np.isfinite(per_env_mean).any()
    has_std  = np.isfinite(per_env_std).any()
    return (float(np.nanmean(per_env_mean)) if has_mean else float("nan"),
            float(np.nanstd(per_env_mean))  if has_mean else float("nan"),
            float(np.nanmean(per_env_std))  if has_std  else float("nan"),
            float(np.nanstd(per_env_std))   if has_std  else float("nan"))


# ---------------- Aggregate across segments ----------------

def _compute_enhanced_metrics(npz_path: str, peak_window_sec: float = 2.0) -> dict:
    """Compute per-axis per-env metrics for all 6 axes (roll, pitch, vx, vy, vz, yaw).

    Also computes attitude-norm SS error / jitter (on ||[roll_err, pitch_err]||).
    """
    data = _load_npz(npz_path)
    time = data["time"]
    dt = float(time[1] - time[0])
    peak_window = int(round(peak_window_sec / dt))
    segments = _find_segments(data)
    terminated = data["terminated"]
    alive_all = ~terminated

    axes = ("roll", "pitch", "vx", "vy", "vz", "yaw")
    # Dispersion (std-across-envs) is paired with each mean/jitter/rise_time so
    # that a reader can see how tightly the 64 envs cluster on each metric.
    # Aggregation rule: std is computed per-segment across envs, then averaged
    # across segments (matching the existing mean aggregation).
    keys = ("os_env_mean", "os_env_std",
            "os_env_median", "os_env_q90",
            "us_env_mean", "us_env_std",
            "n_gt20", "n_gt40", "n_us_lt_minus20",
            "rise_time", "rise_time_std",
            "ss_error", "ss_error_std",
            "ss_jitter", "ss_jitter_std")
    store = {ax: {k: [] for k in keys} for ax in axes}
    # Attitude-norm (combined roll+pitch) SS buffers (mean and env-spread std)
    att_norm_ss, att_norm_ss_std = [], []
    att_norm_jit, att_norm_jit_std = [], []

    for s, e in segments:
        kind = _classify_segment(data, s)
        if kind in ("init", "zero", "mixed"): continue
        if _is_target_zero(data, s):           continue
        alive_seg = alive_all[s:e]

        if kind == "attitude":
            ax_list = _AX_ATT
            # attitude-norm computation
            err_norm = np.sqrt(data["error_roll"][s:e]**2 + data["error_pitch"][s:e]**2)
            ss_start = (e - s) // 2
            masked = np.where(alive_seg[ss_start:], err_norm[ss_start:], np.nan)
            pe_mean = np.nanmean(masked, axis=0)
            pe_std  = np.nanstd(masked, axis=0)
            has_m = np.isfinite(pe_mean).any()
            has_s = np.isfinite(pe_std).any()
            att_norm_ss.append(float(np.nanmean(pe_mean)) if has_m else float("nan"))
            att_norm_ss_std.append(float(np.nanstd(pe_mean)) if has_m else float("nan"))
            att_norm_jit.append(float(np.nanmean(pe_std))  if has_s else float("nan"))
            att_norm_jit_std.append(float(np.nanstd(pe_std))  if has_s else float("nan"))
        elif kind == "lin_vel":
            ax_list = _AX_LIN
        elif kind == "yaw":
            ax_list = [_AX_YAW]
        else:
            continue

        for act_key, tgt_key, name in ax_list:
            cur  = float(data[tgt_key][s])
            prev = float(data[tgt_key][s-1]) if s > 0 else 0.0
            seg_actual = data[act_key][s:e]
            # OS / US distribution (dict already carries *_std)
            m = _per_env_peak_metrics(seg_actual, alive_seg, prev, cur, peak_window)
            # Rise time (mean + std across envs)
            rt_mean, rt_std = _per_env_rise_time(seg_actual, alive_seg, prev, cur, dt)
            m["rise_time"]     = rt_mean
            m["rise_time_std"] = rt_std
            # SS error and jitter (means + stds across envs)
            ss_err, ss_err_std, ss_jit, ss_jit_std = _per_env_ss_stats(seg_actual, alive_seg, cur)
            m["ss_error"]      = ss_err
            m["ss_error_std"]  = ss_err_std
            m["ss_jitter"]     = ss_jit
            m["ss_jitter_std"] = ss_jit_std
            for k, v in m.items():
                store[name][k].append(v)

    out = {}
    for ax, s in store.items():
        out[ax] = {k: (float(np.nanmean(v)) if len(v) and np.isfinite(v).any() else float("nan"))
                   for k, v in s.items()}
    out["att_norm"] = {
        "ss_error":      float(np.nanmean(att_norm_ss)) if att_norm_ss else float("nan"),
        "ss_error_std":  float(np.nanmean(att_norm_ss_std)) if att_norm_ss_std else float("nan"),
        "ss_jitter":     float(np.nanmean(att_norm_jit)) if att_norm_jit else float("nan"),
        "ss_jitter_std": float(np.nanmean(att_norm_jit_std)) if att_norm_jit_std else float("nan"),
    }
    out["survival_pct"] = float((~terminated[-1]).sum() / terminated.shape[1] * 100.0)
    return out


def _process_run(run_dir: str) -> dict:
    eval_dir = os.path.join(run_dir, "eval_dr")
    result = {}
    for level in _RC_DR_LEVELS:
        path = os.path.join(eval_dir, f"eval_{level}.npz")
        if not os.path.exists(path):
            print(f"  [WARN] {path} missing, skip"); continue
        result[level] = _compute_enhanced_metrics(path)
    return result


# ---------------- Plot helpers ----------------

def _level_xlabels():
    return [f"{lvl}\n(DR {int(_RC_DR_SCALE[lvl]*100)}%)" for lvl in _RC_DR_LEVELS]


def _extract(metrics: dict, axes: list[str], metric_key: str) -> dict[str, list[float]]:
    """Returns dict[axis_name] -> [val_per_level]."""
    out = {}
    for ax in axes:
        out[ax] = []
        for lv in _RC_DR_LEVELS:
            m = metrics.get(lv, {}).get(ax, {})
            out[ax].append(m.get(metric_key, float("nan")))
    return out


def _extract_scalar(metrics: dict, ax_name: str, metric_key: str) -> list[float]:
    return [metrics.get(lv, {}).get(ax_name, {}).get(metric_key, float("nan"))
            for lv in _RC_DR_LEVELS]


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
                          axes: list[str], ss_unit: str, title: str, filename: str) -> str:
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
    path = os.path.join(run_dir, "eval_dr", filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _plot_unified_single(run_dir: str, metrics: dict, *,
                         ax_name: str, ss_unit: str, title: str, filename: str) -> str:
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
    path = os.path.join(run_dir, "eval_dr", filename)
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


def _make_summary_att(run_dir: str, metrics: dict) -> str:
    """Attitude summary: roll+pitch grouped; SS shown per-axis (roll/pitch)."""
    return _plot_unified_grouped(
        run_dir, metrics,
        axes=["roll", "pitch"], ss_unit="deg",
        title="Attitude Summary (per-env metrics)",
        filename="summary_att.png")


def _make_summary_lin_vel(run_dir: str, metrics: dict) -> str:
    return _plot_unified_grouped(
        run_dir, metrics,
        axes=["vx", "vy", "vz"], ss_unit="m/s",
        title="Linear Velocity Summary (per-env metrics)",
        filename="summary_lin_vel.png")


def _make_summary_yaw(run_dir: str, metrics: dict) -> str:
    return _plot_unified_single(
        run_dir, metrics,
        ax_name="yaw", ss_unit="rad/s",
        title="Yaw Summary (per-env metrics)",
        filename="summary_yaw.png")


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


def _write_run_json(run_dir: str, metrics: dict) -> None:
    out = os.path.join(run_dir, "eval_dr", "enhanced_summary.json")
    with open(out, "w") as f:
        json.dump(metrics, f, indent=2,
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


def _process_and_write(run_dir: str) -> dict:
    print(f"\nProcessing: {run_dir}")
    metrics = _process_run(run_dir)
    _print_run_summary(os.path.basename(run_dir), metrics)
    _write_run_json(run_dir, metrics)
    if metrics:
        print(f"  Saved {_make_summary_att(run_dir, metrics)}")
        print(f"  Saved {_make_summary_lin_vel(run_dir, metrics)}")
        print(f"  Saved {_make_summary_yaw(run_dir, metrics)}")
    return metrics


def cmd_recompute(ns: argparse.Namespace) -> int:
    """Entry point for the recompute subcommand."""
    run_dirs = [d.strip().rstrip("/") for d in ns.run.split(",")]
    plot_path = ns.plot

    runs = {}
    for rd in run_dirs:
        metrics = _process_and_write(rd)
        runs[os.path.basename(rd)] = metrics

    if plot_path and len(runs) > 1:
        _multirun_comparison_plot(runs, plot_path)
    return 0


# ===========================================================================
# eval_dr subcommand
# (merged from analyze_eval_dr.py)
# ===========================================================================

_ED_AXES = ("roll", "pitch", "vx", "vy", "vz", "yaw")
_ED_DEFAULT_LEVELS = ("none", "soft", "medium", "hard")
# Unit scales reported per axis: {axis: (err_key, target_key, unit, threshold_default)}
_ED_AXIS_SPEC: dict[str, dict[str, Any]] = {
    "roll":  {"err": "error_roll",  "unit": "deg",  "thresh_key": "att"},
    "pitch": {"err": "error_pitch", "unit": "deg",  "thresh_key": "att"},
    "vx":    {"err": None, "actual": "lin_vel_x", "target": "target_vx",        "unit": "m/s", "thresh_key": "lv"},
    "vy":    {"err": None, "actual": "lin_vel_y", "target": "target_vy",        "unit": "m/s", "thresh_key": "lv"},
    "vz":    {"err": None, "actual": "lin_vel_z", "target": "target_vz",        "unit": "m/s", "thresh_key": "lv"},
    "yaw":   {"err": None, "actual": "yaw_rate",  "target": "target_yaw_rate",  "unit": "rad/s", "thresh_key": "yaw"},
}


def _ed_resolve_eval_dir(run: str) -> str:
    if os.path.isdir(os.path.join(run, "eval_dr")):
        return os.path.join(run, "eval_dr")
    if os.path.basename(run.rstrip("/")) == "eval_dr":
        return run
    if os.path.isdir(run) and any(f.startswith("eval_") and f.endswith(".npz") for f in os.listdir(run)):
        return run
    raise FileNotFoundError(f"no eval_dr found under {run}")


def _ed_load_level(eval_dir: str, level: str) -> dict[str, np.ndarray] | None:
    p = os.path.join(eval_dir, f"eval_{level}.npz")
    if not os.path.exists(p):
        return None
    return _load_npz(p)


def _ed_per_env_error(d: dict[str, np.ndarray], axis: str) -> np.ndarray | None:
    """Return (T, N_env) absolute error array for axis, or None if missing."""
    spec = _ED_AXIS_SPEC[axis]
    if spec.get("err") and spec["err"] in d:
        return np.abs(d[spec["err"]])
    actual_k, target_k = spec.get("actual"), spec.get("target")
    if actual_k is None or actual_k not in d or target_k not in d:
        return None
    actual = d[actual_k]
    target = d[target_k]
    if target.ndim == 1 and actual.ndim == 2:
        target = target[:, None]
    return np.abs(actual - target)


@dataclass
class _HeavyTail:
    ss_mean: float
    ss_std: float
    ss_max: float
    peak_mean: float
    peak_max: float
    pct_peak_gt_thresh: float  # percentage of envs with peak > threshold
    pct_ss_gt_hthresh: float   # percentage of envs with ss > half-threshold
    n_env: int


def _ed_compute_heavy_tail(err_abs: np.ndarray, threshold: float, window_frac: float = 0.2) -> _HeavyTail:
    """err_abs: (T, N). Compute per-env SS (mean over last window_frac) and peak."""
    T, N = err_abs.shape
    s = int((1 - window_frac) * T)
    ss = err_abs[s:].mean(axis=0)         # (N,)
    peak = err_abs[s:].max(axis=0)        # (N,)
    return _HeavyTail(
        ss_mean=float(ss.mean()),
        ss_std=float(ss.std()),
        ss_max=float(ss.max()),
        peak_mean=float(peak.mean()),
        peak_max=float(peak.max()),
        pct_peak_gt_thresh=float(100.0 * (peak > threshold).sum() / max(N, 1)),
        pct_ss_gt_hthresh=float(100.0 * (ss > threshold / 10.0).sum() / max(N, 1)),
        n_env=N,
    )


def _ed_pick_sample_env(d: dict[str, np.ndarray]) -> int | None:
    """Replicate eval_dr_fulldof._pick_sample_env: median-attitude-error env."""
    if "error_roll" not in d or "error_pitch" not in d:
        return None
    er = d["error_roll"]
    if er.ndim < 2 or er.shape[1] <= 1:
        return None
    att = np.sqrt(er**2 + d["error_pitch"] ** 2)
    per_env = np.nanmean(att, axis=0)
    median = np.nanmedian(per_env)
    return int(np.argmin(np.abs(per_env - median)))


def _ed_compute_sample_divergence(err_abs: np.ndarray, sample_idx: int, window_frac: float = 0.2) -> dict[str, float]:
    """Compare sample env trajectory vs mean trajectory (across envs).

    Returns L1 (MAE), L2 (RMSE), and L-inf (max abs diff) over last window.
    Also reports per-env rank of sample env in SS error (0=best, 1=worst).
    """
    T, N = err_abs.shape
    s = int((1 - window_frac) * T)
    mean_traj = err_abs[s:].mean(axis=1)           # (T,)
    sample_traj = err_abs[s:, sample_idx]          # (T,)
    diff = sample_traj - mean_traj
    ss_per_env = err_abs[s:].mean(axis=0)          # (N,)
    rank = float((ss_per_env < ss_per_env[sample_idx]).sum()) / max(N - 1, 1)
    return {
        "mae": float(np.abs(diff).mean()),
        "rmse": float(np.sqrt((diff**2).mean())),
        "linf": float(np.abs(diff).max()),
        "sample_ss": float(ss_per_env[sample_idx]),
        "mean_ss": float(mean_traj.mean()),
        "sample_rank_pct": 100.0 * rank,
    }


def _ed_compute_cross_axis_corr(d: dict[str, np.ndarray], window_frac: float = 0.2) -> dict[str, float]:
    """Per-env correlations between axes (axis decorrelation signal).

    Near 0 = envs that fail roll differ from envs that fail vz -> sample env divergence.
    Near +1 = same envs fail all axes together.
    """
    out: dict[str, float] = {}
    get = lambda ax: _ed_per_env_error(d, ax)
    ers = {ax: get(ax) for ax in _ED_AXES}

    def pe(arr: np.ndarray | None) -> np.ndarray | None:
        if arr is None:
            return None
        T = arr.shape[0]
        s = int((1 - window_frac) * T)
        return arr[s:].mean(axis=0)

    pe_ax = {ax: pe(ers[ax]) for ax in _ED_AXES}

    def rho(a: np.ndarray | None, b: np.ndarray | None) -> float:
        if a is None or b is None or a.std() < 1e-9 or b.std() < 1e-9:
            return 0.0
        return float(np.corrcoef(a, b)[0, 1])

    # Attitude vs linear velocity norm
    roll_pe, pitch_pe = pe_ax["roll"], pe_ax["pitch"]
    if roll_pe is not None and pitch_pe is not None:
        att = np.sqrt(roll_pe**2 + pitch_pe**2)
    else:
        att = None
    vx_pe, vy_pe, vz_pe = pe_ax["vx"], pe_ax["vy"], pe_ax["vz"]
    if vx_pe is not None and vy_pe is not None and vz_pe is not None:
        lv = np.sqrt(vx_pe**2 + vy_pe**2 + vz_pe**2)
    else:
        lv = None
    out["att_lv"] = rho(att, lv)

    # Pairwise of interest
    for a, b in [("roll", "vz"), ("roll", "vy"), ("pitch", "vy"), ("vx", "vy"), ("roll", "yaw"), ("pitch", "vx")]:
        out[f"{a}_{b}"] = rho(pe_ax[a], pe_ax[b])
    return out


def _ed_thresh_for(axis: str, t_att: float, t_lv: float, t_yaw: float) -> float:
    tk = _ED_AXIS_SPEC[axis]["thresh_key"]
    return {"att": t_att, "lv": t_lv, "yaw": t_yaw}[tk]


def _ed_analyze_run(eval_dir: str, levels: list[str], t_att: float, t_lv: float, t_yaw: float) -> dict:
    out: dict = {"eval_dir": eval_dir, "levels": {}}
    for lvl in levels:
        d = _ed_load_level(eval_dir, lvl)
        if d is None:
            continue
        sample_idx = _ed_pick_sample_env(d)
        lvl_out: dict = {"sample_idx": sample_idx, "axes": {}}
        for ax in _ED_AXES:
            err = _ed_per_env_error(d, ax)
            if err is None:
                continue
            th = _ed_thresh_for(ax, t_att, t_lv, t_yaw)
            ht = _ed_compute_heavy_tail(err, th)
            axis_out = {"threshold": th, "heavy_tail": ht.__dict__}
            if sample_idx is not None:
                axis_out["divergence"] = _ed_compute_sample_divergence(err, sample_idx)
            lvl_out["axes"][ax] = axis_out
        lvl_out["corr"] = _ed_compute_cross_axis_corr(d)
        out["levels"][lvl] = lvl_out
    return out


def _ed_print_report(results: list[tuple[str, dict]], levels: list[str]) -> None:
    """Multi-run side-by-side console tables."""
    labels = [lab for lab, _ in results]

    # ---- Heavy-tail table per level ----
    for lvl in levels:
        any_has = any(lvl in r["levels"] for _, r in results)
        if not any_has:
            continue
        print(f"\n=== HEAVY-TAIL | {lvl.upper()} | ss_mean (ss_max) | peak_mean (peak_max) | %env peak>th | n_env ===")
        hdr = f'{"axis":<6} ' + ' '.join(f'{lab:<30}' for lab in labels)
        print(hdr)
        for ax in _ED_AXES:
            row = [ax]
            for _, r in results:
                axes_d = r["levels"].get(lvl, {}).get("axes", {})
                if ax not in axes_d:
                    row.append('-'.ljust(30)); continue
                ht = axes_d[ax]["heavy_tail"]
                cell = (f"{ht['ss_mean']:.3f}({ht['ss_max']:.2f}) "
                        f"pk={ht['peak_mean']:.2f}({ht['peak_max']:.2f}) "
                        f"{ht['pct_peak_gt_thresh']:.0f}%")
                row.append(cell.ljust(30))
            print(f'{row[0]:<6} ' + ' '.join(row[1:]))

    # ---- Sample-mean divergence table per level ----
    for lvl in levels:
        any_has = any(lvl in r["levels"] for _, r in results)
        if not any_has:
            continue
        print(f"\n=== SAMPLE-MEAN DIVERGENCE | {lvl.upper()} | MAE / L-inf / sample_ss vs mean_ss / rank% ===")
        hdr = f'{"axis":<6} ' + ' '.join(f'{lab:<36}' for lab in labels)
        print(hdr)
        for ax in _ED_AXES:
            row = [ax]
            for _, r in results:
                axes_d = r["levels"].get(lvl, {}).get("axes", {})
                if ax not in axes_d or "divergence" not in axes_d[ax]:
                    row.append('-'.ljust(36)); continue
                dv = axes_d[ax]["divergence"]
                cell = (f"MAE={dv['mae']:.3f} Linf={dv['linf']:.2f} "
                        f"s/m={dv['sample_ss']:.3f}/{dv['mean_ss']:.3f} "
                        f"r={dv['sample_rank_pct']:.0f}%")
                row.append(cell.ljust(36))
            print(f'{row[0]:<6} ' + ' '.join(row[1:]))

    # ---- Cross-axis correlation table per level ----
    for lvl in levels:
        any_has = any(lvl in r["levels"] for _, r in results)
        if not any_has:
            continue
        print(f"\n=== AXIS DECORRELATION (per-env rho) | {lvl.upper()} ===")
        print('  rho~0 => axes solved on different env subsets (sample-mean divergence)')
        print('  rho~+1 => same envs fail all axes together')
        pairs = ["att_lv", "roll_vz", "roll_vy", "pitch_vy", "vx_vy", "roll_yaw", "pitch_vx"]
        hdr = f'{"run":<22} ' + ' '.join(f'{p:<11}' for p in pairs)
        print(hdr)
        for lab, r in results:
            corr = r["levels"].get(lvl, {}).get("corr", {})
            cells = [f'{corr.get(p, 0):+.3f}'.ljust(11) for p in pairs]
            print(f'{lab:<22} ' + ' '.join(cells))


def _ed_save_histogram(results: list[tuple[str, dict]], eval_dirs: list[str],
                       levels: list[str], axis: str, out_path: str) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    _, axes = plt.subplots(len(levels), len(results), figsize=(4*len(results), 2.8*len(levels)))
    if len(levels) == 1:
        axes = np.array([axes])
    if len(results) == 1:
        axes = axes[:, None]
    for ri, lvl in enumerate(levels):
        for ci, (lab, _) in enumerate(results):
            eval_dir = eval_dirs[ci]
            d = _ed_load_level(eval_dir, lvl)
            if d is None:
                axes[ri, ci].set_visible(False); continue
            err = _ed_per_env_error(d, axis)
            if err is None:
                axes[ri, ci].set_visible(False); continue
            T, N = err.shape; s = int(0.8*T)
            peak = err[s:].max(axis=0)
            axes[ri, ci].hist(peak, bins=15, color="tomato", edgecolor="k", alpha=0.7)
            axes[ri, ci].axvline(peak.mean(), color="navy", lw=1.8, label=f"mean={peak.mean():.2f}")
            axes[ri, ci].set_title(f"{lab}\n{lvl} peak |{axis}| (n={N})", fontsize=9)
            axes[ri, ci].legend(fontsize=7)
    plt.tight_layout()
    plt.savefig(out_path, dpi=80, bbox_inches="tight")
    print(f"[histogram] saved -> {out_path}")


def cmd_eval_dr(ns: argparse.Namespace) -> int:
    """Entry point for the eval_dr subcommand."""
    eval_dirs = [_ed_resolve_eval_dir(r) for r in ns.runs]
    labels = ns.labels if ns.labels else [
        os.path.basename(os.path.dirname(d.rstrip("/"))) or d for d in eval_dirs
    ]
    if len(labels) != len(eval_dirs):
        print("[warn] #labels != #runs, using run names", file=sys.stderr)
        labels = [os.path.basename(os.path.dirname(d.rstrip("/"))) or d for d in eval_dirs]

    results = []
    for lab, ed in zip(labels, eval_dirs):
        r = _ed_analyze_run(ed, ns.levels, ns.threshold_att, ns.threshold_lv, ns.threshold_yaw)
        results.append((lab, r))

    _ed_print_report(results, ns.levels)

    if ns.save_hist:
        _ed_save_histogram(results, eval_dirs, ns.levels, ns.hist_axis, ns.save_hist)
    return 0


# ===========================================================================
# switching subcommand
# (merged from analyze_dr_switching.py)
# ===========================================================================

def _sw_load_run(run_dir: str) -> dict:
    eval_dir = (os.path.join(run_dir, "eval_dr_switching")
                if not run_dir.rstrip("/").endswith("eval_dr_switching") else run_dir)
    summary_path = os.path.join(eval_dir, "switching_summary.json")
    with open(summary_path) as f:
        summary = json.load(f)
    data = {}
    for lvl in DR_LEVELS:
        p = os.path.join(eval_dir, f"eval_{lvl}.npz")
        if os.path.isfile(p):
            d = np.load(p, allow_pickle=True)
            data[lvl] = {k: d[k] for k in d.files}
    return {"summary": summary, "data": data}


def _sw_all_post_switch(run: dict, lvl: str, key: str) -> np.ndarray:
    per = run["summary"]["metrics"][lvl]["per_seg"]
    return np.concatenate([np.array(p[key]) for p in per[1:]])  # skip seg 0


def _sw_print_aggregate(runs: dict[str, dict], levels: list[str]) -> None:
    print(f"\n{'=' * 100}")
    print("AGGREGATE (segs 1..N, env×seg distribution — cascade PID, target xyz=0 rpy=0)")
    print(f"{'=' * 100}")
    print(f"{'level':<8} {'run':<14} "
          f"{'pos_peak':>10} {'pos_ss':>8} {'pos_max':>8} "
          f"{'roll_pk':>8} {'pitch_pk':>9} {'yaw_pk':>8} "
          f"{'roll_ss':>8} {'pitch_ss':>9} {'yaw_ss':>8}")
    for lvl in levels:
        for name, run in runs.items():
            pos_peak = _sw_all_post_switch(run, lvl, "pos_drift_peak")
            pos_ss = _sw_all_post_switch(run, lvl, "pos_drift_ss")
            rp = _sw_all_post_switch(run, lvl, "peak_roll_deg")
            pp = _sw_all_post_switch(run, lvl, "peak_pitch_deg")
            yp = _sw_all_post_switch(run, lvl, "peak_yaw_deg")
            rs = _sw_all_post_switch(run, lvl, "ss_roll_deg")
            ps = _sw_all_post_switch(run, lvl, "ss_pitch_deg")
            ys = _sw_all_post_switch(run, lvl, "ss_yaw_deg")
            print(f"{lvl:<8} {name:<14} "
                  f"{pos_peak.mean():8.4f}m {pos_ss.mean():7.4f}m {pos_peak.max():7.4f}m "
                  f"{rp.mean():7.3f}° {pp.mean():8.3f}° {yp.mean():7.3f}° "
                  f"{rs.mean():7.3f}° {ps.mean():8.3f}° {ys.mean():7.3f}°")
        print()


def _sw_heavy_tail_table(runs: dict[str, dict], levels: list[str]) -> None:
    print(f"\n{'=' * 100}")
    print("HEAVY-TAIL pos drift peak (env×seg, segs 1..N)")
    print(f"{'=' * 100}")
    print(f"{'level':<8} {'run':<14} {'p50':>8} {'p75':>8} {'p90':>8} {'p95':>8} {'p99':>8} {'max':>8} "
          f"{'%>0.1m':>7} {'%>0.2m':>7}")
    for lvl in levels:
        for name, run in runs.items():
            vals = _sw_all_post_switch(run, lvl, "pos_drift_peak")
            p50 = np.percentile(vals, 50); p75 = np.percentile(vals, 75)
            p90 = np.percentile(vals, 90); p95 = np.percentile(vals, 95)
            p99 = np.percentile(vals, 99); mx = vals.max()
            pct1 = 100 * (vals > 0.1).mean(); pct2 = 100 * (vals > 0.2).mean()
            print(f"{lvl:<8} {name:<14} {p50:7.4f}m {p75:7.4f}m {p90:7.4f}m {p95:7.4f}m "
                  f"{p99:7.4f}m {mx:7.4f}m {pct1:5.1f}% {pct2:5.1f}%")
        print()

    print(f"\n{'=' * 100}")
    print("HEAVY-TAIL attitude peak (env×seg, segs 1..N)")
    print(f"{'=' * 100}")
    print(f"{'level':<8} {'run':<14} {'axis':<6} {'p50':>7} {'p95':>7} {'p99':>7} {'max':>7} {'%>5°':>6} {'%>10°':>7}")
    for lvl in levels:
        for name, run in runs.items():
            for axk, axn in [("peak_roll_deg", "roll"), ("peak_pitch_deg", "pitch"), ("peak_yaw_deg", "yaw")]:
                v = _sw_all_post_switch(run, lvl, axk)
                print(f"{lvl:<8} {name:<14} {axn:<6} "
                      f"{np.percentile(v, 50):6.2f}° {np.percentile(v, 95):6.2f}° "
                      f"{np.percentile(v, 99):6.2f}° {v.max():6.2f}° "
                      f"{100*(v>5).mean():4.1f}% {100*(v>10).mean():5.1f}%")
        print()


def _sw_divergence_table(runs: dict[str, dict], levels: list[str]) -> None:
    names = list(runs.keys())
    if len(names) != 2:
        return
    a, b = names
    print(f"\n{'=' * 90}")
    print("ENV-LEVEL AGREEMENT (same DR seed — same env is worst in pos drift?)")
    print(f"{'=' * 90}")
    print(f"{'level':<8} {'worst_A':>10} {'worst_B':>10} {'A_peak':>10} {'B_peak':>10} {'spearman_rho':>14}")
    for lvl in levels:
        n_envs = runs[a]["summary"]["config"]["num_envs"]
        per_a = runs[a]["summary"]["metrics"][lvl]["per_seg"][1:]
        per_b = runs[b]["summary"]["metrics"][lvl]["per_seg"][1:]
        env_peak_a = np.zeros(n_envs)
        env_peak_b = np.zeros(n_envs)
        for p in per_a:
            env_peak_a = np.maximum(env_peak_a, np.array(p["pos_drift_peak"]))
        for p in per_b:
            env_peak_b = np.maximum(env_peak_b, np.array(p["pos_drift_peak"]))
        wa, wb = int(np.argmax(env_peak_a)), int(np.argmax(env_peak_b))
        ra, rb = np.argsort(np.argsort(env_peak_a)), np.argsort(np.argsort(env_peak_b))
        rho = np.corrcoef(ra, rb)[0, 1]
        print(f"{lvl:<8} {wa:>10} {wb:>10} {env_peak_a[wa]:8.4f}m {env_peak_b[wb]:8.4f}m {rho:+12.3f}")


def _sw_per_seg_table(runs: dict[str, dict], levels: list[str]) -> None:
    for lvl in levels:
        print(f"\n{'=' * 100}\nDR LEVEL: {lvl.upper()}  (per-seg pos_peak / pos_ss / max_att_peak | env mean)\n{'=' * 100}")
        names = list(runs.keys())
        max_segs = max(len(r["summary"]["metrics"][lvl]["per_seg"]) for r in runs.values())
        print(f"{'seg':>4}  " + " | ".join(f"{n:<38}" for n in names))
        for seg in range(max_segs):
            row = f"{seg:>4}  "
            parts = []
            for n in names:
                per = runs[n]["summary"]["metrics"][lvl]["per_seg"]
                if seg >= len(per):
                    parts.append(f"{'-':<38}"); continue
                p = per[seg]
                pp = np.mean(p["pos_drift_peak"])
                ps = np.mean(p["pos_drift_ss"])
                att = max(np.mean(p["peak_roll_deg"]),
                          np.mean(p["peak_pitch_deg"]),
                          np.mean(p["peak_yaw_deg"]))
                parts.append(f"pos_pk={pp:.4f}m pos_ss={ps:.4f}m att_pk={att:.2f}°  ")
            print(row + " | ".join(parts))


def cmd_switching(ns: argparse.Namespace) -> int:
    """Entry point for the switching subcommand."""
    labels = ns.labels or [os.path.basename(r.rstrip("/")) for r in ns.runs]
    runs = {labels[i]: _sw_load_run(ns.runs[i]) for i in range(len(ns.runs))}

    _sw_print_aggregate(runs, ns.levels)
    _sw_heavy_tail_table(runs, ns.levels)
    _sw_divergence_table(runs, ns.levels)
    _sw_per_seg_table(runs, ns.levels)
    return 0


# ===========================================================================
# table subcommand
# (merged from table_eval_dr_attitude.py)
# ===========================================================================

# Default hardcoded paths (preserved verbatim from original)
_TABLE_TDC = "/workspace/isaaclab/logs/rsl_rl/full_dof_tdc/classical_baseline/eval_dr/enhanced_summary.json"
_TABLE_V5  = "/workspace/isaaclab/logs/rsl_rl/full_dof_ablation/2026-04-22_01-41-00_ablation_v5_pureppo/eval_dr/enhanced_summary.json"
_TABLE_R13 = "/workspace/isaaclab/logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/eval_dr/enhanced_summary.json"
# Output path is written to <run>/table1_eval_dr_attitude.png (set at runtime via cmd_table)


def cmd_table(ns: argparse.Namespace) -> int:
    """Entry point for the table subcommand.

    Renders Table 1 (attitude SS error under DR) as a paper-style PNG.
    Uses the hardcoded TDC/V5/r13_A paths from the original script unless
    overridden via --tdc, --v5, --r13 flags. The <run> positional sets the
    output directory (table1_eval_dr_attitude.png is written there).
    """
    import matplotlib as mpl
    import matplotlib.pyplot as plt

    tdc_path = ns.tdc if ns.tdc else _TABLE_TDC
    v5_path  = ns.v5  if ns.v5  else _TABLE_V5
    r13_path = ns.r13 if ns.r13 else _TABLE_R13

    tdc = json.load(open(tdc_path))
    v5  = json.load(open(v5_path))
    r13 = json.load(open(r13_path))

    levels = ["none", "soft", "medium", "hard"]
    controllers = [
        ("TDC+PD",                  tdc, "#C74E47"),
        ("PurePPO (no enc, no IPO)", v5,  "#2E7D32"),
        ("r13_A (RL+Encoder)",       r13, "#1565C0"),
    ]

    def cell(d, axis, key="ss_error"):
        return d[axis][key], d[axis][key + "_std"]

    # Build table rows
    header_top = ["DR", "Controller", "Roll  SS err (deg)", "Pitch  SS err (deg)"]
    rows, best_mask = [], []  # best_mask[i] = list of bool per cell in row (for bold)
    for lvl in levels:
        # Determine best (min mean) per axis across controllers for this DR
        roll_means = [cell(d[lvl], "roll")[0] for _, d, _ in controllers]
        pitch_means = [cell(d[lvl], "pitch")[0] for _, d, _ in controllers]
        best_roll_idx = roll_means.index(min(roll_means))
        best_pitch_idx = pitch_means.index(min(pitch_means))

        for ci, (name, d, _) in enumerate(controllers):
            roll_m, roll_s = cell(d[lvl], "roll")
            pitch_m, pitch_s = cell(d[lvl], "pitch")
            roll_str = f"{roll_m:.2f} +- {roll_s:.2f}"
            pitch_str = f"{pitch_m:.2f} +- {pitch_s:.2f}"
            # Only first row of each DR block prints the DR label
            dr_cell = lvl if ci == 0 else ""
            rows.append([dr_cell, name, roll_str, pitch_str])
            best_mask.append([False, False, ci == best_roll_idx, ci == best_pitch_idx])

    # Render
    mpl.rcParams["font.family"] = "serif"
    mpl.rcParams["mathtext.fontset"] = "stix"
    fig_w, fig_h = 9.5, 0.50 + 0.44 * (len(rows) + 1)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")

    table = ax.table(
        cellText=[header_top] + rows,
        cellLoc="center",
        colWidths=[0.08, 0.35, 0.27, 0.27],
        loc="center",
        edges="open",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(11)
    table.scale(1.0, 1.55)

    n_rows = len(rows) + 1  # incl. header
    for (r, c), cell_obj in table.get_celld().items():
        cell_obj.set_edgecolor("none")
        cell_obj.set_linewidth(0)
        # Top rule above header, midrule below header, bottom rule at bottom
        if r == 0:
            cell_obj.set_text_props(weight="bold")
            cell_obj.visible_edges = "TB"
            cell_obj.set_linewidth(1.2)
        elif r == n_rows - 1:
            cell_obj.visible_edges = "B"
            cell_obj.set_linewidth(1.2)
        # Bold best values
        if r > 0 and best_mask[r - 1][c]:
            cell_obj.set_text_props(weight="bold")
        # DR block separators: draw a light line above first row of each block (ci==0)
        if r > 0 and (r - 1) % 3 == 0 and r != 1:
            cell_obj.visible_edges = "T"
            cell_obj.set_linewidth(0.5)
            cell_obj.set_edgecolor("#AAAAAA")

    # Title
    fig.suptitle(
        "Table 1. Attitude steady-state error under domain randomization\n"
        "(deg, mean +- std across 64 environments; lower is better)",
        fontsize=11, y=0.98, weight="bold",
    )

    # Caveat note
    fig.text(
        0.5, 0.02,
        "Note: TDC uses single-step DLS IK (compute-matched fairness). Bold = best per DR level per axis.",
        ha="center", fontsize=8.5, style="italic", color="#555555",
    )

    fig.tight_layout(rect=(0, 0.04, 1, 0.94))

    # Determine output path
    run_dir = ns.run.rstrip("/")
    out_path = os.path.join(run_dir, "table1_eval_dr_attitude.png")
    os.makedirs(run_dir, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight", facecolor="white")
    print(f"Saved: {out_path}")
    return 0


# ===========================================================================
# Argument parser wiring
# ===========================================================================

def build_parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = top.add_subparsers(dest="mode", required=True)

    # -- recompute --
    p_rc = sub.add_parser(
        "recompute",
        help="npz -> enhanced_summary.json (pipeline prerequisite)",
        description="Read eval_{none,soft,medium,hard}.npz from <run>/eval_dr/ and produce enhanced_summary.json.",
    )
    p_rc.add_argument(
        "run",
        help="Run directory (or comma-separated list for multi-run comparison)",
    )
    p_rc.add_argument(
        "--plot",
        metavar="PATH",
        default=None,
        help="Save multi-run comparison PNG to PATH (requires 2+ runs)",
    )
    p_rc.set_defaults(func=cmd_recompute)

    # -- eval_dr --
    p_ed = sub.add_parser(
        "eval_dr",
        help="heavy-tail / sample-mean divergence metrics",
        description="Analyze eval_dr npz outputs: heavy-tail, sample-mean divergence, cross-axis correlation.",
    )
    p_ed.add_argument("runs", nargs="+", help="run dirs or eval_dr dirs")
    p_ed.add_argument("--labels", nargs="+", help="labels for each run")
    p_ed.add_argument("--levels", nargs="+", default=list(_ED_DEFAULT_LEVELS))
    p_ed.add_argument("--threshold-att", type=float, default=20.0, help="att threshold deg (default 20)")
    p_ed.add_argument("--threshold-lv",  type=float, default=0.5,  help="lin_vel threshold m/s (default 0.5)")
    p_ed.add_argument("--threshold-yaw", type=float, default=0.5,  help="yaw rate threshold rad/s (default 0.5)")
    p_ed.add_argument("--save-hist", metavar="PATH", help="save per-env peak histogram to PATH (axis=roll)")
    p_ed.add_argument("--hist-axis", default="roll", choices=list(_ED_AXES))
    p_ed.set_defaults(func=cmd_eval_dr)

    # -- switching --
    p_sw = sub.add_parser(
        "switching",
        help="summary_switching.json analysis",
        description="Analyze eval_dr_switching outputs (cascade PID, target xyz=0 rpy=0).",
    )
    p_sw.add_argument("runs", nargs="+", help="Run dirs or eval_dr_switching dirs")
    p_sw.add_argument("--labels", nargs="+", default=None)
    p_sw.add_argument("--levels", nargs="+", default=DR_LEVELS)
    p_sw.set_defaults(func=cmd_switching)

    # -- table --
    p_tb = sub.add_parser(
        "table",
        help="Table 1 attitude SS error PNG",
        description=(
            "Render Table 1 (attitude SS error under DR) as paper-style PNG. "
            "The <run> positional is the output directory. "
            "Input JSON paths default to the original hardcoded run locations."
        ),
    )
    p_tb.add_argument(
        "run",
        help="Output directory where table1_eval_dr_attitude.png is written",
    )
    p_tb.add_argument("--tdc", default=None, metavar="PATH",
                      help="Path to TDC enhanced_summary.json (overrides default)")
    p_tb.add_argument("--v5",  default=None, metavar="PATH",
                      help="Path to PurePPO enhanced_summary.json (overrides default)")
    p_tb.add_argument("--r13", default=None, metavar="PATH",
                      help="Path to r13_A enhanced_summary.json (overrides default)")
    p_tb.set_defaults(func=cmd_table)

    return top


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    return ns.func(ns)


if __name__ == "__main__":
    raise SystemExit(main())
