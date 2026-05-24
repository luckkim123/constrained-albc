#!/usr/bin/env python3
"""Post-hoc analysis of eval_dr / eval_dr_fulldof output.

Loads `<run_dir>/eval_dr/eval_{level}.npz` for each DR level and computes three
families of metrics that `enhanced_summary.json` alone does not reveal:

1. Heavy-tail: per-env SS error + per-env peak error, % env exceeding threshold.
   Mean ss_error low yet a few envs blowing up is the distributional failure
   mode that summary's mean+-std hides.

2. Sample-mean divergence: sample env (median-att) trajectory vs mean trajectory.
   Gives the exact number behind the visual "dashed vs solid" gap in tracking
   PNGs. Large divergence on an axis signals axis-wise decorrelation -- policy
   solves axes on different env subsets.

3. Cross-axis env-level correlation: rho(roll err, vz err), rho(att, lv_norm)
   per-DR-level. rho near 0 means axes are solved on different env subsets
   (decorrelation); rho near +1 means one env fails all axes together.

Usage:
    python3 analyze_eval_dr.py <run_dir> [<run_dir> ...] \
        [--labels L1 L2 ...] [--threshold-att 20] [--threshold-lv 0.5] \
        [--save-plot <png>] [--levels none soft medium hard]

`run_dir` may be either the training run dir (contains `eval_dr/`) or the
`eval_dr/` dir itself. Accepts eval_dr from eval_dr.py or eval_dr_fulldof.py.
"""
from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from typing import Any

import numpy as np

# ---------------------------------------------------------------------- config
AXES = ("roll", "pitch", "vx", "vy", "vz", "yaw")
DEFAULT_LEVELS = ("none", "soft", "medium", "hard")
ATT_AXES = ("roll", "pitch")
LV_AXES = ("vx", "vy", "vz")
# Unit scales reported per axis: {axis: (err_key, target_key, unit, threshold_default)}
AXIS_SPEC: dict[str, dict[str, Any]] = {
    "roll":  {"err": "error_roll",  "unit": "deg",  "thresh_key": "att"},
    "pitch": {"err": "error_pitch", "unit": "deg",  "thresh_key": "att"},
    "vx":    {"err": None, "actual": "lin_vel_x", "target": "target_vx",        "unit": "m/s", "thresh_key": "lv"},
    "vy":    {"err": None, "actual": "lin_vel_y", "target": "target_vy",        "unit": "m/s", "thresh_key": "lv"},
    "vz":    {"err": None, "actual": "lin_vel_z", "target": "target_vz",        "unit": "m/s", "thresh_key": "lv"},
    "yaw":   {"err": None, "actual": "yaw_rate",  "target": "target_yaw_rate",  "unit": "rad/s", "thresh_key": "yaw"},
}


# ---------------------------------------------------------------------- loader
def resolve_eval_dir(run: str) -> str:
    if os.path.isdir(os.path.join(run, "eval_dr")):
        return os.path.join(run, "eval_dr")
    if os.path.basename(run.rstrip("/")) == "eval_dr":
        return run
    if os.path.isdir(run) and any(f.startswith("eval_") and f.endswith(".npz") for f in os.listdir(run)):
        return run
    raise FileNotFoundError(f"no eval_dr found under {run}")


def load_level(eval_dir: str, level: str) -> dict[str, np.ndarray] | None:
    p = os.path.join(eval_dir, f"eval_{level}.npz")
    if not os.path.exists(p):
        return None
    return dict(np.load(p))


def per_env_error(d: dict[str, np.ndarray], axis: str) -> np.ndarray | None:
    """Return (T, N_env) absolute error array for axis, or None if missing."""
    spec = AXIS_SPEC[axis]
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


# ---------------------------------------------------------------------- core
@dataclass
class HeavyTail:
    ss_mean: float
    ss_std: float
    ss_max: float
    peak_mean: float
    peak_max: float
    pct_peak_gt_thresh: float  # percentage of envs with peak > threshold
    pct_ss_gt_hthresh: float   # percentage of envs with ss > half-threshold
    n_env: int


def compute_heavy_tail(err_abs: np.ndarray, threshold: float, window_frac: float = 0.2) -> HeavyTail:
    """err_abs: (T, N). Compute per-env SS (mean over last window_frac) and peak."""
    T, N = err_abs.shape
    s = int((1 - window_frac) * T)
    ss = err_abs[s:].mean(axis=0)         # (N,)
    peak = err_abs[s:].max(axis=0)        # (N,)
    return HeavyTail(
        ss_mean=float(ss.mean()),
        ss_std=float(ss.std()),
        ss_max=float(ss.max()),
        peak_mean=float(peak.mean()),
        peak_max=float(peak.max()),
        pct_peak_gt_thresh=float(100.0 * (peak > threshold).sum() / max(N, 1)),
        pct_ss_gt_hthresh=float(100.0 * (ss > threshold / 10.0).sum() / max(N, 1)),
        n_env=N,
    )


def pick_sample_env(d: dict[str, np.ndarray]) -> int | None:
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


