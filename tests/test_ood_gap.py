# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free unit tests for OOD generalization-gap + level-discovery (GAP 1, 2c).

These are PURE post-processing on summary dicts and on-disk data_*.npz names --
no Isaac Sim. They guard two things:
  1. _compute_generalization_gap: gap[axis][field] = ood - hard, only when both
     present; None otherwise (4-level summaries stay byte-identical).
  2. _discover_levels: union of the 4 in-dist levels + any extra data_<lvl>.npz
     on disk, ordered (in-dist first, ood last). A dir with ONLY the 4 npz must
     yield exactly the 4 in-dist levels (byte-identity guard).
"""
from __future__ import annotations

import os
import sys

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from _analyze.recompute_metrics import (  # noqa: E402
    _RC_DR_LEVELS,
    _compute_generalization_gap,
    _discover_levels,
)
from _analyze.recompute_plots import _write_run_json  # noqa: E402


def _mk_summary(levels):
    """Minimal summary[level][axis][field] with deterministic values per level."""
    base = {"none": 1.0, "soft": 2.0, "medium": 3.0, "hard": 4.0, "ood": 9.0}
    return {
        lvl: {
            "roll":  {"ss_error": base[lvl], "ss_jitter": base[lvl] * 0.1},
            "pitch": {"ss_error": base[lvl] + 0.5},
        }
        for lvl in levels
    }


# ---------------- generalization gap ----------------

def test_gap_is_ood_minus_hard_per_axis_field():
    summary = _mk_summary(["none", "soft", "medium", "hard", "ood"])
    gap = _compute_generalization_gap(summary)
    assert gap is not None
    # roll ss_error: ood 9.0 - hard 4.0 = 5.0
    assert gap["roll"]["ss_error"] == 5.0
    assert gap["roll"]["ss_jitter"] == (9.0 * 0.1) - (4.0 * 0.1)
    # pitch ss_error: (9.0+0.5) - (4.0+0.5) = 5.0
    assert gap["pitch"]["ss_error"] == 5.0


def test_gap_is_none_when_ood_absent():
    summary = _mk_summary(["none", "soft", "medium", "hard"])
    assert _compute_generalization_gap(summary) is None


def test_gap_is_none_when_hard_absent():
    # ood present but no hard baseline -> cannot compute a gap.
    summary = _mk_summary(["none", "soft", "ood"])
    assert _compute_generalization_gap(summary) is None


def test_gap_skips_field_missing_in_one_level():
    summary = _mk_summary(["hard", "ood"])
    # remove a field from hard so it cannot be differenced
    del summary["hard"]["roll"]["ss_jitter"]
    gap = _compute_generalization_gap(summary)
    assert "ss_error" in gap["roll"]
    assert "ss_jitter" not in gap["roll"]  # silently skipped, not crashed


def test_gap_skips_non_numeric_and_axis_only_in_one_level():
    summary = _mk_summary(["hard", "ood"])
    summary["ood"]["yaw"] = {"ss_error": 1.0}  # axis absent from hard
    summary["hard"]["roll"]["ss_error"] = None  # non-numeric -> skip
    gap = _compute_generalization_gap(summary)
    assert "yaw" not in gap                     # axis must exist in BOTH
    assert "ss_error" not in gap.get("roll", {})  # None operand skipped


# ---------------- level discovery ----------------

def test_discover_levels_four_npz_is_byte_identical_to_constant(tmp_path):
    for lvl in _RC_DR_LEVELS:
        (tmp_path / f"data_{lvl}.npz").write_bytes(b"")
    levels = _discover_levels(str(tmp_path))
    assert levels == list(_RC_DR_LEVELS)  # exact, ordered, no extras


def test_discover_levels_appends_ood_last(tmp_path):
    for lvl in [*_RC_DR_LEVELS, "ood"]:
        (tmp_path / f"data_{lvl}.npz").write_bytes(b"")
    levels = _discover_levels(str(tmp_path))
    assert levels == [*list(_RC_DR_LEVELS), "ood"]


def test_discover_levels_ignores_non_data_files(tmp_path):
    for lvl in _RC_DR_LEVELS:
        (tmp_path / f"data_{lvl}.npz").write_bytes(b"")
    (tmp_path / "summary.json").write_bytes(b"{}")
    (tmp_path / "latent_hard.npz").write_bytes(b"")  # not a data_*.npz
    levels = _discover_levels(str(tmp_path))
    assert levels == list(_RC_DR_LEVELS)


def test_discover_levels_missing_indist_npz_only_returns_present(tmp_path):
    # if some in-dist npz are missing, only the present in-dist levels appear
    # (still ordered), so downstream skip-if-missing stays consistent.
    for lvl in ["none", "hard", "ood"]:
        (tmp_path / f"data_{lvl}.npz").write_bytes(b"")
    levels = _discover_levels(str(tmp_path))
    assert levels == ["none", "hard", "ood"]


# ---------------- summary.json gap attachment + byte-identity ----------------

def _read_summary(d):
    import json
    with open(os.path.join(d, "summary.json")) as f:
        return json.load(f)


def test_write_run_json_four_level_has_no_gap_key(tmp_path):
    # Byte-identity guard: a 4-level (no-ood) summary must NOT gain any new key.
    sub = tmp_path / "eval_dr"
    sub.mkdir()
    metrics = _mk_summary(list(_RC_DR_LEVELS))
    _write_run_json(str(tmp_path), metrics, data_subdir="eval_dr")
    out = _read_summary(str(sub))
    assert set(out.keys()) == set(_RC_DR_LEVELS)
    assert "generalization_gap" not in out


def test_write_run_json_five_level_attaches_gap(tmp_path):
    sub = tmp_path / "eval_dr"
    sub.mkdir()
    metrics = _mk_summary([*list(_RC_DR_LEVELS), "ood"])
    _write_run_json(str(tmp_path), metrics, data_subdir="eval_dr")
    out = _read_summary(str(sub))
    assert "generalization_gap" in out
    # roll ss_error gap = ood 9.0 - hard 4.0 = 5.0
    assert out["generalization_gap"]["roll"]["ss_error"] == 5.0
    # the 5 level entries are still present and unchanged
    assert out["ood"]["roll"]["ss_error"] == 9.0
    assert out["hard"]["roll"]["ss_error"] == 4.0


def test_write_run_json_does_not_mutate_caller_metrics(tmp_path):
    # attaching the gap to the JSON must not leave a stray key in the in-memory
    # metrics dict the caller still uses for plotting.
    sub = tmp_path / "eval_dr"
    sub.mkdir()
    metrics = _mk_summary([*list(_RC_DR_LEVELS), "ood"])
    _write_run_json(str(tmp_path), metrics, data_subdir="eval_dr")
    assert "generalization_gap" not in metrics
