"""Characterize isaaclab DelayBuffer for the latency-DR wiring contract.

Skipped if importing isaaclab.utils.buffers boots Isaac Sim (structural-only test) --
in this container `isaaclab.utils.__init__` transitively imports `pxr` via `mesh.py`,
which is unavailable, so this test skips here (sibling convention, see
test_latency_dr_config.py). Verified offline (outside pytest, bypassing the
isaaclab.utils package __init__ via a manual sys.modules stub for the `buffers`
submodule only) against the real DelayBuffer on an environment where pxr is absent
but the buffers submodule's own dependencies (torch only) resolve: the warmup-clamp
values below are the OBSERVED behavior, not merely predicted.
"""
import pytest

DelayBuffer = pytest.importorskip("isaaclab.utils.buffers").DelayBuffer

import torch


def test_zero_lag_is_passthrough():
    """lag=0 returns the just-appended sample, value-identical, every step."""
    buf = DelayBuffer(history_length=3, batch_size=2, device="cpu")
    buf.set_time_lag(0)
    for step in range(5):
        x = torch.full((2, 4), float(step))
        out = buf.compute(x)
        assert torch.equal(out, x)


def test_n_step_lag_delays_by_n():
    """lag=2: output at step t equals input at step t-2 (warmup clamps to oldest)."""
    buf = DelayBuffer(history_length=3, batch_size=1, device="cpu")
    buf.set_time_lag(2)
    seq = [torch.full((1, 1), float(v)) for v in (10, 11, 12, 13, 14)]
    outs = [buf.compute(x).item() for x in seq]
    # warmup: step0 and step1 clamp to the oldest available sample (10),
    # then step2 onward is delayed by exactly 2.
    assert outs == [10.0, 10.0, 10.0, 11.0, 12.0]


def test_per_env_lag_is_independent():
    """Different envs can carry different integer lags simultaneously."""
    buf = DelayBuffer(history_length=3, batch_size=2, device="cpu")
    buf.set_time_lag(torch.tensor([0, 2], dtype=torch.int))
    seq = [torch.tensor([[float(v)], [float(v)]]) for v in (20, 21, 22, 23)]
    outs = [buf.compute(x) for x in seq]
    # env0 lag0 = live; env1 lag2 = delayed by 2 (warmup-clamped early).
    assert [o[0].item() for o in outs] == [20.0, 21.0, 22.0, 23.0]
    assert [o[1].item() for o in outs] == [20.0, 20.0, 20.0, 21.0]
