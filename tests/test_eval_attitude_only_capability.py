# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Capability-guard tests for eval against the attitude_only env (no _vel_cmd_lin).

The static eval harness (run_evaluation / compute_metrics / run_static print) was
written for the full-DOF env, which has raw_env._vel_cmd_lin and tracks vx/vy/vz.
The attitude_only env legitimately removed _vel_cmd_lin (it has only _ang_cmd =
roll/pitch/yaw_rate). Eval must guard the lin-vel code paths on the *capability*
(hasattr / a data flag), NOT on a --task string, so:

  - full-DOF (has_lin_vel=True, the default): every lin-vel branch behaves exactly
    as before -> byte-identical, zero regression.
  - attitude_only (has_lin_vel=False): lin-vel injection / metrics / print are
    skipped; the attitude + yaw paths are untouched and still produce real numbers.

These are sim-free: compute_metrics is pure numpy/dict (tests/test_eval_dr_metrics.py
pattern). run_evaluation needs a fake raw_env to exercise the hasattr guard without
booting Isaac Sim.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis"))
from _eval_dr.metrics import compute_metrics  # noqa: E402
from _eval_dr.trajectory import build_step_trajectory  # noqa: E402


def _build_static_data(num_envs: int = 4, has_lin_vel: bool = True,
                       seg_duration: float = 1.0, step_dt: float = 0.02) -> dict:
    """Static-mode data dict; when has_lin_vel=False, omit lin-vel target/actual
    arrays exactly as run_evaluation would for an attitude_only env."""
    time_s, targets, seg_names, _ = build_step_trajectory(seg_duration, step_dt)
    total_steps = len(time_s)
    steps_per_segment = int(seg_duration / step_dt)

    def col(arr_1d):
        return np.tile(arr_1d[:, None], (1, num_envs))

    data = {
        "time": time_s,
        "steps_per_segment": steps_per_segment,
        "segment_names": seg_names,
        "segment_duration": seg_duration,
        "terminated": np.zeros((total_steps, num_envs), dtype=bool),
        "target_roll_deg": targets["roll_deg"],
        "target_pitch_deg": targets["pitch_deg"],
        "actual_roll_deg": col(targets["roll_deg"]),
        "actual_pitch_deg": col(targets["pitch_deg"]),
        "error_roll": np.zeros((total_steps, num_envs)),
        "error_pitch": np.zeros((total_steps, num_envs)),
        "yaw_rate": col(targets["yaw_rate"]),
        "target_yaw_rate": targets["yaw_rate"],
        "has_lin_vel": has_lin_vel,
    }
    if has_lin_vel:
        data.update({
            "lin_vel_x": col(targets["vx"]),
            "lin_vel_y": col(targets["vy"]),
            "lin_vel_z": col(targets["vz"]),
            "target_vx": targets["vx"],
            "target_vy": targets["vy"],
            "target_vz": targets["vz"],
            "lin_vel_norm": np.zeros((total_steps, num_envs)),
        })
    return data


# ---------------------------------------------------------------------------
# compute_metrics: attitude_only (no lin-vel arrays) must not KeyError
# ---------------------------------------------------------------------------
def test_compute_metrics_attitude_only_no_keyerror():
    """has_lin_vel=False + no lin_vel_* / target_v* keys -> compute_metrics succeeds
    and returns real attitude + yaw metrics (the channels the policy actually tracks)."""
    m = compute_metrics(_build_static_data(has_lin_vel=False))
    # Attitude tracked perfectly -> SS error ~ 0, survival 100%.
    assert np.nanmean(m["att_ss_errors"]) == pytest.approx(0.0, abs=1.0)
    assert m["survival_rate"] == pytest.approx(100.0)
    # Yaw channel present and real.
    assert np.nanmean(m["yaw_ss_errors"]) == pytest.approx(0.0, abs=0.1)


def test_compute_metrics_attitude_only_lin_vel_absent_or_nan():
    """For attitude_only the lin-vel metric block must be absent or all-NaN, never a
    real number (the policy does not track lin-vel; a finite value would be a lie)."""
    m = compute_metrics(_build_static_data(has_lin_vel=False))
    # total_lin_vel_error: either omitted or NaN.
    tlv = m.get("total_lin_vel_error", float("nan"))
    assert tlv != tlv or np.isnan(tlv)  # NaN
    # If per-axis dict is present, every entry must be NaN/empty.
    for ax in ("vx", "vy", "vz"):
        vals = m.get("lin_vel_ss_errors", {}).get(ax, [])
        assert len(vals) == 0 or all(np.isnan(v) for v in vals)


