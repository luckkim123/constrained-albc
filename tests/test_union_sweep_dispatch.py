# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Union-27D sweep-builder dispatch fingerprint (analysis/common.py).

The union p_t layout (2026-07-12) kept the dim count at 27, so
build_sweep_params_from_checkpoint cannot dispatch on input_dim alone. It
fingerprints on bounds content: idx22 lower > 0 (buoy volume scale bounds)
selects the union builder; pre-union 27D checkpoints (ocean-current y at
idx22, symmetric bounds) must keep their previous generic path.
"""

from __future__ import annotations

import importlib.util
import os
import sys

import numpy as np

_MODULE_PATH = os.path.join(
    os.path.dirname(__file__), "..", "constrained_albc", "analysis", "common.py"
)
_spec = importlib.util.spec_from_file_location("_analysis_common", _MODULE_PATH)
common = importlib.util.module_from_spec(_spec)
sys.modules["_analysis_common"] = common
_spec.loader.exec_module(common)

# Union-27D bounds (matches tests/test_priv_obs_bounds.py _EXPECTED).
_LO = np.array([0.00675, -0.02, -0.02, -0.09, -0.02, -0.02, -0.04, 0.4, 6.885, 4.0,
                0.0, -0.08, -0.08, -0.05, 30.0, 0.3, 28.0, 0.07, 995.0,
                -0.5, -0.5, -0.25, 0.00201, 0.6975, -1.0, -1.0, -1.0])
_HI = np.array([0.01125, 0.02, 0.02, -0.01, 0.02, 0.02, 0.04, 1.7, 11.475, 12.0,
                3.0, 0.08, 0.08, 0.0, 150.0, 7.0, 52.0, 0.13, 1025.0,
                0.5, 0.5, 0.25, 0.00335, 1.1625, 1.0, 1.0, 1.0])


def test_union_bounds_route_to_union_builder():
    params = common.build_sweep_params_from_checkpoint(27, np.zeros(27), _LO, _HI)
    names = [p.name for p in params]
    assert len(params) == 27
    assert names[7] == "Quad Damp Roll"  # Ixx/lin_damp removed
    assert names[22] == "Buoy Volume"
    assert names[23] == "Buoy Body Mass"
    assert names[24:27] == ["Lin Vel U", "Lin Vel V", "Lin Vel W"]


def test_pre_union_bounds_keep_generic_path():
    lo_old = _LO.copy()
    lo_old[22] = -0.5  # pre-union layout: ocean-current y at idx22 (symmetric)
    params = common.build_sweep_params_from_checkpoint(27, np.zeros(27), lo_old, _HI)
    assert params[22].name != "Buoy Volume"  # falls through exactly as before
