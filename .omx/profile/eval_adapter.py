#!/usr/bin/env python3
"""OMX eval-analysis adapter (sim-free) for Constrained ALBC.

The omx CORE already computes basic eval stats (mean/std/CV) from
summary.json via `omx reduce summarize --format eval_summary`. This adapter
adds ONLY what the core cannot: heavy-tail vs sample-mean-divergence
separation (static eval), required by repo rule 03-analysis-quality.md, and the
per-segment post-switch transient (segmented / DR-switch eval). Both delegate to
sim-free drivers (_analyze.eval_dr for static, _analyze.switching for segmented);
the adapter applies only standard numpy reductions, so it cannot drift from the
engine of record. No Isaac Sim.

Coverage: static (heavy-tail) + segmented (post-switch transient). periodic is
NOT covered -- its single data_periodic.npz has no sim-free driver (the periodic
compute lives in eval.py which boots Isaac Sim); see the eval-adapter engine-gap
finding.

Usage:
    python3 eval_adapter.py heavy-tail <eval_dir> [--levels none soft medium hard]
    python3 eval_adapter.py segmented <eval_dir> [--levels none soft medium hard]
"""
from __future__ import annotations

import argparse
import json
import os
import sys

# One-line sys.path shim to reach the sim-free analysis package.
# Verified 2026-06-05: putting analysis/ on sys.path is sufficient because
# _analyze/ is a real package (see findings/analysis_refactor_2026_06_05...).
_ANALYSIS_DIR = os.environ.get(
    "ALBC_ANALYSIS_DIR",
    "/workspace/constrained-albc/constrained_albc/analysis",
)
if _ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, _ANALYSIS_DIR)

# Engine defaults (mirrors _analyze/__init__.py:68-70 and eval_dr.py:19).
_DEFAULT_LEVELS = ("none", "soft", "medium", "hard")
_T_ATT, _T_LV, _T_YAW = 20.0, 0.5, 0.5


def analyze_eval(eval_dir: str, levels=None) -> dict:
    """Heavy-tail / sample-mean-divergence / cross-axis-corr per DR level.

    Pure delegation to the sim-free driver _analyze.eval_dr._ed_analyze_run.
    Computes nothing here, so it cannot drift from the engine of record.
    Basic stats (mean/std/CV) are intentionally NOT here -- the omx core
    already produces them from summary.json via `omx reduce` (DRY).
    """
    from _analyze.eval_dr import _ed_analyze_run  # sim-free

    lvls = list(levels) if levels else list(_DEFAULT_LEVELS)
    return _ed_analyze_run(eval_dir, lvls, _T_ATT, _T_LV, _T_YAW)


# segmented (DR-switch) post-switch transient axes, mapped to the switching engine's keys.
_SEG_AXES = {
    "roll": "peak_roll_deg",
    "pitch": "peak_pitch_deg",
    "yaw": "peak_yaw_deg",
}


def analyze_segmented(eval_dir: str, levels=None) -> dict:
    """Per-level per-axis post-switch transient for segmented (DR-switch) eval.

    Delegates raw loading + post-switch extraction to the sim-free engine driver
    `_analyze.switching` (`_sw_load_run`, `_sw_all_post_switch`), then applies only
    standard numpy reductions (mean / p95 / max) over the engine-extracted values.
    No per-axis metric math is re-implemented here, so the adapter cannot drift from
    the engine of record. Covers the segment-switch transient the core summarize and
    the heavy-tail adapter do not. (periodic remains an engine-gap: its single
    data_periodic.npz has no sim-free driver -- see the engine-gap finding.)
    """
    import json
    import os

    import numpy as np

    from _analyze.switching import _sw_all_post_switch  # sim-free metric extraction

    lvls = list(levels) if levels else list(_DEFAULT_LEVELS)
    # Raw I/O only (NOT metric math): load summary_segmented.json directly so the
    # adapter accepts the current `eval/segmented_<ts>/` layout where the summary
    # sits directly in eval_dir. The engine's _sw_load_run assumes the legacy
    # `eval_dr_switching/` subdir convention; mirroring only its json.load here keeps
    # the post-switch metric extraction (_sw_all_post_switch) owned by the engine.
    summary_path = os.path.join(eval_dir, "summary_segmented.json")
    with open(summary_path) as f:
        run = {"summary": json.load(f), "data": {}}
    avail = set(run["summary"]["metrics"].keys())
    out: dict = {"levels": {}}
    for lvl in lvls:
        if lvl not in avail:
            continue
        axes: dict = {}
        for axis, engine_key in _SEG_AXES.items():
            vals = _sw_all_post_switch(run, lvl, engine_key)  # segs 1..N, env x seg
            axes[axis] = {
                "post_switch": {
                    "peak_mean": float(np.mean(vals)),
                    "peak_p95": float(np.percentile(vals, 95)),
                    "peak_max": float(np.max(vals)),
                }
            }
        out["levels"][lvl] = {"axes": axes}
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="OMX sim-free eval analysis adapter")
    sub = parser.add_subparsers(dest="cmd", required=True)
    ht = sub.add_parser("heavy-tail", help="per-level per-axis heavy-tail / divergence / corr (static)")
    ht.add_argument("eval_dir", help="dir holding data_<level>.npz")
    ht.add_argument("--levels", nargs="+", default=None,
                    help="DR levels (default: none soft medium hard)")
    sg = sub.add_parser("segmented", help="per-level per-axis post-switch transient (DR-switch eval)")
    sg.add_argument("eval_dir", help="dir holding summary_segmented.json")
    sg.add_argument("--levels", nargs="+", default=None,
                    help="DR levels (default: none soft medium hard)")
    args = parser.parse_args(argv)

    if args.cmd == "heavy-tail":
        out = analyze_eval(args.eval_dir, levels=args.levels)
        print(json.dumps(out))
        return 0
    if args.cmd == "segmented":
        out = analyze_segmented(args.eval_dir, levels=args.levels)
        print(json.dumps(out))
        return 0
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
