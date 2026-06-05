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
