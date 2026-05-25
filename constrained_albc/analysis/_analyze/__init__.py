# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Post-hoc analysis of main eval outputs.

Subcommands:
    recompute       <run>            npz -> enhanced_summary.json (pipeline prerequisite)
    eval_dr         <runs> --labels  heavy-tail / sample-mean divergence metrics
    switching       <runs> --labels  summary_switching.json analysis
    table           <run>            Table 1 attitude SS error PNG
    student_latent  <diag_dirs>      per-dim MSE / env-var / confidence ratio from latent logs

Pure Python (no Isaac Sim). Run with plain python3.

Usage:
    python3 scripts/analysis/analyze.py recompute logs/.../run_dir
    python3 scripts/analysis/analyze.py eval_dr 0 1 --labels A B
    python3 scripts/analysis/analyze.py table 0
    python3 scripts/analysis/analyze.py student_latent logs/.../latent_diagnostic
"""
from __future__ import annotations

import argparse

from common import DR_LEVELS  # type: ignore[import-not-found]

from .eval_dr import _ED_AXES, _ED_DEFAULT_LEVELS, cmd_eval_dr
from .recompute import cmd_recompute
from .student_latent import cmd_student_latent
from .switching import cmd_switching
from .table import cmd_table


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

    # -- student_latent --
    p_sl = sub.add_parser(
        "student_latent",
        help="per-dim MSE / env-var / confidence ratio from latent logs",
        description=(
            "Load latent_log_*.npz from one or more diagnose_student_latent runs and "
            "produce per-dim MSE / env-var tables / over-under-confidence ratio."
        ),
    )
    p_sl.add_argument(
        "diag_dirs",
        nargs="+",
        help="Diagnostic directories containing latent_log_{none,soft,medium,hard}.npz",
    )
    p_sl.set_defaults(func=cmd_student_latent)

    return top


def main() -> int:
    parser = build_parser()
    ns = parser.parse_args()
    return ns.func(ns)
