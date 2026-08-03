# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Train/eval acceptance gate for the student encoder input layout (task A8).

38d979e class incident: an eval-side copy of the training forward silently dropped
observation normalization, and every in-loop verdict for two months measured
out-of-distribution encoder inputs. Nothing caught it. The fix (A5) made
`student_input` in `constrained_albc/envs/_core/student/models.py` the ONE place every
encoder forward builds its input -- DAgger collection, training loss, end-of-rollout
hidden recompute, and eval in-loop inference all call it instead of inlining the concat.

This file is the gate that keeps it that way:
(1) an AST check over the real source files asserting every function that calls the
    encoder (`self.student(...)`) either routes through `student_input` or is on the
    TCN allowance (TCN never carries extra channels by design, A3), and
(2) behavioral checks that the REAL `student_input` + REAL GRU encoder actually agree
    between a stepwise (carried-hidden) forward and a whole-sequence forward, and that
    the layout is obs-then-scaled-extra.

Review note: the 2026-07-30 draft of this test compared two byte-identical inlined
loops written inside the test file -- a tautology that would pass no matter what the
real code did. This version asserts on the shipped source and the shipped encoder.

Loads student/{config,models}.py standalone (mirrors tests/test_student_eval_obs_width.py
and tests/test_dagger_schedule.py) to avoid constrained_albc/__init__ -> isaaclab.sim ->
pxr, which is absent in this environment.
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path

import torch

REPO = Path(__file__).resolve().parents[1]
STUDENT_DIR = REPO / "constrained_albc" / "envs" / "_core" / "student"


def _load_student(*module_names: str):
    """Load student modules standalone, by file path, without importing constrained_albc.

    Registers empty parent packages then execs each requested module from
    `_core/student/<name>.py` with `__package__` set so `from .config import ...`
    resolves. Copied per repo convention (see test_student_eval_obs_width.py:38-66,
    test_dagger_schedule.py) rather than shared via conftest.
    """
    for pkg in (
        "constrained_albc",
        "constrained_albc.envs",
        "constrained_albc.envs._core",
        "constrained_albc.envs._core.student",
    ):
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = []  # mark as a package so submodule specs resolve
            sys.modules[pkg] = m

    def _exec(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.envs._core.student"
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    return tuple(
        _exec(f"constrained_albc.envs._core.student.{name}", STUDENT_DIR / f"{name}.py")
        for name in module_names
    )


# Per file: (functions that MUST route through student_input,
#            functions that call the encoder but legitimately must NOT).
# The second set is the TCN path. `_compute_loss_tcn` forwards the encoder and takes no
# extra channels by design (A3 rejects extra_obs_dim > 0 for non-GRU encoders), so it is
# an ALLOWED unrouted forward -- not a violation. `_dagger_action` holds BOTH branches,
# so it belongs in the routed set: its GRU branch must go through student_input.
# CORRECTED 2026-08-03: the first draft of this test omitted the TCN allowance and would
# have failed on correct code -- a gate that cries wolf gets deleted, which is worse than
# no gate. Verified against the code: runner.py has exactly 5 `self.student(` calls.
_SITES = {
    REPO / "constrained_albc" / "envs" / "_core" / "student" / "runner.py": (
        {"_dagger_action", "_compute_loss_gru", "learn"},   # sites (a) (b) (c)
        {"_compute_loss_tcn"},                              # TCN path, no extra by design
    ),
    REPO / "constrained_albc" / "analysis" / "student_policy.py": (
        {"__call__"},                                       # site (d)
        set(),
    ),
}


def _fns_calling_the_encoder(tree):
    """Function names containing a `self.student(...)` / `self.student(...)`-style call."""
    out = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if (isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "student"):
                out.add(fn.name)
    return out


def _fns_calling_student_input(tree):
    out = set()
    for fn in [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef)]:
        for node in ast.walk(fn):
            if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "student_input":
                out.add(fn.name)
    return out


def test_every_encoder_forward_uses_the_shared_layout():
    for path, (must_route, allowed_unrouted) in _SITES.items():
        tree = ast.parse(path.read_text())
        forwards = _fns_calling_the_encoder(tree)
        routed = _fns_calling_student_input(tree)
        # (1) Catches a NEW forward added without anyone noticing -- the failure that
        #     would have let runner.py's end-of-rollout hidden recompute (site c) ship
        #     unwidened. A new function calling the encoder fails here until it is
        #     deliberately classified as routed or TCN-only.
        assert forwards == must_route | allowed_unrouted, (
            f"{path.name}: encoder forwards are {sorted(forwards)}, expected "
            f"{sorted(must_route | allowed_unrouted)}. A forward was added, removed, or "
            "renamed -- route it through student_input and update _SITES deliberately."
        )
        # (2) Every forward that is not on the TCN allowance must use the shared layout.
        assert must_route <= routed, (
            f"{path.name}: {sorted(must_route - routed)} call the encoder without student_input"
        )


def test_stepwise_and_sequence_forwards_agree():
    torch.manual_seed(0)
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 6      # tiny for speed; the layout logic is width-agnostic
    cfg.extra_obs_dim = 4
    cfg.gru_hidden = 8
    cfg.gru_head_hidden = 4
    enc = models_mod.make_student_encoder(cfg)
    si = models_mod.student_input
    scale = torch.tensor(cfg.extra_obs_scale[: cfg.extra_obs_dim])
    T, B = 7, 3
    obs = torch.randn(B, T, cfg.policy_obs_dim)
    extra = torch.randn(B, T, cfg.extra_obs_dim)

    # stepwise + carried hidden == sites (a) and (d)
    h = enc.init_hidden(B, torch.device("cpu"))
    for t in range(T):
        l_step_seq, h = enc(si(obs[:, t], extra[:, t], scale).unsqueeze(1), hidden=h)

    # whole-sequence == sites (b) and (c)
    l_seq, _ = enc(si(obs, extra, scale), hidden=enc.init_hidden(B, torch.device("cpu")))

    assert torch.allclose(l_seq[:, -1], l_step_seq[:, -1], atol=1e-6), \
        "sequence forward and stepwise forward disagree -- hidden carry is broken"
    # extra_obs_dim == 0 must be byte-identical to no-extra (the OFF path every other arm uses)
    assert torch.equal(si(obs, extra, None), obs)


def test_layout_is_obs_then_scaled_extra():
    _, models_mod = _load_student("config", "models")
    obs = torch.zeros(2, 3)
    extra = torch.tensor([[10.0, 20.0], [30.0, 40.0]])
    scale = torch.tensor([10.0, 2.0])
    out = models_mod.student_input(obs, extra, scale)
    assert out.shape == (2, 5)
    assert torch.equal(out[:, :3], obs)                       # obs first, unscaled
    assert torch.allclose(out[:, 3:], torch.tensor([[1.0, 10.0], [3.0, 20.0]]))
