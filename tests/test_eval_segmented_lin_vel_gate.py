# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""`eval.py segmented` must REFUSE an env that cannot receive its cascade command.

The defect this pins (2026-09 cleanup, merge review). segmented's outer loop is a
cascade position controller: it computes `vel_cmd` from position error and writes it to
`raw_env._vel_cmd_lin`. That buffer existed only on the full-DOF family, which WP5
deleted -- the attitude-only main env explicitly has none (`_sample_velocity_command`:
"no linear velocity"). WP5 wrapped the three writes in `hasattr` guards, which turned a
loud AttributeError into silence: the mode ran to completion while

  * the command reached no env, so no position control was applied, yet
  * `vel_cmd_x/y/z` still recorded it and `write_eval_npz` published it, and
  * `pos_drift_*` measured FREE DRIFT under a "cascade PID" header.

A guard whose condition is always false is not a guard, it is a silent no-op. The fix
refuses at setup instead, so the failure is loud again and no npz can claim a command
that was never delivered.

Parsed with `ast` rather than imported: eval.py boots Isaac Sim at module scope
(`AppLauncher` at :370), so importing it here is impossible.
"""
from __future__ import annotations

import ast
from pathlib import Path

import pytest

EVAL_PY = Path(__file__).resolve().parents[1] / "constrained_albc" / "analysis" / "eval.py"
ATTR = "_vel_cmd_lin"


def _func(name: str) -> ast.FunctionDef:
    tree = ast.parse(EVAL_PY.read_text())
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == name:
            return node
    pytest.fail(f"{name}() not found in {EVAL_PY} -- the gate is measuring nothing")


def _hasattr_tests_on(node: ast.AST, attr: str) -> list[ast.Call]:
    """Every `hasattr(<anything>, "<attr>")` call inside `node`."""
    return [
        n
        for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Name)
        and n.func.id == "hasattr"
        and len(n.args) == 2
        and isinstance(n.args[1], ast.Constant)
        and n.args[1].value == attr
    ]


def test_run_segmented_refuses_an_env_without_the_lin_vel_command():
    """Setup must raise, not skip, when the env cannot receive the cascade command."""
    fn = _func("run_segmented")
    guards = _hasattr_tests_on(fn, ATTR)
    assert guards, (
        f"run_segmented() does not check for {ATTR} at all. Without it the cascade outer "
        "loop is a no-op on every attitude-only task and the npz still records vel_cmd_*."
    )
    raises = [n for n in ast.walk(fn) if isinstance(n, ast.Raise)]
    assert raises, (
        f"run_segmented() checks for {ATTR} but never raises. A capability the mode "
        "cannot do without must stop the run, not be skipped."
    )


def test_run_switching_eval_does_not_silently_skip_the_command():
    """The per-step writes must be unguarded: reaching them means the attribute exists.

    A `hasattr` here is the exact silent no-op the setup guard replaces -- it would let
    the loop keep recording vel_cmd_x/y/z for a command it never delivered.
    """
    fn = _func("run_switching_eval")
    guards = _hasattr_tests_on(fn, ATTR)
    assert not guards, (
        f"run_switching_eval() guards its {ATTR} writes with hasattr at "
        f"line(s) {[g.lineno for g in guards]}. On every registered task that condition "
        "is permanently false, so the cascade command is dropped while vel_cmd_x/y/z "
        "still lands in the npz. Refuse in run_segmented() setup instead."
    )
