# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Joint1 drift analysis for the centering experiment (pure numpy + matplotlib).

Consumes the joint1_cmd / joint1_target / joint1_pos arrays that eval.py records
in data_<level>.npz (T, num_envs). Quantifies the free-DOF drift the centering
reward is meant to suppress, and compares runs (baseline vs k sweep).

Drift metrics (per env, then aggregated over envs):
  - drift_slope: least-squares slope of joint1_target over the post-warmup window
    (rad/s). The drift signature is a non-zero monotonic slope at flat command.
  - target_range: max(joint1_target) - min(joint1_target) over the window (rad).
  - final_abs: |joint1_target[-1]| at episode end, wrapped to (-pi, pi] (rad).
  - cmd_mean / cmd_std: action[0] mean and std (a non-zero mean = directional bias
    that the integrator accumulates into drift).

Usage (single run, all DR levels):
  python constrained_albc/analysis/joint1_drift.py --run_dir <eval_output_dir>
Compare runs:
  python constrained_albc/analysis/joint1_drift.py \
      --label baseline:<dir> --label k05:<dir> --label k10:<dir> --label k20:<dir> \
      --out <out_dir>
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
from common import DR_LEVELS


def _wrap(x: np.ndarray) -> np.ndarray:
    """Wrap angle(s) to (-pi, pi]."""
    return np.arctan2(np.sin(x), np.cos(x))


def _find_data_files(run_dir: Path) -> dict[str, Path]:
    """Map DR level -> data_<level>.npz under a run/eval directory."""
    found: dict[str, Path] = {}
    for level in DR_LEVELS + ["ood"]:
        for cand in run_dir.rglob(f"data_{level}.npz"):
            found[level] = cand
            break
    return found


def _drift_metrics(npz_path: Path, warmup_steps_default: int = 0) -> dict:
    """Compute per-env joint1 drift metrics from one data_<level>.npz."""
    d = np.load(npz_path, allow_pickle=True)
    if "joint1_target" not in d:
        raise KeyError(
            f"{npz_path} has no joint1_target -- re-run eval.py with the joint1 "
            "recording (this build) to populate it."
        )
    tgt = d["joint1_target"]  # (T, num_envs)
    cmd = d["joint1_cmd"]  # (T, num_envs)
    pos = d["joint1_pos"]  # (T, num_envs)
    T, n = tgt.shape

    warm = int(d["warmup_steps"]) if "warmup_steps" in d else warmup_steps_default
    warm = min(warm, max(0, T - 2))
    step_dt = float(d["time"][1] - d["time"][0]) if "time" in d and T > 1 else 0.02

    t = np.arange(warm, T) * step_dt
    seg = tgt[warm:]  # (T', num_envs)
    # Per-env least-squares slope (rad/s): cov(t, x) / var(t).
    t_c = t - t.mean()
    denom = (t_c**2).sum()
    slopes = (t_c[:, None] * (seg - seg.mean(axis=0, keepdims=True))).sum(axis=0) / denom

    target_range = seg.max(axis=0) - seg.min(axis=0)
    final_abs = np.abs(_wrap(tgt[-1]))
    cmd_seg = cmd[warm:]
    cmd_mean = cmd_seg.mean(axis=0)
    cmd_std = cmd_seg.std(axis=0)

    def agg(a):
        return {
            "mean": float(np.mean(a)),
            "std": float(np.std(a)),
            "p50": float(np.percentile(a, 50)),
            "p95": float(np.percentile(a, 95)),
            "max": float(np.max(a)),
        }

    return {
        "n_envs": int(n),
        "drift_slope_rad_s": agg(np.abs(slopes)),
        "target_range_rad": agg(target_range),
        "final_abs_rad": agg(final_abs),
        "cmd_mean": agg(np.abs(cmd_mean)),
        "cmd_std": agg(cmd_std),
        "_raw": {  # kept for plotting
            "tgt": tgt,
            "pos": pos,
            "time": d["time"] if "time" in d else np.arange(T) * step_dt,
            "warm": warm,
        },
    }


