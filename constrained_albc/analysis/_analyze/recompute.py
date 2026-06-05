# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""`recompute` subcommand: dispatch only (merged from recompute_eval_summary.py).

Metric core -> recompute_metrics.py (pure numpy).
Plot/JSON I/O -> recompute_plots.py (matplotlib).
"""

from __future__ import annotations

import argparse
import os

from .recompute_metrics import _RC_DR_LEVELS, _RC_DR_SCALE  # noqa: F401 (re-exported for callers)
from .recompute_plots import _multirun_comparison_plot, _process_and_write


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