def compute_sample_divergence(err_abs: np.ndarray, sample_idx: int, window_frac: float = 0.2) -> dict[str, float]:
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


def compute_cross_axis_corr(d: dict[str, np.ndarray], window_frac: float = 0.2) -> dict[str, float]:
    """Per-env correlations between axes (axis decorrelation signal).

    Near 0 = envs that fail roll differ from envs that fail vz -> sample env divergence.
    Near +1 = same envs fail all axes -> sample env trajectory mirrors mean.
    """
    out: dict[str, float] = {}
    get = lambda ax: per_env_error(d, ax)
    ers = {ax: get(ax) for ax in AXES}

    def pe(arr: np.ndarray | None) -> np.ndarray | None:
        if arr is None:
            return None
        T = arr.shape[0]
        s = int((1 - window_frac) * T)
        return arr[s:].mean(axis=0)

    pe_ax = {ax: pe(ers[ax]) for ax in AXES}

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


# ---------------------------------------------------------------------- report
def thresh_for(axis: str, t_att: float, t_lv: float, t_yaw: float) -> float:
    tk = AXIS_SPEC[axis]["thresh_key"]
    return {"att": t_att, "lv": t_lv, "yaw": t_yaw}[tk]


def analyze_run(eval_dir: str, levels: list[str], t_att: float, t_lv: float, t_yaw: float) -> dict:
    out: dict = {"eval_dir": eval_dir, "levels": {}}
    for lvl in levels:
        d = load_level(eval_dir, lvl)
        if d is None:
            continue
        sample_idx = pick_sample_env(d)
        lvl_out: dict = {"sample_idx": sample_idx, "axes": {}}
        for ax in AXES:
            err = per_env_error(d, ax)
            if err is None:
                continue
            th = thresh_for(ax, t_att, t_lv, t_yaw)
            ht = compute_heavy_tail(err, th)
            axis_out = {"threshold": th, "heavy_tail": ht.__dict__}
            if sample_idx is not None:
                axis_out["divergence"] = compute_sample_divergence(err, sample_idx)
            lvl_out["axes"][ax] = axis_out
        lvl_out["corr"] = compute_cross_axis_corr(d)
        out["levels"][lvl] = lvl_out
    return out


def print_report(results: list[tuple[str, dict]], levels: list[str]) -> None:
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
        for ax in AXES:
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
        for ax in AXES:
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
        print(f'  rho~0 => axes solved on different env subsets (sample-mean divergence)')
        print(f'  rho~+1 => same envs fail all axes together')
        pairs = ["att_lv", "roll_vz", "roll_vy", "pitch_vy", "vx_vy", "roll_yaw", "pitch_vx"]
        hdr = f'{"run":<22} ' + ' '.join(f'{p:<11}' for p in pairs)
        print(hdr)
        for lab, r in results:
            corr = r["levels"].get(lvl, {}).get("corr", {})
            cells = [f'{corr.get(p, 0):+.3f}'.ljust(11) for p in pairs]
            print(f'{lab:<22} ' + ' '.join(cells))


# ---------------------------------------------------------------------- plot
def save_histogram(results: list[tuple[str, dict]], eval_dirs: list[str],
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
            d = load_level(eval_dir, lvl)
            if d is None:
                axes[ri, ci].set_visible(False); continue
            err = per_env_error(d, axis)
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


# ---------------------------------------------------------------------- main
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("runs", nargs="+", help="run dirs or eval_dr dirs")
    ap.add_argument("--labels", nargs="+", help="labels for each run")
    ap.add_argument("--levels", nargs="+", default=list(DEFAULT_LEVELS))
    ap.add_argument("--threshold-att", type=float, default=20.0, help="att threshold deg (default 20)")
    ap.add_argument("--threshold-lv",  type=float, default=0.5,  help="lin_vel threshold m/s (default 0.5)")
    ap.add_argument("--threshold-yaw", type=float, default=0.5,  help="yaw rate threshold rad/s (default 0.5)")
    ap.add_argument("--save-hist", metavar="PATH", help="save per-env peak histogram to PATH (axis=roll)")
    ap.add_argument("--hist-axis", default="roll", choices=list(AXES))
    ns = ap.parse_args()

    eval_dirs = [resolve_eval_dir(r) for r in ns.runs]
    labels = ns.labels if ns.labels else [os.path.basename(os.path.dirname(d.rstrip("/"))) or d for d in eval_dirs]
    if len(labels) != len(eval_dirs):
        print("[warn] #labels != #runs, using run names", file=sys.stderr)
        labels = [os.path.basename(os.path.dirname(d.rstrip("/"))) or d for d in eval_dirs]

    results = []
    for lab, ed in zip(labels, eval_dirs):
        r = analyze_run(ed, ns.levels, ns.threshold_att, ns.threshold_lv, ns.threshold_yaw)
        results.append((lab, r))

    print_report(results, ns.levels)

    if ns.save_hist:
        save_histogram(results, eval_dirs, ns.levels, ns.hist_axis, ns.save_hist)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
