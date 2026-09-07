# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""WP11 gate: the GRU student's training forward must reset its hidden AT each done.

The defect this pins (2026-09 cleanup, plan section 3 WP11). Collection resets the GRU
hidden at the exact done step and the buffer records `prev_dones` per timestep, but
training used to collapse a rollout's dones into `any()` and zero the WHOLE window's
start hidden for any env that reset anywhere in it. For an env that reset at step k:

  * steps before k lost the true hidden carried from the previous rollout, and
  * steps at/after k inherited the hidden propagated through the PREVIOUS episode
    rather than a fresh zero,

while the runner comment claimed the snapshot gave "the correct initial state". Both
reviewers (codex, session) called it a definite bug against its own stated intent, and
early terminations make the affected fraction larger than the timeout-only 1.6%.

What is asserted here, against the SHIPPED `StudentRunner._gru_seq_forward` bound to a
real `StudentEncoderGRU` (no Isaac Sim, no env):

  1. an env with a done at step k: the post-done tail equals a forward started from a
     ZERO hidden at k, and the pre-done prefix equals the fused forward from the carried
     hidden -- neither of which the old `any()` collapse could produce;
  2. an env with NO done is byte-identical to the plain fused `self.student(...)` call,
     so the fix cannot move a run that had no mid-rollout reset;
  3. the returned final hidden matches the same segmentation;
  4. gradients flow to the encoder through the stitched output (the implementation
     reassembles clean and dirty envs with `index_copy`, which must stay differentiable).

Loads student/{config,models,runner}.py the way the sibling student tests do -- by file
path under stub parent packages -- because importing `constrained_albc` registers the gym
tasks and cascades into `isaaclab.sim -> pxr`, absent here.
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
import torch

REPO = Path(__file__).resolve().parents[1]
STUDENT_DIR = REPO / "constrained_albc" / "algorithms" / "student"


