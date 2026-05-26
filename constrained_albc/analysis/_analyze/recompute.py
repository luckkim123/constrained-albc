# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`recompute` subcommand: npz -> summary.json (merged from recompute_eval_summary.py)."""

from __future__ import annotations

import argparse
import json
import os

import numpy as np

from ._shared import _load_npz

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


def _process_run(run_dir: str, data_subdir: str = "eval_dr") -> dict:
    eval_dir = os.path.join(run_dir, data_subdir)
    result = {}
    for level in _RC_DR_LEVELS:
        path = os.path.join(eval_dir, f"data_{level}.npz")
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


def _process_and_write(run_dir: str, data_subdir: str = "eval_dr") -> dict:
    """Recompute per-env metrics from <run_dir>/<data_subdir>/data_*.npz and write
    summary.json + summary_*.png into the same dir.

    data_subdir defaults to "eval_dr" for the legacy `analyze.py recompute` layout.
    The run-id-tree static eval passes the actual timestamped data folder name
    (e.g. "static_2026-05-26_04-59-47") so outputs land beside the .npz files
    instead of a non-existent eval_dr/ sibling.
    """
    print(f"\nProcessing: {run_dir} (data in {data_subdir}/)")
    metrics = _process_run(run_dir, data_subdir=data_subdir)
    _print_run_summary(os.path.basename(run_dir), metrics)
    _write_run_json(run_dir, metrics, data_subdir=data_subdir)
    if metrics:
        print(f"  Saved {_make_summary_att(run_dir, metrics, data_subdir=data_subdir)}")
        print(f"  Saved {_make_summary_lin_vel(run_dir, metrics, data_subdir=data_subdir)}")
        print(f"  Saved {_make_summary_yaw(run_dir, metrics, data_subdir=data_subdir)}")
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
