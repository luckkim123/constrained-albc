# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for recompute metric core (split from recompute.py god-file)."""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from _analyze.recompute_metrics import (  # noqa: E402
    _compute_enhanced_metrics,
    _per_env_ss_stats,
    _per_env_ss_vectors,
)
from _eval_dr.trajectory import build_step_trajectory  # noqa: E402


def test_per_env_ss_stats_perfect_tracking_is_zero():
    """Perfect tracking -> SS error and jitter both ~0."""
    n_steps, n_envs = 200, 4
    actual = np.zeros((n_steps, n_envs))
    alive = np.ones((n_steps, n_envs), dtype=bool)
    ss_err_mean, ss_err_std, ss_jit_mean, ss_jit_std = _per_env_ss_stats(actual, alive, cur_tgt=0.0)
    assert abs(ss_err_mean) < 1e-9
    assert ss_jit_mean < 1e-9


def test_per_env_ss_stats_constant_error():
    """Constant offset -> SS error equals offset, jitter ~0."""
    n_steps, n_envs = 200, 4
    offset = 2.5
    actual = np.full((n_steps, n_envs), offset)
    alive = np.ones((n_steps, n_envs), dtype=bool)
    ss_err_mean, _, ss_jit_mean, _ = _per_env_ss_stats(actual, alive, cur_tgt=0.0)
    assert abs(ss_err_mean - offset) < 1e-6
    assert ss_jit_mean < 1e-9


def test_per_env_vectors_are_what_the_scalars_reduce():
    """_per_env_ss_stats must be exactly the reduction of _per_env_ss_vectors.

    Guards the delegation: if the stats function grows its own second copy of the
    masking/window logic, these stop agreeing.
    """
    rng = np.random.default_rng(0)
    actual = rng.normal(size=(200, 8))
    alive = np.ones((200, 8), dtype=bool)
    pe_mean, pe_std = _per_env_ss_vectors(actual, alive, cur_tgt=0.3)
    ss_err, ss_err_std, ss_jit, ss_jit_std = _per_env_ss_stats(actual, alive, cur_tgt=0.3)
    assert np.isclose(np.nanmean(pe_mean), ss_err)
    assert np.isclose(np.nanstd(pe_mean), ss_err_std)
    assert np.isclose(np.nanmean(pe_std), ss_jit)
    assert np.isclose(np.nanstd(pe_std), ss_jit_std)


def _write_offset_npz(tmp_path, offsets):
    """Attitude-only eval npz where env i tracks roll/pitch with a constant offset."""
    time_s, targets, _names, _ = build_step_trajectory(1.0, 0.02)
    n_steps, n_envs = len(time_s), len(offsets)
    off = np.asarray(offsets, dtype=float)[None, :]

    def col(a):
        return np.tile(a[:, None], (1, n_envs))

    payload = {
        "time": time_s,
        "terminated": np.zeros((n_steps, n_envs), dtype=bool),
        "target_roll_deg": targets["roll_deg"],
        "target_pitch_deg": targets["pitch_deg"],
        "target_yaw_rate": targets["yaw_rate"],
        "actual_roll_deg": col(targets["roll_deg"]) + off,
        "actual_pitch_deg": col(targets["pitch_deg"]),
        "error_roll": np.zeros((n_steps, n_envs)) + off,
        "error_pitch": np.zeros((n_steps, n_envs)),
        "yaw_rate": col(targets["yaw_rate"]),
    }
    path = tmp_path / "data_none.npz"
    np.savez_compressed(path, **payload)
    return path


def test_per_env_vector_reproduces_scalar(tmp_path):
    """The whole reason with_per_env exists: mean(per_env[ax]) == out[ax]["ss_error"].

    A paired cross-run comparison is only sound if the per-env vector is the same
    quantity the published scalar summarizes. A hand reimplementation of this
    metric missed the published value by up to 3.6x the 0.10 deg decision floor,
    so the equivalence is asserted rather than assumed.
    """
    offsets = [0.5, 1.0, 1.5, 2.0]
    m = _compute_enhanced_metrics(str(_write_offset_npz(tmp_path, offsets)), with_per_env=True)

    per_env = m["per_env"]["roll"]
    assert len(per_env) == len(offsets)
    assert np.isclose(np.nanmean(per_env), m["roll"]["ss_error"])
    # and it really is per-env, not a broadcast scalar
    assert np.allclose(sorted(per_env), sorted(offsets), atol=1e-6)
    # att_norm goes through the same helper, so it must agree too
    assert np.isclose(np.nanmean(m["per_env"]["att_norm"]), m["att_norm"]["ss_error"])


def test_per_env_is_off_by_default(tmp_path):
    """summary.json must stay byte-identical for callers that do not ask for it."""
    m = _compute_enhanced_metrics(str(_write_offset_npz(tmp_path, [0.5, 1.0])))
    assert "per_env" not in m