def _load_student(*module_names: str):
    for pkg in (
        "constrained_albc",
        "constrained_albc.algorithms",
        "constrained_albc.algorithms.student",
    ):
        if pkg not in sys.modules:
            sys.modules[pkg] = types.ModuleType(pkg)
            sys.modules[pkg].__path__ = []
    # The leaf gets a REAL __path__ so runner.py's own `from .collector import ...` and
    # `from .teacher import ...` resolve without importing constrained_albc. Set
    # unconditionally: a sibling test module may have installed the same stub first with an
    # empty __path__, and under a full-suite run that stub is what this would inherit.
    sys.modules["constrained_albc.algorithms.student"].__path__ = [str(STUDENT_DIR)]

    def _exec(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.algorithms.student"
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    return tuple(
        _exec(f"constrained_albc.algorithms.student.{n}", STUDENT_DIR / f"{n}.py")
        for n in module_names
    )


class _Bound:
    """Minimal carrier for the shipped `_gru_seq_forward`: it touches only `self.student`."""

    def __init__(self, student, fn):
        self.student = student
        self._fn = fn

    def __call__(self, x_seq, h_in, dones_seq):
        return self._fn(self, x_seq, h_in, dones_seq)


_MISSING = object()

D, H, T, LAT = 6, 8, 7, 3


@pytest.fixture(scope="module")
def seq_forward():
    """The REAL runner method, bound to a REAL GRU encoder.

    `runner.py` guards `import wandb` with `except ImportError`, which is correct for
    production. It is not enough HERE: sibling test modules install `_MockModule` stubs for
    omni/pxr/carb into the shared `sys.modules`, and wandb's pydantic models then fail with
    `TypeError: expected str, bytes or os.PathLike object, not _MockModule` -- so the file
    imports standalone and errored under a full-suite run. wandb is stubbed for the load and
    the previous entry restored, rather than widening the production guard to `except
    Exception`, which would also swallow a genuine wandb breakage on a real training host.
    """
    cfg_mod, models_mod = _load_student("config", "models")
    _prev_wandb = sys.modules.get("wandb", _MISSING)
    sys.modules["wandb"] = types.ModuleType("wandb")
    try:
        (runner_mod,) = _load_student("runner")
    finally:
        if _prev_wandb is _MISSING:
            del sys.modules["wandb"]
        else:
            sys.modules["wandb"] = _prev_wandb
    cfg = cfg_mod.StudentCfg(
        encoder_type="gru", gru_hidden=H, gru_layers=1, latent_dim=LAT, policy_obs_dim=D
    )
    torch.manual_seed(0)
    student = models_mod.StudentEncoderGRU(cfg).double()
    return _Bound(student, runner_mod.StudentRunner._gru_seq_forward)


def _inputs(num_envs, seed=1):
    g = torch.Generator().manual_seed(seed)
    x = torch.randn(num_envs, T, D, generator=g, dtype=torch.float64)
    h = torch.randn(1, num_envs, H, generator=g, dtype=torch.float64)
    return x, h


def test_no_done_is_byte_identical_to_the_fused_forward(seq_forward):
    """An env that never reset must be unchanged by this fix -- bitwise."""
    x, h = _inputs(4)
    dones = torch.zeros(4, T, dtype=torch.bool)
    got, h_got = seq_forward(x, h, dones)
    want, h_want = seq_forward.student(x, hidden=h)
    assert torch.equal(got, want)
    assert torch.equal(h_got, h_want)


def test_hidden_resets_at_the_done_step(seq_forward):
    """Env 0 resets at k: tail == zero-hidden restart, prefix == carried-hidden forward."""
    k = 3
    x, h = _inputs(3, seed=2)
    dones = torch.zeros(3, T, dtype=torch.bool)
    dones[0, k] = True
    got, h_got = seq_forward(x, h, dones)

    # prefix: env 0, steps [0, k) driven by the CARRIED hidden
    pre, _ = seq_forward.student(x[:1, :k], hidden=h[:, :1].contiguous())
    assert torch.allclose(got[0, :k], pre[0], atol=1e-12)

    # tail: env 0, steps [k, T) restarted from ZERO
    tail, h_tail = seq_forward.student(x[:1, k:], hidden=torch.zeros_like(h[:, :1]))
    assert torch.allclose(got[0, k:], tail[0], atol=1e-12)
    assert torch.allclose(h_got[:, 0], h_tail[:, 0], atol=1e-12)

    # the collapse the fix removes: zeroing the WHOLE window would give this instead
    collapsed, _ = seq_forward.student(x[:1], hidden=torch.zeros_like(h[:, :1]))
    assert not torch.allclose(got[0, :k], collapsed[0, :k], atol=1e-6), (
        "prefix still matches the old any()-collapse -- the fix is not in effect"
    )

    # sibling envs with no done keep the fused result
    want, _ = seq_forward.student(x[1:], hidden=h[:, 1:].contiguous())
    assert torch.equal(got[1:], want)


def test_done_at_step_zero_zeroes_the_start_hidden(seq_forward):
    """`done_flat[0]` is the carried prev_dones: a True there means start from zero."""
    x, h = _inputs(2, seed=3)
    dones = torch.zeros(2, T, dtype=torch.bool)
    dones[1, 0] = True
    got, _ = seq_forward(x, h, dones)
    want, _ = seq_forward.student(x[1:], hidden=torch.zeros_like(h[:, 1:]))
    assert torch.allclose(got[1], want[0], atol=1e-12)


def test_gradients_flow_through_the_stitched_output(seq_forward):
    """index_copy reassembly must stay differentiable for BOTH halves."""
    x, h = _inputs(4, seed=4)
    dones = torch.zeros(4, T, dtype=torch.bool)
    dones[2, 2] = True  # one dirty env, three clean
    seq_forward.student.zero_grad(set_to_none=True)
    out, _ = seq_forward(x, h, dones)
    out.sum().backward()
    grads = [p.grad for p in seq_forward.student.parameters() if p.grad is not None]
    assert grads, "no parameter received a gradient"
    assert all(torch.isfinite(g).all() for g in grads)
    assert any(g.abs().sum() > 0 for g in grads)
