# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`eval_dr` subcommand: heavy-tail / sample-mean divergence metrics (merged from analyze_eval_dr.py)."""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

from ._shared import _load_npz

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
    """Replicate eval_dr.py static._pick_sample_env: median-attitude-error env."""
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
