# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Post-hoc analysis of main eval outputs.

Subcommands:
    recompute       <run>            npz -> summary.json (pipeline prerequisite)
    eval_dr         <runs> --labels  heavy-tail / sample-mean divergence metrics
    switching       <runs> --labels  summary_segmented.json analysis
    student_latent  <diag_dirs>      per-dim MSE / env-var / confidence ratio from latent logs
    export          <path> --format  eval artifacts -> MATLAB .mat / long-format CSV

Pure Python (no Isaac Sim). Run with plain python3.

Usage:
    python3 constrained_albc/analysis/analyze.py recompute logs/.../run_dir
    python3 constrained_albc/analysis/analyze.py eval_dr 0 1 --labels A B
    python3 constrained_albc/analysis/analyze.py student_latent logs/.../latent_diagnostic
"""
from __future__ import annotations

import argparse

from common import DR_LEVELS  # type: ignore[import-not-found]

from .eval_dr import _ED_AXES, _ED_DEFAULT_LEVELS, cmd_eval_dr
from .export import cmd_export
from .recompute import cmd_recompute
from .student_latent import cmd_student_latent
from .switching import cmd_switching


def build_parser() -> argparse.ArgumentParser:
    top = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    sub = top.add_subparsers(dest="mode", required=True)

    # -- recompute --
    p_rc = sub.add_parser(
        "recompute",
        help="npz -> summary.json (pipeline prerequisite)",
        description="Read data_{none,soft,medium,hard}.npz from <run>/eval_dr/ and produce summary.json.",
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
    p_ed.add_argument("--failure-dr", action=argparse.BooleanOptionalAction, default=True,
                      help="join worst-env failures vs their per-env DR + save plot (default on)")
    p_ed.add_argument("--failure-dr-axis", default="roll", choices=list(_ED_AXES),
                      help="axis whose worst-k envs are joined against DR (default roll)")
    p_ed.add_argument("--failure-dr-k", type=int, default=10, help="num worst envs treated as failing (default 10)")
    p_ed.set_defaults(func=cmd_eval_dr)

    # -- switching --
    p_sw = sub.add_parser(
        "switching",
        help="summary_segmented.json analysis",
        description="Analyze segmented-mode outputs (cascade PID, target xyz=0 rpy=0).",
    )
    p_sw.add_argument("runs", nargs="+", help="Run dirs or eval_dr_switching dirs")
    p_sw.add_argument("--labels", nargs="+", default=None)
    p_sw.add_argument("--levels", nargs="+", default=DR_LEVELS)
    p_sw.set_defaults(func=cmd_switching)

    # -- student_latent --
    p_sl = sub.add_parser(
        "student_latent",
        help="per-dim MSE / env-var / confidence ratio from latent logs",
        description=(
            "Load latent_*.npz from one or more diagnose_student_latent runs and "
            "produce per-dim MSE / env-var tables / over-under-confidence ratio."
        ),
    )
    p_sl.add_argument(
        "diag_dirs",
        nargs="+",
        help="Diagnostic directories containing latent_{none,soft,medium,hard}.npz",
    )
    p_sl.set_defaults(func=cmd_student_latent)

    # -- export --
    p_ex = sub.add_parser(
        "export",
        help="eval artifacts -> MATLAB .mat / long-format CSV",
        description="Convert trajectory npz -> .mat and/or summary.json -> long-format CSV.",
    )
    p_ex.add_argument("path", help="A data_*.npz file, a summary.json, or a run/eval_dr dir")
    p_ex.add_argument(
        "--format", choices=["mat", "csv", "both"], default="both",
        help="Output formats to emit (default: both)",
    )
    p_ex.add_argument("--output-dir", default=None, help="Where to write outputs (default: alongside input)")
    p_ex.set_defaults(func=cmd_export)

    return top


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    return ns.func(ns)
