# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Shared helper for the analyze subcommands (npz loading)."""

from __future__ import annotations

import numpy as np


def _load_npz(path: str) -> dict[str, np.ndarray]:
    """Load a .npz file and return as a plain dict."""
    return dict(np.load(path))
