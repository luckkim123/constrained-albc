# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Audit P4d: detect_oscillation must separate true oscillation from iid noise.

The prior gates (sign_change_rate > 0.3, fixed prominence 0.1) were inverted:
iid noise (sign-change-rate ~0.66, autocorr floor ~0.2) passed while smooth
sinusoids (rate ~0.1, autocorr peak ~0.78) were rejected. Verified: 30/30 noise
series flagged oscillating, 0/10 sinusoids. The fix uses a plausible-rate range
plus an autocorr peak-magnitude floor > 0.5.
"""
from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))

from tslib import detect_oscillation  # type: ignore[import-not-found]  # noqa: E402


def test_pure_noise_not_flagged_oscillating():
    rng = np.random.RandomState(0)
    fp = 0
    for _ in range(30):
        std = 10 ** rng.uniform(-4, -1)
        if detect_oscillation(rng.randn(100) * std)["oscillating"]:
            fp += 1
    assert fp == 0, f"{fp}/30 noise series falsely flagged oscillating"


def test_sinusoid_flagged_oscillating():
    rng = np.random.RandomState(1)
    tp = 0
    t = np.arange(120)
    for freq in (0.1, 0.15, 0.2, 0.25, 0.3):
        sig = np.sin(freq * t) + rng.randn(120) * 0.03
        if detect_oscillation(sig)["oscillating"]:
            tp += 1
    # at least 4/5 clean sinusoids detected (very short periods are borderline)
    assert tp >= 4, f"only {tp}/5 sinusoids detected"


def test_flat_signal_not_oscillating():
    flat = np.ones(100) * 0.5 + np.random.RandomState(2).randn(100) * 1e-6
    assert detect_oscillation(flat)["oscillating"] is False


def test_short_series_returns_none():
    assert detect_oscillation(np.arange(20)) is None
