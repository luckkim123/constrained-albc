# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free guard: the eval latent instrument must DELEGATE, never re-run the encoder.

Regression guard for the E0 instrument bug. `_InstrumentedStudentPolicy` (eval.py static
student mode) used to REPLICATE `StudentInLoopPolicy.__call__`'s forward so it could capture
the intermediate latent without double-advancing the TCN ring / GRU hidden state. That copy
omitted the obs normalization on the TCN branch -- it fed the raw ring to the encoder while
training (`runner._compute_loss_tcn`), the deploy reference (`StudentInLoopPolicy`) and even
the copy's own GRU branch all normalized first. E-int's actor_obs_normalizer spans 72 dims
with 23 of std < 0.2, so the encoder saw inputs off by up to ~150x.

Consequence: every TCN in-loop measurement from `static` between 2026-05-26 (096f5b8) and
2026-07-29 -- including the "observability floor" latent env-variance ratio and the DAgger
hard-DR verdict -- was taken on out-of-distribution encoder inputs. `segmented` mode was
unaffected (it uses StudentInLoopPolicy directly).

The fix is structural rather than a patched-in normalize call: the policy publishes
`last_l_hat` and the instrument reads it, so exactly ONE encoder forward exists in the eval
path and cannot drift from training. These checks fail if a future refactor reintroduces a
second forward. Source-level (like test_student_eval_obs_width.py's second check) because
importing eval.py pulls the Isaac Sim app chain.
"""
from __future__ import annotations

import ast
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
EVAL_PY = REPO / "constrained_albc" / "analysis" / "eval.py"
STUDENT_POLICY_PY = REPO / "constrained_albc" / "analysis" / "student_policy.py"


def _class_node(path: Path, name: str) -> tuple[ast.ClassDef, str]:
    """Return (ClassDef node, its source text) without importing the module."""
    src = path.read_text()
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.ClassDef) and node.name == name:
            return node, ast.get_source_segment(src, node)
    raise AssertionError(f"class {name} not found in {path}")


def test_instrument_delegates_and_never_forwards_the_encoder():
    node, src = _class_node(EVAL_PY, "_InstrumentedStudentPolicy")

    # It reads the latent the policy published instead of computing its own.
    assert "last_l_hat" in src, "instrument must read the policy's published latent"

    # And it holds NO encoder call of its own. `<anything>.student(...)` is the encoder
    # forward; the whole bug was that this class had one that diverged from training.
    encoder_calls = [
        n for n in ast.walk(node)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute)
        and n.func.attr == "student"
    ]
    assert not encoder_calls, (
        "_InstrumentedStudentPolicy runs its own encoder forward again -- that duplicate is "
        "what silently dropped obs normalization on the TCN branch. Delegate to the wrapped "
        "policy and read `last_l_hat` instead."
    )


def test_student_policy_publishes_the_latent_it_used():
    _, src = _class_node(STUDENT_POLICY_PY, "StudentInLoopPolicy")
    # The single source of truth the instrument depends on. Must be the same l_hat that
    # was handed to the teacher actor, i.e. assigned after the normalized forward.
    assert "self.last_l_hat = l_hat" in src
    assert src.index("self.last_l_hat = l_hat") < src.index("actor_forward")
    # The normalization the duplicate used to skip, still present on the TCN branch.
    assert "self.obs_normalizer(self.ring.reshape(B * H, D))" in src
