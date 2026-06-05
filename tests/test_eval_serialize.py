# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Unit tests for sim-free serialization helpers extracted from eval.py."""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)
from eval_serialize import _build_mat_meta, write_eval_npz  # noqa: E402


def test_build_mat_meta_returns_dict_with_level_and_scale():
    meta = _build_mat_meta(
        {"roll": np.zeros((10, 4))},
        level="hard",
        dr_scale=1.0,
        checkpoint="/tmp/model.pt",
        task="Isaac-ConstrainedALBC-TRPO-v0",
        num_envs=4,
        mode="static",
    )
    assert isinstance(meta, dict)
    assert meta["dr_level"] == "hard"
    assert meta["dr_scale"] == 1.0


def test_write_eval_npz_roundtrips(tmp_path):
    data = {"roll": np.arange(40).reshape(10, 4).astype(float)}
    write_eval_npz(str(tmp_path), "none", data)
    loaded = np.load(str(tmp_path / "data_none.npz"))
    np.testing.assert_array_equal(loaded["roll"], data["roll"])
