"""PLAN §4 item 10: `thruster_always_dead` exposure.

Two claims, and the second is the one that actually costs something if it is wrong:

1. Columns named in ``thruster_always_dead`` are EXACTLY 0.0 in every env, on both
   sampler paths (``thruster_fixed_health`` set, and the Bernoulli path), regardless
   of severity and regardless of ``fault.enable`` (the sampler never reads `enable`).
2. NOTHING ELSE MOVES. Run against the same generator state with ``()`` and the
   non-dead columns must be bit-identical -- the dead atom must not consume an extra
   RNG draw or reorder the stream, which is the discipline `thruster_dead_frac`
   already holds itself to.

Loads faults.py by path (as tests/test_fault_sampler_exposure.py does) so no Isaac
import chain is needed. Pure torch, runs on CPU.

Run:  python3 -m pytest test_always_dead_exposure.py -q
"""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import torch

_FAULTS_PATH = Path(__file__).resolve().parent / "constrained_albc" / "envs" / "main" / "mdp" / "faults.py"
_spec = importlib.util.spec_from_file_location("faults_under_test", _FAULTS_PATH)
faults = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(faults)
sample_thruster_health = faults.sample_thruster_health

N = 1000
T = 6
DEV = "cpu"
DEAD = (0, 3)
ALIVE = [1, 2, 4, 5]
SEED = 20260907


def _cfg(always_dead, fixed=None):
    """Minimal stand-in for FaultInjectionCfg -- only the fields the sampler reads."""
    return SimpleNamespace(
        thruster_fail_prob=0.30,
        thruster_health_range=(0.0, 0.5),
        thruster_dead_frac=0.5,
        thruster_fixed_health=fixed,
        thruster_always_dead=always_dead,
    )


def _severity():
    """Random per-env severity, drawn from its own generator so the two runs below
    compare against an identical severity vector as well as an identical sampler seed."""
    g = torch.Generator(device=DEV).manual_seed(7)
    return torch.rand(N, device=DEV, generator=g)


def _run(always_dead, fixed=None):
    gen = torch.Generator(device=DEV).manual_seed(SEED)
    return sample_thruster_health(N, T, _cfg(always_dead, fixed), DEV, gen, _severity())


def test_bernoulli_path_dead_columns_are_exactly_zero():
    health = _run(DEAD)
    assert health.shape == (N, T)
    for i in DEAD:
        assert torch.equal(health[:, i], torch.zeros(N)), f"column {i} not all-zero"


def test_bernoulli_path_leaves_other_columns_bit_identical():
    on = _run(DEAD)
    off = _run(())
    assert torch.equal(on[:, ALIVE], off[:, ALIVE]), "always_dead perturbed a live column"
    # and the off run must NOT have zeroed the dead columns for us (otherwise the
    # comparison above would be vacuous)
    assert (off[:, list(DEAD)] > 0.0).any()


def test_fixed_health_path():
    fixed = (1.0, 0.8, 1.0, 1.0, 0.0, 1.0)  # m4 dead, the FTC-m4 eval instrument
    on = _run(DEAD, fixed=fixed)
    off = _run((), fixed=fixed)
    for i in DEAD:
        assert torch.equal(on[:, i], torch.zeros(N))
    assert torch.equal(on[:, ALIVE], off[:, ALIVE])
    # always_dead must OUTRANK the fixed vector, not be outranked by it
    assert off[0, 0].item() == 1.0 and on[0, 0].item() == 0.0


def test_empty_tuple_is_a_no_op_on_both_paths():
    g1 = torch.Generator(device=DEV).manual_seed(SEED)
    g2 = torch.Generator(device=DEV).manual_seed(SEED)
    sev = _severity()
    with_field = sample_thruster_health(N, T, _cfg(()), DEV, g1, sev)
    cfg_without = _cfg(())
    del cfg_without.thruster_always_dead  # a cfg predating the field
    without_field = sample_thruster_health(N, T, cfg_without, DEV, g2, sev)
    assert torch.equal(with_field, without_field)


def test_out_of_range_index_raises():
    try:
        _run((0, 6))
    except ValueError as exc:
        assert "out of range" in str(exc)
    else:
        raise AssertionError("expected ValueError for index 6 with num_thrusters=6")


def test_apply_always_dead_on_a_healthy_baseline():
    """The fault-disabled path in albc_env._reset_physics: ones, then the mask."""
    health = faults.apply_always_dead(torch.ones(N, T), _cfg(DEAD))
    for i in DEAD:
        assert torch.equal(health[:, i], torch.zeros(N))
    assert torch.equal(health[:, ALIVE], torch.ones(N, len(ALIVE)))


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}", flush=True)
