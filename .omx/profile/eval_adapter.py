#!/usr/bin/env python3
"""OMX eval-analysis adapter (sim-free) for Constrained ALBC.

The omx CORE already computes basic eval stats (mean/std/CV) from
summary.json via `omx reduce summarize --format eval_summary`. This adapter
adds ONLY what the core cannot: heavy-tail vs sample-mean-divergence
separation, required by repo rule 03-analysis-quality.md. It delegates 100%
to the sim-free driver constrained_albc/analysis/_analyze/eval_dr._ed_analyze_run;
it computes nothing itself, so it cannot drift from the engine. No Isaac Sim.

Usage:
    python3 eval_adapter.py heavy-tail <eval_dir> [--levels none soft medium hard]
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
