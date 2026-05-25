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
            "task": "Isaac-ConstrainedALBC-TRPO-v0",
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
        task="Isaac-ConstrainedALBC-TRPO-v0",
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
        run_id="2026-05-25_s", task="Isaac-ConstrainedALBC-TRPO-v0",
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


# ---------------------------------------------------------------------------
# task_short / make_run_id (design section 2-A)
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "task_id, expected",
    [
        ("Isaac-ConstrainedALBC-TRPO-v0", "trpo"),
        ("Isaac-ConstrainedALBC-PPO-v0", "ppo"),
        ("Isaac-ConstrainedALBC-NoEncoder-v0", "noenc"),
        ("Isaac-ConstrainedALBC-TDC-v0", "tdc"),
        # Superset substrings must match the longer pattern first.
        ("Isaac-ConstrainedALBC-TRPO-NoIPO-v0", "trpo-noipo"),  # not "trpo"
        ("Isaac-ConstrainedALBC-PPO-Enc-v0", "ppo-enc"),        # not "ppo"
    ],
)
def test_task_short_known_tasks(task_id, expected):
    assert P.task_short(task_id) == expected


def test_task_short_unknown_fallback():
    # Unrecognized task -> slugified, never crashes.
    assert P.task_short("Isaac-ConstrainedALBC-Mystery-v0") == "mystery"
    assert P.task_short("Isaac-Cartpole-v0") == "cartpole"


def test_make_run_id_format():
    rid = P.make_run_id("Isaac-ConstrainedALBC-TRPO-v0", ts="2026-05-25_16-02-48")
    assert rid == "2026-05-25_16-02-48_trpo"


def test_make_run_id_with_tag():
    rid = P.make_run_id("Isaac-ConstrainedALBC-PPO-Enc-v0", tag="ablation", ts="2026-05-25_17-00-12")
    assert rid == "2026-05-25_17-00-12_ppo-enc_ablation"


def test_make_run_id_no_git_sha():
    """Open Q #3: run_id must NOT contain a git sha (only ts + task_short [+ tag])."""
    rid = P.make_run_id("Isaac-ConstrainedALBC-TRPO-v0", ts="2026-05-25_16-02-48")
    # Exactly 3 underscore-joined fields: date_time_taskshort (date has its own _).
    assert rid.count("_") == 2
    assert rid == "2026-05-25_16-02-48_trpo"


# ---------------------------------------------------------------------------
# emit_run_manifest: minimal-touch single-tree wiring (training output not moved)
# ---------------------------------------------------------------------------
def _fake_log_dir(tmp_path, leaf="2026-05-25_16-02-48", with_params=True):
    """Create a fake train.py log_dir with optional params/{env,agent}.yaml."""
    log_dir = tmp_path / "logs" / "rsl_rl" / "full_dof_trpo" / leaf
    (log_dir / "params").mkdir(parents=True)
    if with_params:
        (log_dir / "params" / "env.yaml").write_text("env: {}\n")
        (log_dir / "params" / "agent.yaml").write_text("agent: {}\n")
    return log_dir


def test_emit_manifest_reuses_log_dir_timestamp(tmp_path):
    log_dir = _fake_log_dir(tmp_path)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest("Isaac-ConstrainedALBC-TRPO-v0", log_dir, experiments_root=str(exp))
    # run_id timestamp matches the training folder leaf -> no drift.
    assert h.run_id == "2026-05-25_16-02-48_trpo"
    assert (exp / h.run_id / P.MANIFEST_NAME).is_file()


def test_emit_manifest_copies_configs(tmp_path):
    log_dir = _fake_log_dir(tmp_path)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest("Isaac-ConstrainedALBC-TRPO-v0", log_dir, experiments_root=str(exp))
    assert (h.root / "config" / "env.yaml").read_text() == "env: {}\n"
    assert (h.root / "config" / "agent.yaml").read_text() == "agent: {}\n"


