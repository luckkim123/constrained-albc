# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free verification of audit P2 plot fixes (yaw deg/s, OOD 5-level, lin_vel yerr).

Lives in repo-root tests/ (NOT analysis/) so it imports on plain python3 without
booting Isaac Sim -- the analysis/ package pulls carb transitively. Mirrors the
dr_snapshot / failure_dr test pattern.
"""
from __future__ import annotations

import os
import sys

import numpy as np

# analysis/ uses sibling-relative imports (from common import ...); add it to the path.
_ANALYSIS = os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
sys.path.insert(0, os.path.abspath(_ANALYSIS))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.axes  # noqa: E402

import common  # type: ignore[import-not-found]  # noqa: E402
import eval_plots  # type: ignore[import-not-found]  # noqa: E402


# --- OOD 5-level: render order + KeyError-safe scale/color (USER-2) ---

def test_dr_render_order_includes_ood_last():
    assert common.DR_RENDER_ORDER == ["none", "soft", "medium", "hard", "ood"]


def test_ood_scale_and_color_present():
    # plots index DR_SCALE[lvl] / DR_COLORS[lvl] directly -- must not KeyError on ood
    assert "ood" in common.DR_SCALE
    assert "ood" in common.DR_COLORS
    assert common.DR_COLORS["ood"] != common.DR_COLORS["hard"]  # visually distinct


def test_levels_derivation_includes_ood_when_present():
    # generate_plots derives: [lvl for lvl in DR_RENDER_ORDER if lvl in all_data]
    all_data = {"none": {}, "soft": {}, "medium": {}, "hard": {}, "ood": {}}
    levels = [lvl for lvl in common.DR_RENDER_ORDER if lvl in all_data]
    assert levels == ["none", "soft", "medium", "hard", "ood"]


def test_levels_derivation_four_level_eval_unchanged():
    # regression guard: a 4-level eval (no ood) still draws exactly 4, ood-last order
    all_data = {"none": {}, "soft": {}, "medium": {}, "hard": {}}
    levels = [lvl for lvl in common.DR_RENDER_ORDER if lvl in all_data]
    assert levels == ["none", "soft", "medium", "hard"]
    assert "ood" not in levels


def test_in_dist_dr_levels_unchanged():
    # DR_LEVELS (the in-distribution set) must NOT have grown an ood entry
    assert common.DR_LEVELS == ["none", "soft", "medium", "hard"]


# --- yaw deg/s display conversion (USER-1) ---

def test_rad2deg_constant():
    assert eval_plots._RAD2DEG == 180.0 / np.pi
    # 1 rad/s -> ~57.2958 deg/s
    assert abs(1.0 * eval_plots._RAD2DEG - 57.29577951) < 1e-6


# --- lin_vel summary yerr (false-precision fix, MEDIUM) ---

def _fake_lin_vel_metrics(levels):
    """Minimal all_metrics for _plot_summary_lin_vel: per-axis per-env lists + scalars."""
    rng = np.random.RandomState(0)
    axes = ["vx", "vy", "vz"]
    out = {}
    for lvl in levels:
        per_axis_keys = {
            k: {a: list(rng.rand(8) * 0.1) for a in axes}
            for k in (
                "lin_vel_ss_errors", "lin_vel_ss_jitters", "lin_vel_rise_times",
                "lin_vel_overshoot_pcts", "lin_vel_zero_crossings",
            )
        }
        out[lvl] = {**per_axis_keys, "lin_vel_survival": 95.0}
    return out


def test_summary_lin_vel_renders_with_ood_level(tmp_path):
    # exercises the full _plot_summary_lin_vel with an ood level present:
    # proves DR_SCALE[ood]/DR_COLORS[ood] don't KeyError AND yerr path runs.
    levels = ["none", "soft", "medium", "hard", "ood"]
    all_metrics = _fake_lin_vel_metrics(levels)
    eval_plots._plot_summary_lin_vel(all_metrics, levels, str(tmp_path))
    assert (tmp_path / "summary_linvel.png").exists()


def test_summary_lin_vel_yerr_uses_per_env_std(tmp_path):
    # the bars must carry non-zero error bars when per-env spread exists.
    # capture by mocking ax.bar to record yerr.
    levels = ["none", "hard"]
    all_metrics = _fake_lin_vel_metrics(levels)
    captured = []
    real_bar = matplotlib.axes.Axes.bar

    def spy_bar(self, *args, **kwargs):
        if "yerr" in kwargs and kwargs["yerr"] is not None:
            captured.append(kwargs["yerr"])
        return real_bar(self, *args, **kwargs)

    matplotlib.axes.Axes.bar = spy_bar
    try:
        eval_plots._plot_summary_lin_vel(all_metrics, levels, str(tmp_path))
    finally:
        matplotlib.axes.Axes.bar = real_bar
    # 5 grouped-bar panels x 3 axes = 15 yerr-carrying bar calls (survival uses _bar_subplot)
    assert len(captured) >= 15
    # at least one error bar is non-zero (random per-env spread)
    assert any(np.nanmax(np.asarray(e)) > 0 for e in captured)
