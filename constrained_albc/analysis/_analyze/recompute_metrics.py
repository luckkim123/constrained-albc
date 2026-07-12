# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Pure-numpy metric core for the recompute subcommand (split from recompute.py).

No matplotlib, no JSON I/O. Importable on plain python3 so omx can call
_compute_enhanced_metrics / _process_run without booting Isaac Sim.

TODO(metric-drift): steady-state / tracking-error metric logic is duplicated
across THREE drifted implementations that are NOT byte-equivalent and were left
separate on purpose (merging risks changing metric values -- out of scope for the
structural refactor):
  - this module: _per_env_ss_stats / _compute_enhanced_metrics (per-env shape)
  - _eval_dr/metrics.py: att_ss_errors / lin_vel_ss_errors / yaw_ss_errors lists
  - compare.py: compute_level_metrics ("verbatim from compare_dr.py")
Reconciling them into one source is a separate, risk-bearing change requiring
before/after numeric equivalence checks on real eval npz.
"""

from __future__ import annotations

import os

import numpy as np

# DR constants sourced from common (single definition); aliases kept for callers
# that imported _RC_DR_LEVELS/_RC_DR_SCALE directly from this module.
from common import DR_LEVELS as _RC_DR_LEVELS  # type: ignore[import-not-found]  # noqa: E402
from common import (
    DR_SCALE as _RC_DR_SCALE,  # type: ignore[import-not-found]  # noqa: E402,F401  (re-exported for callers)
)

from ._shared import _load_npz

_AX_LIN = [("lin_vel_x", "target_vx", "vx"),
           ("lin_vel_y", "target_vy", "vy"),
           ("lin_vel_z", "target_vz", "vz")]
_AX_YAW = ("yaw_rate", "target_yaw_rate", "yaw")
_AX_ATT = [("actual_roll_deg",  "target_roll_deg",  "roll"),
           ("actual_pitch_deg", "target_pitch_deg", "pitch")]


# ---------------- Segment detection ----------------

# Target keys absent from the attitude_only eval npz (it tracks no linear velocity).
# Every target-key read below skips missing keys via `k in data`, so the recompute
# path degrades to attitude+yaw cleanly instead of KeyError. For the full-DOF teacher
# all keys are present -> behavior byte-identical.
def _find_segments(data: dict) -> list[tuple[int, int]]:
    n = len(data["time"])
    change = np.zeros(n, dtype=bool)
    for key in ["target_roll_deg", "target_pitch_deg",
                "target_vx", "target_vy", "target_vz", "target_yaw_rate"]:
        if key in data:
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
              for k in ("target_vx", "target_vy", "target_vz") if k in data)
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
                "target_vx","target_vy","target_vz","target_yaw_rate") if k in data)


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


def _discover_levels(eval_dir: str) -> list[str]:
    """Levels present as data_<level>.npz in eval_dir, ordered: the in-dist
    levels (_RC_DR_LEVELS order) first, then any EXTRA level (e.g. "ood") last.

    A dir holding only the 4 in-dist npz returns exactly _RC_DR_LEVELS, so a
    4-level summary stays byte-identical to the pre-OOD behavior. Extra levels
    (the GAP-1 "ood" level) are appended in sorted order after the in-dist ones.
    """
    try:
        present = {
            fn[len("data_"):-len(".npz")]
            for fn in os.listdir(eval_dir)
            if fn.startswith("data_") and fn.endswith(".npz")
        }
    except FileNotFoundError:
        return []
    ordered = [lvl for lvl in _RC_DR_LEVELS if lvl in present]
    extras = sorted(present - set(_RC_DR_LEVELS))
    return ordered + extras


def _compute_generalization_gap(summary: dict) -> dict | None:
    """gap[axis][field] = ood[axis][field] - hard[axis][field], in-dist vs OOD.

    Returns None unless BOTH "ood" and "hard" levels are present (so a 4-level,
    no-ood summary is unchanged). Differences only numeric scalars that exist in
    BOTH levels for the same axis; missing axes/fields or non-numeric values are
    silently skipped (never invented).
    """
    hard = summary.get("hard")
    ood = summary.get("ood")
    if not isinstance(hard, dict) or not isinstance(ood, dict):
        return None
    gap: dict[str, dict[str, float]] = {}
    for axis, ood_fields in ood.items():
        hard_fields = hard.get(axis)
        if not isinstance(ood_fields, dict) or not isinstance(hard_fields, dict):
            continue
        axis_gap: dict[str, float] = {}
        for field, ood_val in ood_fields.items():
            hard_val = hard_fields.get(field)
            if isinstance(ood_val, bool) or isinstance(hard_val, bool):
                continue
            if not isinstance(ood_val, (int, float)) or not isinstance(hard_val, (int, float)):
                continue
            axis_gap[field] = float(ood_val) - float(hard_val)
        if axis_gap:
            gap[axis] = axis_gap
    return gap


def _process_run(run_dir: str, data_subdir: str = "eval_dr") -> dict:
    eval_dir = os.path.join(run_dir, data_subdir)
    result = {}
    # Discover present levels so an extra "ood" level (GAP 1) is processed too;
    # a dir with only the 4 in-dist npz yields the identical 4-level result.
    for level in _discover_levels(eval_dir):
        path = os.path.join(eval_dir, f"data_{level}.npz")
        if not os.path.exists(path):
            print(f"  [WARN] {path} missing, skip"); continue
        result[level] = _compute_enhanced_metrics(path)
    return result


# ---------------- Pure-data extract helpers (used by plots) ----------------

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
