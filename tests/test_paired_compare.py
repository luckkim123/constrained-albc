# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Paired-condition comparison mode (G4, 2026-07-27).

Pins the delta/verdict table and the injection bite-check (byte-identical
condition arrays = silent no-op injector -> hard failure).
"""

from __future__ import annotations

import argparse
import json
import os
import sys

import numpy as np
import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from _analyze.paired import bite_check, cmd_paired  # noqa: E402


def _mk_eval_dir(root, name, ss_error, os_mean, fault_health):
    d = root / name
    d.mkdir()
    summary = {"none": {"roll": {"ss_error": ss_error, "os_env_mean": os_mean},
                        "survival_pct": 100.0}}
    (d / "summary.json").write_text(json.dumps(summary))
    np.savez(d / "data_none.npz", fault_thruster_4=np.full(4, fault_health, dtype=np.float32))
    return str(d)


def _ns(**kw):
    defaults = dict(axes=["roll"], fields=["ss_error", "os_env_mean"],
                    bite=None, allow_no_bite=False)
    defaults.update(kw)
    return argparse.Namespace(**defaults)


def test_delta_table_with_floor_verdicts(tmp_path, capsys):
    base = _mk_eval_dir(tmp_path, "healthy", ss_error=1.0, os_mean=5.0, fault_health=1.0)
    treat = _mk_eval_dir(tmp_path, "fault", ss_error=1.25, os_mean=8.0, fault_health=0.0)
    cmd_paired(_ns(pair=[f"P:{base}:{treat}"], bite="fault_thruster_4"))
    out = capsys.readouterr().out
    assert "[BITE-CHECK OK]" in out
    assert "+0.250" in out and "REAL" in out          # ss_error 0.25 >= 0.10 deg floor
    assert "+3.000" in out and "BELOW-FLOOR" in out   # os delta 3 pp < 10 pp floor


def test_bite_check_fails_on_identical_arrays(tmp_path):
    base = _mk_eval_dir(tmp_path, "healthy", 1.0, 5.0, fault_health=1.0)
    treat = _mk_eval_dir(tmp_path, "fault", 1.2, 6.0, fault_health=1.0)  # injector no-op
    with pytest.raises(SystemExit):
        cmd_paired(_ns(pair=[f"P:{base}:{treat}"], bite="fault_thruster_4"))


def test_bite_check_reports_missing_key(tmp_path):
    base = _mk_eval_dir(tmp_path, "healthy", 1.0, 5.0, 1.0)
    treat = _mk_eval_dir(tmp_path, "fault", 1.2, 6.0, 0.0)
    fails = bite_check([("P", base, treat)], "fault_thruster_9", ["none"])
    assert fails and "lacks" in fails[0]
