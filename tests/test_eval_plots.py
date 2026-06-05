# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for the sim-free plotting helpers extracted from eval.py.

eval.py needs a booted Isaac Sim app to import; eval_plots.py is pure
matplotlib/numpy, so these tests pin behavior on plain python3 (no sim, no GPU).
Pattern mirrors tests/test_eval_dr_metrics.py.
"""

from __future__ import annotations

import os
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from eval_plots import _bar_subplot  # noqa: E402


def test_bar_subplot_draws_bars_without_error():
    fig, ax = plt.subplots()
    _bar_subplot(
        ax,
        x=[0, 1, 2, 3],
        values=[1.0, 2.0, 3.0, 4.0],
        colors=["#2196F3", "#4CAF50", "#FF9800", "#F44336"],
        xlabels=["none", "soft", "medium", "hard"],
        ylabel="error",
        title="test",
    )
    assert len(ax.patches) == 4  # one bar per value
    assert ax.get_ylabel() == "error"
    plt.close(fig)


def test_bar_subplot_applies_ylim_and_yerr():
    fig, ax = plt.subplots()
    _bar_subplot(
        ax,
        x=[0, 1],
        values=[1.0, 2.0],
        colors=["#2196F3", "#4CAF50"],
        xlabels=["a", "b"],
        ylabel="y",
        title="t",
        ylim=(0, 5),
        yerr=[0.1, 0.2],
    )
    assert ax.get_ylim() == (0.0, 5.0)
    plt.close(fig)


def test_collect_metric_across_levels():
    from eval_plots import _collect_metric_across_levels

    # real input shape: all_metrics[level]["num_segments"] + ["per_seg"][seg][key]
    # the func iterates range(1, num_segments), so seg 0 is ignored
    # int-keyed per_seg; returns (means, stds) via np.nanmean/np.nanstd
    all_metrics = {
        "none": {"num_segments": 2, "per_seg": {0: {"ss": [9.0]}, 1: {"ss": [0.1, 0.3]}}},
        "hard": {"num_segments": 2, "per_seg": {0: {"ss": [9.0]}, 1: {"ss": [0.5, 0.7]}}},
    }
    means, stds = _collect_metric_across_levels(all_metrics, ["none", "hard"], "ss", stat="mean")
    assert len(means) == 2 and len(stds) == 2
    # seg 0 is ignored; mean of [0.1, 0.3] = 0.2, mean of [0.5, 0.7] = 0.6
    assert abs(means[0] - 0.2) < 1e-9
    assert abs(means[1] - 0.6) < 1e-9
    # nanstd of [0.1, 0.3] = 0.1, nanstd of [0.5, 0.7] = 0.1
    assert abs(stds[0] - 0.1) < 1e-9
    assert abs(stds[1] - 0.1) < 1e-9


def test_generate_plots_produces_pngs(tmp_path):
    """generate_plots on a synthetic all_data/all_metrics dict writes the expected PNGs."""
    from eval_plots import generate_plots

    rng = np.random.default_rng(0)
    n_envs = 4
    # 3 segments: attitude x2, lin_vel x1, yaw x1 -- 50 steps each
    seg_names = ["att_0deg_0deg", "att_10deg_5deg", "linvel_0.2_0_0", "yaw_0.3"]
    steps_per_seg = 50
    n_steps = len(seg_names) * steps_per_seg
    levels = ["none", "hard"]

    def _make_level():
        return {
            "segment_names": seg_names,
            "steps_per_segment": steps_per_seg,
            "time": np.arange(n_steps) * 0.02,
            "terminated": np.zeros((n_steps, n_envs), dtype=bool),
            "actual_roll_deg": rng.standard_normal((n_steps, n_envs)) * 2.0,
            "actual_pitch_deg": rng.standard_normal((n_steps, n_envs)) * 2.0,
            "target_roll_deg": np.zeros(n_steps),
            "target_pitch_deg": np.zeros(n_steps),
            "lin_vel_x": rng.standard_normal((n_steps, n_envs)) * 0.05,
            "lin_vel_y": rng.standard_normal((n_steps, n_envs)) * 0.05,
            "lin_vel_z": rng.standard_normal((n_steps, n_envs)) * 0.05,
            "target_vx": np.zeros(n_steps),
            "target_vy": np.zeros(n_steps),
            "target_vz": np.zeros(n_steps),
            "yaw_rate": rng.standard_normal((n_steps, n_envs)) * 0.05,
            "target_yaw_rate": np.zeros(n_steps),
            "error_roll": rng.standard_normal((n_steps, n_envs)) * 2.0,
            "error_pitch": rng.standard_normal((n_steps, n_envs)) * 2.0,
            "action_magnitude": rng.standard_normal((n_steps, n_envs)) * 0.1,
            "time_to_failure": np.full(n_envs, float("nan")),
        }

    all_data = {lvl: _make_level() for lvl in levels}

    # all_metrics: keys expected by _plot_summary_* functions
    def _make_metrics():
        return {
            "att_ss_errors": rng.uniform(0, 5, n_envs),
            "att_ss_jitters": rng.uniform(0, 2, n_envs),
            "att_settling_times": rng.uniform(0, 3, n_envs),
            "att_overshoot_pcts": rng.uniform(0, 20, n_envs),
            "att_rise_times": rng.uniform(0, 2, n_envs),
            "att_zero_crossings": rng.integers(0, 5, n_envs).astype(float),
            "lin_vel_ss_errors": {"vx": rng.uniform(0, 0.1, n_envs),
                                  "vy": rng.uniform(0, 0.1, n_envs),
                                  "vz": rng.uniform(0, 0.1, n_envs)},
            "lin_vel_ss_jitters": {"vx": rng.uniform(0, 0.05, n_envs),
                                   "vy": rng.uniform(0, 0.05, n_envs),
                                   "vz": rng.uniform(0, 0.05, n_envs)},
            "lin_vel_rise_times": {"vx": rng.uniform(0, 2, n_envs),
                                   "vy": rng.uniform(0, 2, n_envs),
                                   "vz": rng.uniform(0, 2, n_envs)},
            "lin_vel_overshoot_pcts": {"vx": rng.uniform(0, 20, n_envs),
                                       "vy": rng.uniform(0, 20, n_envs),
                                       "vz": rng.uniform(0, 20, n_envs)},
            "lin_vel_zero_crossings": {"vx": rng.integers(0, 5, n_envs).astype(float),
                                       "vy": rng.integers(0, 5, n_envs).astype(float),
                                       "vz": rng.integers(0, 5, n_envs).astype(float)},
            "lin_vel_survival": 100.0,
            "yaw_ss_errors": rng.uniform(0, 0.1, n_envs),
            "yaw_ss_jitters": rng.uniform(0, 0.05, n_envs),
            "yaw_overshoot_pcts": rng.uniform(0, 20, n_envs),
            "yaw_rise_times": rng.uniform(0, 2, n_envs),
            "yaw_zero_crossings": rng.integers(0, 5, n_envs).astype(float),
            "yaw_survival": 100.0,
        }

    all_metrics = {lvl: _make_metrics() for lvl in levels}

    generate_plots(all_data, all_metrics, str(tmp_path))
    pngs = list(tmp_path.glob("*.png"))
    assert len(pngs) > 0
