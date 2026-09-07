"""PLAN §4 item 11: exogenous heave disturbance (`FzDisturbanceCfg`).

Checks the numerical core in `mdp/disturbance.py` -- the same functions albc_env calls,
not a copy of their arithmetic:

  * ``|Fz| <= strength * fz_max`` elementwise, for a batch of strengths and draws;
  * ``My == my_per_fz * Fz`` EXACTLY (the sign carries finding/155's realised
    ``deployed_tam.json`` ratio -0.1458; a flipped sign is the failure this guards);
  * ``strength == 0`` -> the whole wrench is zeros (the DORAEMON nominal must be inert);
  * the hold re-draw fires only for envs whose counter has reached 0.

The hold-expiry test mirrors ``ALBCEnv._step_fz_disturbance`` (a two-line countdown on
the env's own buffer) rather than importing it, because that method needs Isaac to
construct an env; the arithmetic it drives is the ``sample_fz_and_hold`` call tested
above. Pure torch, runs on CPU.

Run:  python3 -m pytest test_fz_disturbance.py -q
"""
import importlib.util
from pathlib import Path

import torch

_PATH = Path(__file__).resolve().parent / "constrained_albc" / "envs" / "main" / "mdp" / "disturbance.py"
_spec = importlib.util.spec_from_file_location("disturbance_under_test", _PATH)
disturbance = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(disturbance)

N = 10_000
BODIES = 1
DEV = "cpu"
FZ_MAX = 13.0            # config default: one vertical at the 13 N measured coefficient
MY_PER_FZ = -0.1458      # finding/155, realised deployed_tam.json My/Fz
HOLD_S = (1.0, 5.0)
STEP_DT = 0.02           # 50 Hz policy step (decimation 4 x sim dt 0.005)


def _strengths(seed=1):
    g = torch.Generator(device=DEV).manual_seed(seed)
    return torch.rand(N, device=DEV, generator=g)


def _draw(strength, seed=99):
    g = torch.Generator(device=DEV).manual_seed(seed)
    return disturbance.sample_fz_and_hold(strength, FZ_MAX, HOLD_S, g)


def test_magnitude_is_bounded_by_strength():
    strength = _strengths()
    fz, _ = _draw(strength)
    assert torch.all(fz.abs() <= strength * FZ_MAX + 1e-6)
    # the bound must be TIGHT, not vacuous: some env has to get near its own ceiling
    ratio = fz.abs() / (strength * FZ_MAX).clamp(min=1e-9)
    assert ratio.max().item() > 0.99


def test_sign_is_two_sided():
    """The depth PID pushes both ways -- a one-sided draw would be a systematic bias."""
    fz, _ = _draw(_strengths())
    assert (fz > 0).any() and (fz < 0).any()
    assert abs(fz.mean().item()) < 0.2  # ~0 by symmetry, not pinned to one side


def test_hold_is_inside_its_range():
    _, hold = _draw(_strengths())
    lo, hi = HOLD_S
    assert torch.all(hold >= lo) and torch.all(hold <= hi)
    assert hold.std().item() > 0.1  # randomized in TIMING, not a constant hold


def test_zero_strength_gives_an_all_zero_wrench():
    strength = torch.zeros(N, device=DEV)
    fz, hold = _draw(strength)
    assert torch.equal(fz, torch.zeros(N))
    forces = torch.zeros(N, BODIES, 3, device=DEV)
    torques = torch.zeros(N, BODIES, 3, device=DEV)
    disturbance.write_fz_wrench(forces, torques, fz, MY_PER_FZ)
    assert torch.equal(forces, torch.zeros(N, BODIES, 3))
    assert torch.equal(torques, torch.zeros(N, BODIES, 3))
    # the hold still ticks, so an env at nominal rejoins the band the moment DORAEMON opens
    assert torch.all(hold >= HOLD_S[0])


def test_wrench_couples_my_to_fz_exactly():
    fz, _ = _draw(_strengths())
    forces = torch.zeros(N, BODIES, 3, device=DEV)
    torques = torch.zeros(N, BODIES, 3, device=DEV)
    disturbance.write_fz_wrench(forces, torques, fz, MY_PER_FZ)

    assert torch.equal(forces[:, 0, 2], fz)
    assert torch.equal(torques[:, 0, 1], MY_PER_FZ * fz)
    # every other component untouched
    assert torch.equal(forces[:, :, :2], torch.zeros(N, BODIES, 2))
    assert torch.equal(torques[:, :, 0], torch.zeros(N, BODIES))
    assert torch.equal(torques[:, :, 2], torch.zeros(N, BODIES))
    # the coupling is NEGATIVE (finding/155): +Fz produces -My
    pos = fz > 0
    assert torch.all(torques[pos, 0, 1] < 0)


def test_redraw_fires_only_for_expired_envs():
    """_step_fz_disturbance: hold -= step_dt, then re-draw where it reached 0."""
    strength = torch.full((4,), 0.5)
    fz = torch.tensor([1.0, 2.0, 3.0, 4.0])
    hold = torch.tensor([STEP_DT, 3.0, STEP_DT / 2.0, 1.0])  # envs 0 and 2 expire this step

    hold = hold - STEP_DT
    expired = hold <= 0.0
    assert expired.tolist() == [True, False, True, False]

    ids = expired.nonzero(as_tuple=True)[0]
    new_fz, new_hold = disturbance.sample_fz_and_hold(strength[ids], FZ_MAX, HOLD_S)
    fz[ids] = new_fz
    hold[ids] = new_hold

    # untouched envs keep BOTH their force and their remaining hold
    assert fz[1].item() == 2.0 and fz[3].item() == 4.0
    assert abs(hold[1].item() - (3.0 - STEP_DT)) < 1e-6
    assert abs(hold[3].item() - (1.0 - STEP_DT)) < 1e-6
    # re-drawn envs get a fresh hold back inside the range (no negative carry-over)
    assert torch.all(hold[ids] >= HOLD_S[0])
    assert torch.all(fz[ids].abs() <= 0.5 * FZ_MAX + 1e-6)


if __name__ == "__main__":
    for name, fn in sorted(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            print(f"PASS {name}", flush=True)
