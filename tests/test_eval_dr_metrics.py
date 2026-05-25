# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Regression tests for the pure metric helpers extracted to _eval_dr/metrics.py.

These functions were lifted verbatim out of eval_dr.py during the Phase 3 god-file
split. eval_dr.py itself needs a booted Isaac Sim app to import, but metrics.py is
pure numpy/dict, so these tests pin its behavior with synthetic data dicts on plain
python3 (no sim, no GPU). The split was byte-identical; this is the safety net that
catches any future edit that breaks the contracts:

    1. _classify_segment: name -> block type, with "warmup" winning over co-occurring
       keywords (the mechanism that excludes inter-block warmups from metrics).
    2. _get_block_step_range: (start, end) spanning contiguous segments; (0, 0) absent.
    3. _pick_sample_env: median-attitude-error env index; None when num_envs <= 1.
    4. _settling_time: time until signal stays within band permanently (last-exceed+1).
    5. compute_metrics / compute_seg_metrics: end-to-end on a perfect-tracking
       trajectory -> SS error ~ 0, survival 100%, NaN-free dict, peak >= ss.
"""

from __future__ import annotations

import os
import sys

import numpy as np
import pytest

# metrics.py is pure numpy; import the _eval_dr sibling package directly.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis"))
from _eval_dr.metrics import (  # noqa: E402
    _classify_segment,
    _get_block_step_range,
    _pick_sample_env,
    _settling_time,
    _step_response_scalar_segment,
    compute_metrics,
    compute_seg_metrics,
)
from _eval_dr.trajectory import build_step_trajectory  # noqa: E402


# ---------------------------------------------------------------------------
# _classify_segment
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "name, expected",
    [
        ("warmup (init)", "warmup"),
        ("warmup (pre-lin_vel)", "warmup"),  # warmup wins over the "lin_vel" substring
        ("att (-15, 0)", "attitude"),
        ("att zero (post-warmup)", "warmup"),  # warmup wins over the "att" prefix
        ("vxyz (+, +, +)", "lin_vel"),
        ("yaw +0.25", "yaw"),
        ("something else", "unknown"),
    ],
)
def test_classify_segment(name, expected):
    assert _classify_segment(name) == expected


def test_classify_segment_warmup_priority():
    """warmup is checked first, so it must win even when another keyword co-occurs."""
    assert _classify_segment("warmup before att roll pitch vxyz yaw") == "warmup"


# ---------------------------------------------------------------------------
# _get_block_step_range
# ---------------------------------------------------------------------------
def test_get_block_step_range_contiguous():
    names = ["warmup", "att (0,0)", "att (a,0)", "warmup", "vxyz (+,+,+)"]
    spp = 10
    # attitude spans segments 1..2 -> steps [10, 30)
    assert _get_block_step_range(names, spp, "attitude") == (10, 30)
    # lin_vel is the single segment 4 -> steps [40, 50)
    assert _get_block_step_range(names, spp, "lin_vel") == (40, 50)


def test_get_block_step_range_absent():
    names = ["warmup", "att (0,0)"]
    assert _get_block_step_range(names, 10, "yaw") == (0, 0)


# ---------------------------------------------------------------------------
# _pick_sample_env
# ---------------------------------------------------------------------------
def test_pick_sample_env_picks_median():
    # 3 envs with distinct constant attitude error -> median env is index 1.
    t, n = 5, 3
    d = {
        "error_roll": np.tile(np.array([1.0, 5.0, 9.0]), (t, 1)),
        "error_pitch": np.zeros((t, n)),
    }
    assert _pick_sample_env(d) == 1


def test_pick_sample_env_single_env_returns_none():
    d = {"error_roll": np.ones((5, 1)), "error_pitch": np.zeros((5, 1))}
    assert _pick_sample_env(d) is None


def test_pick_sample_env_missing_key_returns_none():
    assert _pick_sample_env({}) is None


# ---------------------------------------------------------------------------
# _settling_time
# ---------------------------------------------------------------------------
def test_settling_time_already_within_band():
    sig = np.full(10, 0.5)
    assert _settling_time(sig, threshold=1.0, step_dt=0.02) == 0.0


def test_settling_time_settles_midway():
    # Exceeds threshold for first 5 steps, then stays under it.
    sig = np.array([2.0] * 5 + [0.1] * 5)
    # Last step above threshold is index 4 -> settle at (4 + 1) * dt.
    assert _settling_time(sig, threshold=1.0, step_dt=0.02) == pytest.approx(5 * 0.02)


def test_settling_time_never_settles():
    sig = np.full(10, 5.0)  # last step still above -> NaN
    assert np.isnan(_settling_time(sig, threshold=1.0, step_dt=0.02))


def test_settling_time_transient_dip_does_not_count():
    """A signal that dips into band then leaves again settles at the LAST exceed, not the first."""
    sig = np.array([2.0, 0.1, 0.1, 2.0, 0.1, 0.1])  # last exceed at index 3
    assert _settling_time(sig, threshold=1.0, step_dt=0.02) == pytest.approx(4 * 0.02)


# ---------------------------------------------------------------------------
# _step_response_scalar_segment
# ---------------------------------------------------------------------------
def test_step_response_scalar_below_min_step_is_nan():
    seg_time = np.arange(10) * 0.02
    actual = np.zeros((10, 2))
    alive = np.ones((10, 2), dtype=bool)
    rt, os_pct = _step_response_scalar_segment(actual, alive, prev_target=0.0, cur_target=0.005, seg_time=seg_time)
    assert np.isnan(rt) and np.isnan(os_pct)


def test_step_response_scalar_instant_track_zero_rise_no_overshoot():
    seg_time = np.arange(10) * 0.02
    actual = np.full((10, 2), 1.0)  # already at target the whole segment
    alive = np.ones((10, 2), dtype=bool)
    rt, os_pct = _step_response_scalar_segment(actual, alive, prev_target=0.0, cur_target=1.0, seg_time=seg_time)
    assert rt == pytest.approx(0.0)
    assert os_pct == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# compute_metrics / compute_seg_metrics: end-to-end on perfect tracking
# ---------------------------------------------------------------------------
def _build_perfect_tracking_static_data(num_envs: int = 4, seg_duration: float = 1.0, step_dt: float = 0.02) -> dict:
    """Synthesize a static-mode data dict where the actual state instantly equals the target.

    Uses the real build_step_trajectory so segment names / steps_per_segment match
    production exactly. Actual == target everywhere -> SS error ~ 0, survival 100%.
    """
    time_s, targets, seg_names, _ = build_step_trajectory(seg_duration, step_dt)
    total_steps = len(time_s)
    steps_per_segment = int(seg_duration / step_dt)

    def col(arr_1d):  # (T,) -> (T, num_envs), perfect tracking across all envs
        return np.tile(arr_1d[:, None], (1, num_envs))

    actual_roll = col(targets["roll_deg"])
    actual_pitch = col(targets["pitch_deg"])
    return {
        "time": time_s,
        "steps_per_segment": steps_per_segment,
        "segment_names": seg_names,
        "segment_duration": seg_duration,
        "terminated": np.zeros((total_steps, num_envs), dtype=bool),  # all alive
        # Attitude: actual == target
        "target_roll_deg": targets["roll_deg"],
        "target_pitch_deg": targets["pitch_deg"],
        "actual_roll_deg": actual_roll,
        "actual_pitch_deg": actual_pitch,
        "error_roll": np.zeros((total_steps, num_envs)),
        "error_pitch": np.zeros((total_steps, num_envs)),
        # Linear velocity: actual == target
        "lin_vel_x": col(targets["vx"]),
        "lin_vel_y": col(targets["vy"]),
        "lin_vel_z": col(targets["vz"]),
        "target_vx": targets["vx"],
        "target_vy": targets["vy"],
        "target_vz": targets["vz"],
        "lin_vel_norm": np.zeros((total_steps, num_envs)),  # |actual - target| norm = 0
        # Yaw rate: actual == target
        "yaw_rate": col(targets["yaw_rate"]),
        "target_yaw_rate": targets["yaw_rate"],
    }


def test_compute_metrics_perfect_tracking():
    m = compute_metrics(_build_perfect_tracking_static_data())

    # Survival: nobody terminated.
    assert m["survival_rate"] == pytest.approx(100.0)
    assert m["lin_vel_survival"] == pytest.approx(100.0)
    assert m["yaw_survival"] == pytest.approx(100.0)

    # Steady-state errors are ~ 0 under perfect tracking.
    assert m["total_att_error"] == pytest.approx(0.0, abs=1e-9)
    assert m["total_lin_vel_error"] == pytest.approx(0.0, abs=1e-9)
    assert m["total_yaw_rate_error"] == pytest.approx(0.0, abs=1e-9)

    # Per-segment SS errors collected. The attitude block has 11 segments:
    # 3x3 grid (9) + return-to-neutral doubled (2); "att zero (post-warmup)"
    # is classified as warmup, so it is excluded.
    assert len(m["att_ss_errors"]) == 11
    assert np.allclose(np.array(m["att_ss_errors"]), 0.0, atol=1e-9)

    # Per-axis lin_vel SS errors keyed by axis, each ~ 0.
    for ax in ("vx", "vy", "vz"):
        assert len(m["lin_vel_ss_errors"][ax]) == 10
        assert np.allclose(np.array(m["lin_vel_ss_errors"][ax]), 0.0, atol=1e-9)


# An env terminated from step 0 is all-NaN along the time axis, so the per-env
# std uses an empty slice -> RuntimeWarning. This is the original code's intended
# behavior (the block mean still ignores it via nanmean); absorb it here.
@pytest.mark.filterwarnings("ignore:Mean of empty slice:RuntimeWarning")
def test_compute_metrics_terminated_envs_drop_survival():
    data = _build_perfect_tracking_static_data(num_envs=4)
    # Terminate 1 of 4 envs from the start -> 75% survival.
    data["terminated"][:, 0] = True
    m = compute_metrics(data)
    assert m["survival_rate"] == pytest.approx(75.0)


def _build_segmented_data(num_envs: int = 4, num_segments: int = 3, steps_per_segment: int = 20) -> dict:
    """Synthesize a segmented-mode data dict with bounded, constant-per-seg states."""
    total = num_segments * steps_per_segment
    rng = np.random.default_rng(0)
    # Bounded small attitudes / positions so peak >= ss always holds.
    return {
        "steps_per_segment": steps_per_segment,
        "num_segments": num_segments,
        "segment_duration": steps_per_segment * 0.02,
        "actual_roll_deg": rng.uniform(-5, 5, (total, num_envs)),
        "actual_pitch_deg": rng.uniform(-5, 5, (total, num_envs)),
        "actual_yaw_deg": rng.uniform(-10, 10, (total, num_envs)),
        "pos_x": rng.uniform(-0.1, 0.1, (total, num_envs)),
        "pos_y": rng.uniform(-0.1, 0.1, (total, num_envs)),
        "pos_z": rng.uniform(-0.1, 0.1, (total, num_envs)),
    }


def test_compute_seg_metrics_shape_and_peak_ge_ss():
    num_envs, num_segments = 4, 3
    out = compute_seg_metrics(_build_segmented_data(num_envs, num_segments))

    assert out["num_envs"] == num_envs
    assert out["num_segments"] == num_segments
    assert len(out["per_seg"]) == num_segments

    for seg in out["per_seg"]:
        # peak (max over time) must be >= ss (mean over last half) per env.
        for peak_key, ss_key in [
            ("peak_roll_deg", "ss_roll_deg"),
            ("peak_pitch_deg", "ss_pitch_deg"),
            ("peak_yaw_deg", "ss_yaw_deg"),
            ("pos_drift_peak", "pos_drift_ss"),
        ]:
            peak = np.array(seg[peak_key])
            ss = np.array(seg[ss_key])
            assert peak.shape == (num_envs,)
            assert np.all(peak >= ss - 1e-9)
