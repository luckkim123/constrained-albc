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
from _analyze.recompute_metrics import _per_env_ss_stats  # noqa: E402


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
