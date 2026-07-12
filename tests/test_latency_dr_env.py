"""Control-action delay: off = byte-identical; on = per-env N-step lag.

Skipped if importing isaaclab.utils.buffers boots Isaac Sim (structural-only test) --
in this container `isaaclab.utils.__init__` transitively imports `pxr` via `mesh.py`,
which is unavailable, so this test skips here (sibling convention, see
test_delay_buffer_behavior.py / test_latency_dr_config.py).

Sibling tests leak import state across the pytest session in two ways this test
must undo before its own gate is trustworthy:
  1. test_config_equivalence.py / test_constraints.py register non-package
     `sys.modules[...]` stubs (no __path__) for "isaaclab", "isaaclab.utils", and
     "constrained_albc.envs.main" to load individual submodules without Isaac Sim.
  2. test_delay_buffer_behavior.py's own `importorskip("isaaclab.utils.buffers")`
     partially executes `isaaclab/utils/__init__.py` -- `from .buffers import *`
     (line 9) succeeds and registers the real `isaaclab.utils.buffers` submodule in
     sys.modules *before* `from .mesh import *` (line 14) fails on the missing pxr
     dependency. That real submodule then lingers in sys.modules even though the
     parent `isaaclab.utils` package never finished initializing, so a later
     `importorskip("isaaclab.utils.buffers")` finds it already cached and returns
     without re-raising -- masking the real reason this test can't run here.
Purge stale entries for both before importing so this test resolves the real
on-disk packages (and skips for the real reason -- pxr missing -- rather than
erroring on a shadowed/partial stub) regardless of collection order.
"""

import sys

import pytest

# isaaclab.utils.buffers is purged unconditionally: even when it has a real
# __path__ it may be an orphaned submodule left behind by a sibling test's failed
# `from .mesh import *` (see docstring point 2) -- only a fresh import of the
# parent chain proves whether pxr is actually available.
sys.modules.pop("isaaclab.utils.buffers", None)

for _name in (
    "isaaclab.utils",
    "isaaclab",
    "constrained_albc.envs.main",
    "constrained_albc.envs",
    "constrained_albc",
):
    _mod = sys.modules.get(_name)
    if _mod is not None and not hasattr(_mod, "__path__"):
        del sys.modules[_name]

pytest.importorskip("isaaclab.utils.buffers")

import torch

from constrained_albc.envs.main.albc_env import (
    _apply_control_delay,  # helper added in Step 3
    _draw_control_delay,  # helper added in Step 3
)


def test_off_is_byte_identical():
    """control_delay_steps=(0,0): applied action equals the input exactly."""
    num_envs = 4
    lag, buf = _draw_control_delay((0, 0), num_envs, device="cpu")
    assert torch.equal(lag, torch.zeros(num_envs, dtype=torch.int))
    for step in range(6):
        a = torch.randn(num_envs, 8)
        out = _apply_control_delay(buf, a)
        assert torch.equal(out, a)  # off = pass-through


def test_on_delays_by_drawn_lag():
    """control_delay_steps=(3,3): every env delayed by exactly 3 steps."""
    num_envs = 2
    lag, buf = _draw_control_delay((3, 3), num_envs, device="cpu")
    assert torch.equal(lag, torch.full((num_envs,), 3, dtype=torch.int))
    seq = [torch.full((num_envs, 8), float(v)) for v in range(6)]
    outs = [_apply_control_delay(buf, a) for a in seq]
    # step0..2 warmup-clamp to oldest (0.0), step3.. delayed by 3.
    assert [o[0, 0].item() for o in outs] == [0.0, 0.0, 0.0, 0.0, 1.0, 2.0]


def test_drawn_lag_in_range():
    """control_delay_steps=(0,3): drawn per-env lag in {0,1,2,3}."""
    lag, _ = _draw_control_delay((0, 3), 256, device="cpu")
    assert lag.min().item() >= 0 and lag.max().item() <= 3
    assert lag.dtype == torch.int