def test_emit_manifest_train_symlink_resolves(tmp_path):
    log_dir = _fake_log_dir(tmp_path)
    # Put a checkpoint in the real log_dir; RunHandle must reach it through the symlink.
    (log_dir / "model_10.pt").write_text("")
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest("Isaac-ConstrainedALBC-TRPO-v0", log_dir, experiments_root=str(exp))
    train_link = h.root / "train"
    assert train_link.is_symlink()
    assert (train_link / "model_10.pt").is_file()
    # Re-resolve via resolve_run -> checkpoints_dir reaches the symlinked log_dir.
    re = P.resolve_run(h.run_id, experiments_root=str(exp))
    assert re.latest_checkpoint().name == "model_10.pt"


def test_emit_manifest_records_config_and_tag(tmp_path):
    log_dir = _fake_log_dir(tmp_path)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest(
        "Isaac-ConstrainedALBC-PPO-Enc-v0", log_dir, tag="ablation",
        config={"num_envs": 4096, "seed": 30}, experiments_root=str(exp),
    )
    # tag flows into run_id; timestamp still from the trpo-named leaf.
    assert h.run_id == "2026-05-25_16-02-48_ppo-enc_ablation"
    loaded = P.read_manifest(h.root)
    assert loaded["config"] == {"num_envs": 4096, "seed": 30}
    assert loaded["task"] == "Isaac-ConstrainedALBC-PPO-Enc-v0"


def test_emit_manifest_without_params_still_writes_manifest(tmp_path):
    log_dir = _fake_log_dir(tmp_path, with_params=False)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest("Isaac-ConstrainedALBC-TDC-v0", log_dir, experiments_root=str(exp))
    assert (h.root / P.MANIFEST_NAME).is_file()
    # No params to copy -> config dir exists but is empty of yamls.
    assert not (h.root / "config" / "env.yaml").exists()


# ---------------------------------------------------------------------------
# eval_dir_for_checkpoint: run_id-tree detection for eval output (#2)
# ---------------------------------------------------------------------------
def test_eval_dir_for_checkpoint_in_run_tree(tmp_path):
    exp = tmp_path / "experiments"
    ckpt = exp / "2026-05-25_16-02-48_trpo" / "train" / "checkpoints" / "model_4999.pt"
    out = P.eval_dir_for_checkpoint(ckpt, "static", experiments_root=str(exp), eval_ts="2026-05-25_18-00-00")
    assert out == exp / "2026-05-25_16-02-48_trpo" / "eval" / "static_2026-05-25_18-00-00"


def test_eval_dir_for_checkpoint_legacy_returns_none(tmp_path):
    # A checkpoint under logs/rsl_rl (not in the run_id tree) -> None (keep legacy default).
    ckpt = tmp_path / "logs" / "rsl_rl" / "full_dof_trpo" / "2026-05-25_16-02-48" / "model_0.pt"
    out = P.eval_dir_for_checkpoint(ckpt, "static", experiments_root=str(tmp_path / "experiments"))
    assert out is None


def test_eval_dir_for_checkpoint_detects_via_unresolved_symlink_path(tmp_path):
    """The minimal-touch layout loads ckpts via experiments/<run_id>/train (a symlink to
    logs/). Detection must use the unresolved path, so the run_id is still recognized."""
    exp = tmp_path / "experiments"
    # train is a symlink to a real logs dir; checkpoint accessed through the symlink path.
    real_logs = tmp_path / "logs" / "rsl_rl" / "full_dof_trpo" / "2026-05-25_16-02-48_trpo"
    (real_logs).mkdir(parents=True)
    (real_logs / "model_4999.pt").write_text("")
    run_root = exp / "2026-05-25_16-02-48_trpo"
    run_root.mkdir(parents=True)
    (run_root / "train").symlink_to(os.path.relpath(real_logs, run_root))
    # Path as the evaluator would see it (through the run_id tree).
    ckpt_via_tree = run_root / "train" / "model_4999.pt"
    out = P.eval_dir_for_checkpoint(ckpt_via_tree, "periodic", experiments_root=str(exp), eval_ts="2026-05-25_18-00-00")
    assert out == run_root / "eval" / "periodic_2026-05-25_18-00-00"


