# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Units + decision-floor contract for the enhanced summary.json (G6, 2026-07-27).

The os/n_gt20 mislabel ("deg" on percent-of-step values) propagated into the
SSOT twice; these tests pin the machine-readable contract that replaces the
author's memory.
"""

from __future__ import annotations

import json
import math
import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from _analyze.recompute_metrics import floor_verdict, unit_for  # noqa: E402
from _analyze.recompute_plots import _write_run_json  # noqa: E402


def test_unit_for():
    assert unit_for("roll", "ss_error") == "deg"
    assert unit_for("yaw", "ss_error") == "rad/s"
    assert unit_for("vx", "ss_jitter") == "m/s"
    assert unit_for("roll", "os_env_mean") == "pp_of_step"
    assert unit_for("roll", "n_gt20") == "envs"
    assert unit_for("roll", "rise_time") == "s"


def test_floor_verdict():
    assert floor_verdict("ss_error", 0.05, "roll") == "BELOW-FLOOR"
    assert floor_verdict("ss_error", 0.10, "roll") == "REAL"
    assert floor_verdict("ss_error", 0.50, "yaw") == "NO-FLOOR"  # rad/s axis
    assert floor_verdict("os_env_mean", -12.0) == "REAL"
    assert floor_verdict("n_gt20", 3.0) == "BELOW-FLOOR"
    assert floor_verdict("ss_jitter", 99.0) == "NO-FLOOR"  # no registered floor
    assert floor_verdict("ss_error", math.nan, "roll") == "NO-FLOOR"


def test_summary_json_carries_units_and_floors(tmp_path):
    run_dir = tmp_path / "run"
    (run_dir / "eval").mkdir(parents=True)
    metrics = {"hard": {"roll": {"ss_error": 1.0}, "survival_pct": 100.0}}
    _write_run_json(str(run_dir), metrics, data_subdir="eval")
    s = json.loads((run_dir / "eval" / "summary.json").read_text())
    assert s["units"]["axis_units"]["yaw"] == "rad/s"
    assert s["units"]["field_units"]["os_env_mean"] == "pp_of_step"
    assert s["decision_floors"]["ss_error"] == 0.10
    assert s["hard"]["roll"]["ss_error"] == 1.0
    # caller's dict must not be mutated
    assert "units" not in metrics
