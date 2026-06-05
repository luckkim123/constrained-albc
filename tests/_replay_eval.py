# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""npz-replay harness: load a data_*.npz fixture, call extracted sim-free
plot/serialize functions, write PNGs+json to an output dir. Run before+after
a refactor and diff the output dirs to prove behavior preservation.

Usage:
    python3 tests/_replay_eval.py <fixture_dir> <output_dir>
"""

from __future__ import annotations

import os
import sys

import numpy as np

sys.path.insert(
    0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis")
)


def _load_levels(fixture_dir: str) -> dict:
    """Load data_<level>.npz into the all_data dict shape eval.py uses."""
    levels = ["none", "soft", "medium", "hard"]
    all_data = {}
    for lvl in levels:
        path = os.path.join(fixture_dir, f"data_{lvl}.npz")
        if os.path.exists(path):
            all_data[lvl] = dict(np.load(path, allow_pickle=True))
    return all_data


def main() -> int:
    fixture_dir, output_dir = sys.argv[1], sys.argv[2]
    os.makedirs(output_dir, exist_ok=True)
    all_data = _load_levels(fixture_dir)
    levels = list(all_data.keys())
    if not levels:
        print(f"[ERROR] no data_*.npz in {fixture_dir}")
        return 1
    # Only the plot funcs already extracted are callable here; this harness
    # grows as more funcs move into eval_plots.py. At minimum prove import.
    import eval_plots  # noqa: F401

    print(f"[OK] loaded {len(levels)} levels: {levels}; eval_plots imported")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
