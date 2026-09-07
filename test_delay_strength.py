"""PLAN item 12: `control_delay_strength` paces `control_delay_steps`.

finding/264: `control_delay_steps` was never in DORAEMON's `_PARAM_DEFS`, so nothing paced
it. finding/315: a flat (0, 3) from iteration 0 stalled a run under a mistuned
`performance_lb`. The fix moves the CEILING with a curriculum knob, and this checks the
three properties that matter:

  * s = 0 pins every env at `lo` -- the incumbent's zero-delay plant, so a run starts where
    the deployed teacher was actually trained (finding/264);
  * s = 1 covers EXACTLY {lo..hi} -- no value missing, none out of range, so the fully-open
    curriculum is the full band and nothing more;
  * an intermediate s never exceeds its own rounded ceiling.

ROUNDING RULE: `torch.round`, which is half-to-EVEN. s=0.5 on (0, 13) -> ceiling
round(6.5) = 6, not 7; s=0.5 on (0, 5) -> round(2.5) = 2, not 3. Both are asserted below so
a change of rounding rule breaks the test rather than silently shifting the plant.

Loads events.py by path -- it imports only torch (its marinelab/isaaclab names are under
`TYPE_CHECKING`), so no Isaac import chain is needed. Pure torch, runs on CPU.

Run:  python3 -m pytest test_delay_strength.py -q
"""
import importlib.util
from pathlib import Path

import torch

_PATH = Path(__file__).resolve().parent / "constrained_albc" / "envs" / "main" / "mdp" / "events.py"
_spec = importlib.util.spec_from_file_location("events_under_test", _PATH)
events = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(events)
sample = events.sample_control_delay_steps

N = 20_000
DEV = "cpu"
LAUNCH = (0, 13)          # finding/148: 152 ms median cmd->joint latency at 50 Hz


def _const(s, n=N):
    return torch.full((n,), float(s), device=DEV)


def test_zero_strength_pins_every_env_at_lo():
    for rng in [LAUNCH, (0, 5), (2, 9)]:
        lag = sample(rng, _const(0.0), DEV)
        assert torch.equal(lag, torch.full((N,), rng[0], dtype=torch.int)), rng


def test_full_strength_covers_exactly_the_whole_range():
    for rng in [LAUNCH, (0, 5), (2, 9)]:
        lo, hi = rng
        lag = sample(rng, _const(1.0), DEV)
        assert lag.min().item() == lo and lag.max().item() == hi, rng
        assert set(lag.unique().tolist()) == set(range(lo, hi + 1)), rng


def test_half_strength_respects_the_rounded_ceiling():
    # torch.round is half-to-even: round(6.5) = 6 and round(2.5) = 2.
    for rng, ceiling in [(LAUNCH, 6), ((0, 5), 2)]:
        lag = sample(rng, _const(0.5), DEV)
        assert lag.max().item() <= ceiling, (rng, lag.max().item())
        assert lag.max().item() == ceiling, (rng, lag.max().item())  # ceiling is reachable
        assert lag.min().item() == rng[0]


def test_rounding_is_half_to_even_not_half_up():
    """Guards the rule itself: half-up would give 7 on (0,13) and 3 on (0,5)."""
    assert torch.round(torch.tensor(6.5)).item() == 6.0
    assert torch.round(torch.tensor(2.5)).item() == 2.0
    assert sample(LAUNCH, _const(0.5), DEV).max().item() != 7
    assert sample((0, 5), _const(0.5), DEV).max().item() != 3


def test_ceiling_is_monotone_in_strength():
    prev = -1
    for s in [0.0, 0.1, 0.25, 0.5, 0.75, 0.9, 1.0]:
        top = sample(LAUNCH, _const(s), DEV).max().item()
        assert top >= prev, (s, top, prev)
        prev = top
    assert prev == LAUNCH[1]


def test_per_env_strength_is_honoured_independently():
    """A mixed batch: each env's ceiling follows ITS OWN strength, not the batch mean."""
    n_each = 5000
    strength = torch.cat([_const(0.0, n_each), _const(1.0, n_each)])
    lag = sample(LAUNCH, strength, DEV)
    assert torch.equal(lag[:n_each], torch.zeros(n_each, dtype=torch.int))
    assert lag[n_each:].max().item() == LAUNCH[1]


def test_lag_never_exceeds_the_buffer_history_length():
    """The DelayBuffer is allocated with history_length = hi, so hi is a hard bound even if
    a config override hands in a strength above 1."""
    lag = sample(LAUNCH, _const(3.0), DEV)
    assert lag.max().item() <= LAUNCH[1]
    assert lag.min().item() >= LAUNCH[0]


def test_dtype_matches_the_lag_buffer():
    assert sample(LAUNCH, _const(0.5), DEV).dtype == torch.int


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}", flush=True)
