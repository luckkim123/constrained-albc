# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""StudentCfg.log_dir_root must stay inside the repo.

`config.py` anchors it with a fixed number of `..` hops from `__file__`. That count is a
function of how deep the module sits, so ANY move of the file silently redirects every
student run's output -- no import breaks, no test fails, the run just writes somewhere
else. That is exactly what the 2026-09 WP4 promotion did: the module went from
`constrained_albc/envs/_core/student/` (4 hops to the repo root) to
`constrained_albc/algorithms/student/` (3 hops) while keeping 4, so a smoke run landed in
the workspace directory ABOVE the repo.

Loaded by file path: importing the package would pull in Isaac Sim.
"""

from __future__ import annotations

import importlib.util
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parents[1]
CFG = REPO / "constrained_albc" / "algorithms" / "student" / "config.py"


def _load_student_cfg():
    spec = importlib.util.spec_from_file_location("student_config_logroot", CFG)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_repo_root_is_the_repo():
    """The `..` hop count must resolve to the repo root, not above or below it."""
    m = _load_student_cfg()
    assert pathlib.Path(m._REPO_ROOT) == REPO, (
        f"_REPO_ROOT resolves to {m._REPO_ROOT!r}, expected the repo root {str(REPO)!r} -- "
        "the `..` hop count in config.py no longer matches the module's depth"
    )


def test_log_dir_root_is_inside_the_repo():
    """Student output must land in <repo>/logs/rsl_rl/<experiment>, like the teacher's."""
    m = _load_student_cfg()
    root = pathlib.Path(m.StudentCfg().log_dir_root).resolve()
    assert root.is_relative_to(REPO), f"log_dir_root escapes the repo: {root}"
    assert root.parts[-3:-1] == ("logs", "rsl_rl"), f"unexpected layout: {root}"
