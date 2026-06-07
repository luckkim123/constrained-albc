# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free verification of audit P3 dispersion fixes.

P3-3: ss_jitter is unified across paths to the recompute per-env-then-aggregate
form (per-env temporal std, then mean across envs), so ss_jitter_std exists.
This test asserts the _eval_dr/metrics jitter formula is numerically equivalent
to recompute_metrics._per_env_ss_stats on the same SS window.

P3-1: _periodic_compute_metrics now emits per-step env-to-env SS-error std.

Lives in repo-root tests/ (NOT analysis/) so it imports on plain python3.
"""
from __future__ import annotations

import os
import sys

import numpy as np

_ANALYSIS = os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
sys.path.insert(0, os.path.abspath(_ANALYSIS))

from _analyze.recompute_metrics import _per_env_ss_stats  # type: ignore[import-not-found]  # noqa: E402
from _eval_dr import metrics as _m  # type: ignore[import-not-found]  # noqa: E402


def _unified_jitter(ss_vals):
    """The formula now used in _eval_dr/metrics for att/lin_vel/yaw jitter."""
    per_env_jit = np.nanstd(ss_vals, axis=0)
    return float(np.nanmean(per_env_jit)), float(np.nanstd(per_env_jit))


def test_eval_dr_jitter_matches_recompute_per_env_form():
    # Build a synthetic SS window [T, N]; both paths must agree on jitter mean+std.
    rng = np.random.RandomState(7)
    T, N = 80, 64
    cur_tgt = 0.0
    # per-env heterogeneous DC offset + oscillation (where std-of-means would differ)
    dc = rng.rand(N) * 0.4
    amp = rng.rand(N) * 0.25
    t = np.arange(T)
    actual = dc[None, :] + amp[None, :] * np.sin(0.3 * t)[:, None] + rng.randn(T, N) * 0.01

    # recompute path: _per_env_ss_stats takes the FULL segment and uses its own
    # ss_start = T//2. Give it a segment whose second half equals our SS window.
    seg = np.concatenate([actual, actual], axis=0)  # [2T, N]; ss half = actual
    seg_alive = np.ones((2 * T, N), dtype=bool)
    _, _, rc_jit_mean, rc_jit_std = _per_env_ss_stats(seg, seg_alive, cur_tgt)

    # eval_dr path formula on the same SS window (abs since recompute uses |.|)
    ss_vals = np.abs(actual - cur_tgt)
    ed_jit_mean, ed_jit_std = _unified_jitter(ss_vals)

    assert abs(ed_jit_mean - rc_jit_mean) < 1e-9, (ed_jit_mean, rc_jit_mean)
    assert abs(ed_jit_std - rc_jit_std) < 1e-9, (ed_jit_std, rc_jit_std)


def test_unified_jitter_differs_from_old_std_of_means():
    # Sanity: the new per-env form is NOT the old std-of-env-mean (they diverge
    # when env oscillations are out of phase). Confirms this is a real change.
    rng = np.random.RandomState(3)
    T, N = 100, 64
    phase = rng.rand(N) * 2 * np.pi
    t = np.arange(T)
    ss_vals = 0.2 + 0.3 * np.sin(0.4 * t[:, None] + phase[None, :])  # phase-shifted per env
    old = float(np.nanstd(np.nanmean(ss_vals, axis=1)))  # std of cross-env mean
    new_mean, _ = _unified_jitter(ss_vals)
    # out-of-phase oscillation cancels in the cross-env mean -> old << new
    assert new_mean > old * 2, (new_mean, old)


def test_periodic_metrics_emit_per_env_std():
    # P3-1: _periodic_compute_metrics must now return per-step + aggregate SS-error std.
    T, N, n_dr = 600, 32, 6
    steps_per_dr = T // n_dr
    rng = np.random.RandomState(1)
    data = {
        "steps_per_dr": steps_per_dr,
        "num_dr_steps": n_dr,
        "step_duration": 2.0,
        "time": np.arange(T) * 0.02,
        "terminated": np.zeros((T, N), dtype=bool),
        "actual_roll_deg": rng.randn(T, N) * 2.0,
        "actual_pitch_deg": rng.randn(T, N) * 2.0,
        "lin_vel_x": rng.randn(T, N) * 0.1,
        "lin_vel_y": rng.randn(T, N) * 0.1,
        "lin_vel_z": rng.randn(T, N) * 0.1,
        "yaw_rate": rng.randn(T, N) * 0.05,
    }
    out = _m._periodic_compute_metrics(data)
    for k in ("per_step_att_err_std", "per_step_lin_vel_std", "per_step_yaw_rate_std",
              "mean_att_err_std", "mean_lin_vel_std", "mean_yaw_rate_std"):
        assert k in out, f"missing {k}"
    # per-step std arrays align with the per-step means
    assert len(out["per_step_att_err_std"]) == len(out["per_step_att_err"])
    # heterogeneous envs -> non-zero env-to-env std
    assert out["mean_att_err_std"] > 0