# ---------------------------------------------------------------------------
# run_id_from_path + student manifest linkage (#3, design section 2-C Option B)
# ---------------------------------------------------------------------------
def test_run_id_from_path_in_tree(tmp_path):
    exp = tmp_path / "experiments"
    teacher_dir = exp / "2026-05-25_16-02-48_trpo" / "train"
    assert P.run_id_from_path(teacher_dir, experiments_root=str(exp)) == "2026-05-25_16-02-48_trpo"


def test_run_id_from_path_legacy_returns_none(tmp_path):
    legacy = tmp_path / "logs" / "rsl_rl" / "fulldof_albc" / "2026-04-20_r13_A"
    assert P.run_id_from_path(legacy, experiments_root=str(tmp_path / "experiments")) is None


def test_emit_manifest_student_links_parent(tmp_path):
    log_dir = _fake_log_dir(tmp_path, leaf="2026-05-25_20-00-00_student", with_params=False)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest(
        "Isaac-ConstrainedALBC-TRPO-v0", log_dir, tag="student",
        kind="student", parent_run_id="2026-05-25_16-02-48_trpo",
        config={"teacher_run_dir": "experiments/2026-05-25_16-02-48_trpo/train"},
        experiments_root=str(exp),
    )
    loaded = P.read_manifest(h.root)
    assert loaded["kind"] == "student"
    assert loaded["parent_run_id"] == "2026-05-25_16-02-48_trpo"


def test_emit_manifest_student_without_parent_omits_link(tmp_path):
    """A teacher in the legacy layout (run_id_from_path -> None) -> student omits parent_run_id."""
    log_dir = _fake_log_dir(tmp_path, leaf="2026-05-25_20-00-00_student", with_params=False)
    exp = tmp_path / "experiments"
    h = P.emit_run_manifest(
        "Isaac-ConstrainedALBC-TRPO-v0", log_dir, tag="student",
        kind="student", parent_run_id=None, experiments_root=str(exp),
    )
    loaded = P.read_manifest(h.root)
    assert loaded["kind"] == "student"
    assert "parent_run_id" not in loaded  # omitted when None (Manifest.to_dict drops it)


# ---------------------------------------------------------------------------
# common.resolve_run_path delegation to paths.resolve_run (#5)
# ---------------------------------------------------------------------------
import common as C  # noqa: E402  sibling on the same sys.path as paths


def test_common_resolve_run_path_legacy_fullpath(tmp_path):
    """Legacy full path -> returns that dir unchanged (behavior preserved)."""
    leg = tmp_path / "logs" / "rsl_rl" / "full_dof_trpo" / "2026-05-25_16-00-00_r1"
    leg.mkdir(parents=True)
    (leg / "events.out.tfevents.1.h").write_text("")
    out = C.resolve_run_path(str(leg), logs_root=str(tmp_path / "logs" / "rsl_rl"))
    assert out == leg


def test_common_resolve_run_path_legacy_substring(tmp_path):
    logs = tmp_path / "logs" / "rsl_rl"
    leg = logs / "full_dof_trpo" / "2026-05-25_16-00-00_r1"
    leg.mkdir(parents=True)
    (leg / "events.out.tfevents.1.h").write_text("")
    out = C.resolve_run_path("r1", logs_root=str(logs))
    assert out == leg


def test_common_resolve_run_path_run_id_tree_returns_train(tmp_path):
    """run_id tree -> returns <run>/train (where tfevents + checkpoints live)."""
    run_root = tmp_path / "experiments" / "2026-05-25_17-00-00_trpo"
    (run_root / "train").mkdir(parents=True)
    (run_root / "train" / "events.out.tfevents.2.h").write_text("")
    (run_root / P.MANIFEST_NAME).write_text(
        '{"run_id": "2026-05-25_17-00-00_trpo", "task": "t", "paths": {"tb": "train"}}'
    )
    out = C.resolve_run_path(str(run_root), logs_root=str(tmp_path / "logs"))
    assert out == run_root / "train"
    assert (out / "events.out.tfevents.2.h").is_file()
