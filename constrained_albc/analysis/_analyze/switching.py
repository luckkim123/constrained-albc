# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`switching` subcommand: summary_switching.json analysis (merged from analyze_dr_switching.py)."""

from __future__ import annotations

import argparse
import json
import os

import numpy as np
from common import DR_LEVELS  # type: ignore[import-not-found]


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
