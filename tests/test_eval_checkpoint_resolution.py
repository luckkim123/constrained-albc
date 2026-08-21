# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Every eval mode must resolve the teacher checkpoint through one helper.

run_static, run_periodic and run_segmented each carried their own copy of the
checkpoint-resolution block, and run_segmented's copy lacked the best_model.pt
preference (096f5b8 added it to two of the three). `eval.py static` and
`eval.py segmented` could therefore score different weights from identical
arguments. This is a source-level check because the defect class is divergence
between copies, not a runtime bug -- and because importing eval.py needs Isaac Sim.
"""

import ast
from pathlib import Path

EVAL_PY = Path(__file__).resolve().parents[1] / "constrained_albc" / "analysis" / "eval.py"
HELPER = "_resolve_teacher_checkpoint"


def _run_mode_functions(tree):
    return [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name.startswith("run_")]


def _called_names(node):
    return {
        c.func.id if isinstance(c.func, ast.Name) else c.func.attr
        for c in ast.walk(node)
        if isinstance(c, ast.Call) and isinstance(c.func, (ast.Name, ast.Attribute))
    }


def test_no_run_mode_resolves_the_checkpoint_itself():
    tree = ast.parse(EVAL_PY.read_text())
    modes = _run_mode_functions(tree)
    assert modes, "no run_* eval modes found -- the file was restructured"
    offenders = [f.name for f in modes if "get_checkpoint_path" in _called_names(f)]
    assert not offenders, (
        f"{offenders} call get_checkpoint_path directly; route them through {HELPER}() "
        "so every mode applies the same best_model.pt preference"
    )


def test_best_model_preference_lives_in_exactly_one_place():
    # A second occurrence means a mode grew its own copy again -- the shape of the
    # original defect, where one copy silently lacked the preference.
    assert EVAL_PY.read_text().count('"best_model.pt"') == 1


if __name__ == "__main__":
    test_no_run_mode_resolves_the_checkpoint_itself()
    test_best_model_preference_lives_in_exactly_one_place()
    print("ok")