def analyze_run(run_dir: Path) -> dict:
    files = _find_data_files(run_dir)
    if not files:
        raise FileNotFoundError(f"no data_<level>.npz under {run_dir}")
    return {lvl: _drift_metrics(p) for lvl, p in files.items()}


def _fmt_table(runs: dict[str, dict]) -> str:
    """Markdown table: rows = (run, DR level), cols = drift metrics (mean/p95)."""
    lines = [
        "| run | DR | drift_slope mean | drift_slope p95 | target_range p95 (rad) "
        "| final_abs p95 (rad) | |cmd_mean| | cmd_std |",
        "|:--|:--|--:|--:|--:|--:|--:|--:|",
    ]
    for run, levels in runs.items():
        for lvl in DR_LEVELS:
            if lvl not in levels:
                continue
            m = levels[lvl]
            lines.append(
                f"| {run} | {lvl} "
                f"| {m['drift_slope_rad_s']['mean']:.4f} "
                f"| {m['drift_slope_rad_s']['p95']:.4f} "
                f"| {m['target_range_rad']['p95']:.3f} "
                f"| {m['final_abs_rad']['p95']:.3f} "
                f"| {m['cmd_mean']['mean']:.4f} "
                f"| {m['cmd_std']['mean']:.4f} |"
            )
    return "\n".join(lines)


def _plot_compare(runs: dict[str, dict], out_dir: Path) -> list[Path]:
    """Per-DR-level: mean +- std joint1_target time-series across runs."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for lvl in DR_LEVELS:
        present = {r: lv[lvl] for r, lv in runs.items() if lvl in lv}
        if not present:
            continue
        fig, ax = plt.subplots(figsize=(9, 5))
        for run, m in present.items():
            raw = m["_raw"]
            tgt = raw["tgt"]  # (T, n)
            time = raw["time"]
            mu = tgt.mean(axis=1)
            sd = tgt.std(axis=1)
            ax.plot(time, mu, label=f"{run} (mean)")
            ax.fill_between(time, mu - sd, mu + sd, alpha=0.15)
        ax.axhline(0.0, color="k", lw=0.8, ls="--", alpha=0.5)
        ax.set_xlabel("time (s)")
        ax.set_ylabel("joint1_target (rad)")
        ax.set_title(f"Joint1 target under flat command -- DR={lvl}")
        ax.legend(fontsize=8)
        ax.grid(alpha=0.3)
        p = out_dir / f"joint1_target_{lvl}.png"
        fig.tight_layout()
        fig.savefig(p, dpi=120)
        plt.close(fig)
        paths.append(p)
    return paths


def _strip_raw(runs: dict) -> dict:
    """Drop the _raw plotting payload before JSON serialization."""
    out = {}
    for run, levels in runs.items():
        out[run] = {}
        for lvl, m in levels.items():
            out[run][lvl] = {k: v for k, v in m.items() if k != "_raw"}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Joint1 drift analysis (centering experiment).")
    ap.add_argument("--run_dir", type=str, default=None, help="Single run eval dir.")
    ap.add_argument(
        "--label",
        action="append",
        default=[],
        help="name:dir for multi-run compare (repeatable).",
    )
    ap.add_argument("--out", type=str, default=None, help="Output dir for table + plots.")
    args = ap.parse_args()

    runs: dict[str, dict] = {}
    if args.run_dir:
        runs["run"] = analyze_run(Path(args.run_dir))
    for spec in args.label:
        name, _, d = spec.partition(":")
        runs[name] = analyze_run(Path(d))
    if not runs:
        ap.error("provide --run_dir or at least one --label name:dir")

    table = _fmt_table(runs)
    print(table)

    out_dir = Path(args.out) if args.out else Path("joint1_drift_out")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "drift_table.md").write_text(table + "\n")
    (out_dir / "drift_metrics.json").write_text(json.dumps(_strip_raw(runs), indent=2))
    plots = _plot_compare(runs, out_dir)
    print(f"\n[INFO] wrote {out_dir}/drift_table.md, drift_metrics.json, {len(plots)} plots")


if __name__ == "__main__":
    main()
