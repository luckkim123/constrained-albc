# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free checks for the depthxy exam schedule and metrics (_eval_dr/depthxy.py)."""

from __future__ import annotations

import math
import os
import sys

import numpy as np
import pytest

_ANALYSIS = os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
sys.path.insert(0, os.path.abspath(_ANALYSIS))

from _eval_dr import depthxy as dx  # type: ignore[import-not-found]  # noqa: E402

DT = 0.02
TAU = 0.5


def test_schedule_segments_and_commands():
    s = dx.build_depthxy_schedule(DT)
    starts = s["seg_start"]
    assert len(s["time"]) == starts[-1] == 4100
    assert [float(s["depth_offset"][a]) for a in starts[:-1]] == pytest.approx(
        [0.0, 0.3, 0.0, -0.3, 0.0, 0.0, 0.0, 0.0, 0.0, 0.0]
    )
    assert [tuple(s["u_xy"][a].tolist()) for a in starts[5:9]] == [(1, 0), (0, 1), (-1, 0), (0, -1)]
    for a, b in zip(starts[:-1], starts[1:]):
        assert np.all(s["depth_offset"][a:b] == s["depth_offset"][a])
        assert np.all(s["u_xy"][a:b] == s["u_xy"][a])


def _synthetic():
    """env0/env2: first-order depth response (tau 0.5 s); env1: constant +0.1 m; env2 dies in 'xy +x'."""
    s = dx.build_depthxy_schedule(DT)
    T, n = len(s["time"]), 3
    tgt = 0.5 + s["depth_offset"].astype(np.float64)
    ez = np.zeros(T)
    for a, b in zip(s["seg_start"][:-1], s["seg_start"][1:]):
        step = tgt[a] - (tgt[a - 1] if a else tgt[0])
        ez[a:b] = -step * np.exp(-(np.arange(b - a) + 1) * DT / TAU)
    depth = np.stack([tgt + ez, tgt + 0.1, tgt + ez], axis=1)
    cmd = np.repeat(s["u_xy"][:, None, :] * 8.0, n, axis=1)
    roll = np.tile([1.0, 2.0, 3.0], (T, 1))
    terminated = np.zeros((T, n), dtype=bool)
    k = int(s["seg_start"][5]) + 10
    terminated[k, 2] = True
    depth[k:, 2] = 99.0  # post-reset garbage must never reach a statistic
    roll[k:, 2] = 99.0
    return {
        **s,
        "depth": depth,
        "depth_target": np.repeat(tgt[:, None], n, axis=1),
        "force_xy": cmd + np.array([0.5, 0.0]),
        "force_cmd_xy": cmd,
        "roll_err_deg": roll,
        "pitch_err_deg": -roll,
        "terminated": terminated,
    }


def test_metrics_settling_overshoot_force_and_termination():
    m = dx.compute_depthxy_metrics(_synthetic(), DT)
    seg = {g["name"]: g for g in m["segments"]}
    assert m["n_terminated"] == 1 and m["survival_frac"] == pytest.approx(2 / 3)

    assert "depth_settle_s" not in seg["hover"]
    up = seg["depth +0.3"]
    assert up["depth_step_m"] == pytest.approx(0.3) and up["n_envs"] == 3
    assert up["depth_settled_frac"] == pytest.approx(2 / 3)  # env1 never enters the 0.05 m band
    assert abs(up["depth_settle_s"]["median"] - TAU * math.log(0.3 / 0.05)) <= DT
    assert up["depth_overshoot_m"]["max"] == pytest.approx(0.1)  # env1 sits 0.1 m past a downward target
    assert up["depth_ss_err_m"]["max"] == pytest.approx(0.1)
    assert seg["depth -0.3"]["depth_overshoot_m"]["max"] == pytest.approx(0.0)
    assert seg["depth return 1"]["depth_step_m"] == pytest.approx(-0.3)

    xy = seg["xy +x"]
    assert xy["n_envs"] == 2 and xy["alive_frac_end"] == pytest.approx(2 / 3)
    assert xy["roll_abs_max_deg"]["max"] == pytest.approx(2.0)
    assert xy["depth_ss_err_m"]["max"] == pytest.approx(0.1)
    assert xy["force_err_N"]["mean"] == pytest.approx(0.5)
    assert seg["hover"]["roll_abs_max_deg"]["max"] == pytest.approx(3.0)


def test_stats_empty_and_markdown_renders():
    assert dx._stats(np.array([np.nan])) == {"mean": None, "median": None, "p90": None, "max": None, "n": 0}
    res = dx.compute_depthxy_metrics(_synthetic(), DT)
    md = dx.render_depthxy_markdown({"meta": {"task": "t"}, "none": {**res, "n_truncated": 0, "override_ok": True}})
    assert md.count("\n| ") == 1 + len(dx.SCHEDULE)  # header + one row per segment