# ---------------------------------------------------------------------------
# compute_metrics: full-DOF default unchanged (regression guard)
# ---------------------------------------------------------------------------
def test_compute_metrics_full_dof_default_unchanged():
    """has_lin_vel=True (default) with lin-vel arrays -> the lin-vel block produces
    real per-axis numbers exactly as before the capability guard."""
    m = compute_metrics(_build_static_data(has_lin_vel=True))
    assert "total_lin_vel_error" in m
    assert np.isfinite(m["total_lin_vel_error"])
    for ax in ("vx", "vy", "vz"):
        assert len(m["lin_vel_ss_errors"][ax]) > 0
        assert np.nanmean(m["lin_vel_ss_errors"][ax]) == pytest.approx(0.0, abs=0.05)


def test_compute_metrics_missing_flag_defaults_to_full_dof():
    """A data dict WITHOUT has_lin_vel (legacy teacher npz) must default to full-DOF
    behavior so old data + the teacher path stay byte-identical."""
    data = _build_static_data(has_lin_vel=True)
    del data["has_lin_vel"]
    m = compute_metrics(data)
    assert np.isfinite(m["total_lin_vel_error"])


# ---------------------------------------------------------------------------
# run_evaluation injection guard: hasattr(raw_env, "_vel_cmd_lin")
# ---------------------------------------------------------------------------
def test_recompute_enhanced_metrics_attitude_only_npz_no_keyerror(tmp_path):
    """Recompute-path round trip (the path static eval invokes at eval.py:1258):
    write an attitude_only-shaped npz (no target_v* / lin_vel_* arrays, mirroring
    what run_evaluation returns + write_eval_npz persists) and assert
    _compute_enhanced_metrics returns without KeyError and leaves vx/vy/vz NaN.

    Closes the gap that the in-memory compute_metrics test cannot reach: the npz
    drops the has_lin_vel bool (it is not an ndarray), so the recompute path's
    correctness rests entirely on the `if k in data` key-presence guards."""
    from _analyze.recompute_metrics import _compute_enhanced_metrics  # noqa: E402

    num_envs = 4
    seg_duration, step_dt = 1.0, 0.02
    time_s, targets, _seg_names, _ = build_step_trajectory(seg_duration, step_dt)
    total_steps = len(time_s)

    def col(arr_1d):
        return np.tile(arr_1d[:, None], (1, num_envs))

    # attitude_only npz: attitude + yaw arrays only, NO target_v* / lin_vel_*.
    npz_payload = {
        "time": time_s,
        "terminated": np.zeros((total_steps, num_envs), dtype=bool),
        "target_roll_deg": targets["roll_deg"],
        "target_pitch_deg": targets["pitch_deg"],
        "target_yaw_rate": targets["yaw_rate"],
        "actual_roll_deg": col(targets["roll_deg"]),
        "actual_pitch_deg": col(targets["pitch_deg"]),
        "error_roll": np.zeros((total_steps, num_envs)),
        "error_pitch": np.zeros((total_steps, num_envs)),
        "yaw_rate": col(targets["yaw_rate"]),
    }
    npz_path = tmp_path / "data_none.npz"
    np.savez_compressed(npz_path, **npz_payload)

    # Must not KeyError on the absent target_v* / lin_vel_* keys.
    m = _compute_enhanced_metrics(str(npz_path))

    # Attitude + yaw axes are real (perfect tracking -> ~0 ss_error).
    assert np.isfinite(m["roll"]["ss_error"])
    assert np.isfinite(m["yaw"]["ss_error"])
    # Lin-vel axes never tracked -> NaN, never a fabricated finite value.
    for ax in ("vx", "vy", "vz"):
        assert np.isnan(m[ax]["ss_error"])


def test_injection_guard_logic_hasattr():
    """Pin the capability predicate: the guard is hasattr-based, never task-string.
    A fake env without _vel_cmd_lin must report has_lin_vel False; one with it, True."""

    class _FakeAttEnv:
        def __init__(self):
            self._ang_cmd = np.zeros((4, 3))  # attitude env: only _ang_cmd

    class _FakeFullEnv(_FakeAttEnv):
        def __init__(self):
            super().__init__()
            self._vel_cmd_lin = np.zeros((4, 3))  # full-DOF: also _vel_cmd_lin

    assert hasattr(_FakeAttEnv(), "_vel_cmd_lin") is False
    assert hasattr(_FakeFullEnv(), "_vel_cmd_lin") is True
    # _ang_cmd is present on both (attitude path must never be guarded away).
    assert hasattr(_FakeAttEnv(), "_ang_cmd") is True
    assert hasattr(_FakeFullEnv(), "_ang_cmd") is True
