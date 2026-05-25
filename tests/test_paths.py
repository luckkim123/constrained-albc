# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for the run_id path resolver (constrained_albc/analysis/paths.py).

paths.py is pure filesystem logic (no Isaac Sim), so these build synthetic run trees
under tmp_path and assert resolution. Covers the 4-step resolve order, manifest-vs-legacy
handling, numeric (never alphabetic) checkpoint sort, and eval-dir layout.
"""

from __future__ import annotations

import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis"))
import paths as P  # noqa: E402


# ---------------------------------------------------------------------------
# Synthetic-tree builders
# ---------------------------------------------------------------------------
def _make_new_run(experiments_root, run_id, with_manifest=True, with_train=True):
    """Create experiments/<run_id>/ with optional manifest + train/ subtree."""
    root = experiments_root / run_id
    if with_train:
        (root / "train" / "tb").mkdir(parents=True)
        (root / "train" / "checkpoints").mkdir(parents=True)
    else:
        root.mkdir(parents=True)
    if with_manifest:
        (root / P.MANIFEST_NAME).write_text(json.dumps({
            "run_id": run_id,
            "task": "Isaac-FullDOF-TRPO-v0",
            "paths": {"tb": "train/tb", "checkpoints": "train/checkpoints"},
        }))
    return root


def _make_legacy_run(logs_root, exp, run_name):
    """Create logs/rsl_rl/<exp>/<run_name>/ with a tfevents file (no manifest)."""
    root = logs_root / exp / run_name
    root.mkdir(parents=True)
    (root / "events.out.tfevents.1234.host").write_text("")
    return root


# ---------------------------------------------------------------------------
# resolve_run: 4-step order
# ---------------------------------------------------------------------------
def test_resolve_direct_path(tmp_path):
    run = _make_new_run(tmp_path / "experiments", "2026-05-25_16-00-00_trpo")
    h = P.resolve_run(str(run))
    assert h.run_id == "2026-05-25_16-00-00_trpo"
    assert h.manifest is not None
    assert not h.is_legacy


def test_resolve_by_run_id_under_experiments(tmp_path):
    exp = tmp_path / "experiments"
    _make_new_run(exp, "2026-05-25_16-00-00_trpo")
    h = P.resolve_run("2026-05-25_16-00-00_trpo", experiments_root=str(exp))
    assert h.run_id == "2026-05-25_16-00-00_trpo"
    assert (h.tb_dir).name == "tb"


def test_resolve_by_substring_and_index(tmp_path):
    exp = tmp_path / "experiments"
    _make_new_run(exp, "2026-05-25_10-00-00_trpo")
    _make_new_run(exp, "2026-05-25_20-00-00_ppo")
    # index 0 = latest (reverse-sorted by name -> the 20-00-00 one)
    assert P.resolve_run("0", experiments_root=str(exp)).run_id.endswith("_ppo")
    # substring
    assert P.resolve_run("trpo", experiments_root=str(exp)).run_id.endswith("_trpo")


def test_resolve_legacy_fallback(tmp_path):
    exp = tmp_path / "experiments"            # empty active tree
    logs = tmp_path / "logs" / "rsl_rl"
    _make_legacy_run(logs, "full_dof_trpo", "2026-04-01_09-00-00_old")
    h = P.resolve_run(
        "old", experiments_root=str(exp), legacy_logs_root=str(logs),
    )
    assert h.is_legacy
    assert h.manifest is None
    assert h.run_id == "2026-04-01_09-00-00_old"


def test_resolve_active_precedes_legacy(tmp_path):
    """An active run_id match must win over a legacy substring match."""
    exp = tmp_path / "experiments"
    logs = tmp_path / "logs" / "rsl_rl"
    _make_new_run(exp, "2026-05-25_16-00-00_trpo")
    _make_legacy_run(logs, "full_dof_trpo", "2026-04-01_09-00-00_trpo")  # also matches "trpo"
    h = P.resolve_run("trpo", experiments_root=str(exp), legacy_logs_root=str(logs))
    assert not h.is_legacy
    assert h.run_id == "2026-05-25_16-00-00_trpo"


def test_resolve_not_found_raises(tmp_path):
    with pytest.raises(FileNotFoundError):
        P.resolve_run(
            "nope",
            experiments_root=str(tmp_path / "experiments"),
            legacy_logs_root=str(tmp_path / "logs"),
        )


# ---------------------------------------------------------------------------
# RunHandle path accessors
# ---------------------------------------------------------------------------
def test_legacy_handle_falls_back_to_root_paths(tmp_path):
    logs = tmp_path / "logs" / "rsl_rl"
    run = _make_legacy_run(logs, "exp", "2026-04-01_run")
    h = P.resolve_run("run", experiments_root=str(tmp_path / "none"), legacy_logs_root=str(logs))
    # No train/ subtree -> tb_dir and checkpoints_dir fall back to the run root.
    assert h.tb_dir == run
    assert h.checkpoints_dir == run


def test_latest_checkpoint_numeric_sort(tmp_path):
    """model_4999.pt must beat model_999.pt (numeric, not alphabetic)."""
    run = _make_new_run(tmp_path / "experiments", "2026-05-25_run")
    ckpt_dir = run / "train" / "checkpoints"
    for n in (99, 999, 4999, 100):
        (ckpt_dir / f"model_{n}.pt").write_text("")
    h = P.resolve_run(str(run))
    assert h.latest_checkpoint().name == "model_4999.pt"


def test_latest_checkpoint_none_when_empty(tmp_path):
    run = _make_new_run(tmp_path / "experiments", "2026-05-25_run")
    h = P.resolve_run(str(run))
    assert h.latest_checkpoint() is None


# ---------------------------------------------------------------------------
# resolve_eval
# ---------------------------------------------------------------------------
def test_resolve_eval_layout(tmp_path):
    run = _make_new_run(tmp_path / "experiments", "2026-05-25_run")
    h = P.resolve_run(str(run))
    eval_dir = P.resolve_eval(h, "static", eval_ts="2026-05-25_18-00-00")
    assert eval_dir == h.root / "eval" / "static_2026-05-25_18-00-00"
    # resolve_eval must not create the directory (read-only for reads).
    assert not eval_dir.exists()


def test_resolve_eval_generates_timestamp(tmp_path):
    run = _make_new_run(tmp_path / "experiments", "2026-05-25_run")
    h = P.resolve_run(str(run))
    eval_dir = P.resolve_eval(h, "periodic")
    assert eval_dir.parent == h.root / "eval"
    assert eval_dir.name.startswith("periodic_")


# ---------------------------------------------------------------------------
# manifest read/write round-trip
# ---------------------------------------------------------------------------
def test_manifest_round_trip(tmp_path):
    m = P.Manifest(
        run_id="2026-05-25_16-00-00_trpo",
        task="Isaac-FullDOF-TRPO-v0",
        config={"num_envs": 4096, "seed": 30},
    )
    out = P.write_manifest(tmp_path / "run", m)
    assert out.name == P.MANIFEST_NAME
    loaded = P.read_manifest(tmp_path / "run")
    assert loaded["run_id"] == "2026-05-25_16-00-00_trpo"
    assert loaded["config"]["num_envs"] == 4096
    assert loaded["status"] == "running"
    # parent_run_id omitted for a teacher run.
    assert "parent_run_id" not in loaded


def test_manifest_student_includes_parent(tmp_path):
    m = P.Manifest(
        run_id="2026-05-25_s", task="Isaac-FullDOF-TRPO-v0",
        kind="student", parent_run_id="2026-05-25_t",
    )
    P.write_manifest(tmp_path / "run", m)
    loaded = P.read_manifest(tmp_path / "run")
    assert loaded["kind"] == "student"
    assert loaded["parent_run_id"] == "2026-05-25_t"


def test_find_runs_skips_legacy(tmp_path):
    exp = tmp_path / "experiments"
    _make_new_run(exp, "2026-05-25_a")
    _make_new_run(exp, "2026-05-25_b")
    (exp / "legacy").mkdir()  # must be skipped
    runs = P.find_runs(str(exp))
    assert {r.run_id for r in runs} == {"2026-05-25_a", "2026-05-25_b"}
