# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Tests for summarize_student_extra -- the obs4 B0 bite check (2026-08-03).

The function exists because an extra-observation channel that is present but degenerate is a
SILENT no-op: the run completes, the metrics look ordinary, and the verdict is about nothing.
The E2 delay injector did exactly that for a full sweep. So every test here names the PRODUCTION
defect it catches and constructs data that fails only under that defect -- a test whose data
cannot distinguish the failure is decoration, which is how three gates shipped broken in the
obs4 plan itself.

    nonzero       <- compute_student_extra_obs returns a zero buffer (channel wired but unfilled)
    time_varying  <- the buffer is filled once and the per-step update is skipped
    gravity_ok    <- the specific-force convention slips: sign flip, or gravity subtracted out
    hold_ok       <- the zero-order hold branch is bypassed, so the run measures a 50 Hz channel
                     the real <=25 Hz sensor bus cannot deliver
    heave_snr     <- the heave channel is present and moving but carries less signal than the
                     sensor noise its own depth-noise chain imposes

metrics.py is pure numpy, so this runs on plain python3 with no Isaac Sim and no GPU.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "constrained_albc", "analysis"))
from _eval_dr.metrics import summarize_student_extra  # noqa: E402


def _healthy(T: int = 200, E: int = 8, hold: int = 2, seed: int = 0) -> np.ndarray:
    """A (T, E, 4) block shaped like what a correct run produces.

    Distinguishable along every axis the code could scramble: each (env, channel) gets its own
    offset and each timestep its own value, so a permutation or a broadcast bug cannot pass by
    accident. The zero-order hold is applied last, exactly as the env applies it.
    """
    rng = np.random.default_rng(seed)
    base = rng.normal(0.0, 0.5, size=(T, E, 4))
    base += np.arange(E)[None, :, None] * 0.01       # env-distinguishable
    base += np.arange(T)[:, None, None] * 1e-4       # time-distinguishable
    base[..., 2] += 9.81                             # gravity-included convention
    # zero-order hold: sample only on a boundary, repeat in between
    held = base.copy()
    for t in range(T):
        if t % hold != 0:
            held[t] = held[t - 1]
    return held


def test_healthy_block_passes_every_check():
    """Baseline: correct data must pass, or the gate fires on correct code and gets deleted."""
    s = summarize_student_extra(_healthy(), hold_steps=2)
    assert s["nonzero"] and s["time_varying"] and s["gravity_ok"] and s["hold_ok"]
    assert s["shape"] == [200, 8, 4]
    assert s["sensor_dt"] == pytest.approx(0.04)


def test_nonzero_fails_on_an_unfilled_channel():
    """Defect: compute_student_extra_obs publishes the buffer but never writes channel 3."""
    x = _healthy()
    x[..., 3] = 0.0
    s = summarize_student_extra(x, hold_steps=2)
    assert s["nonzero"] is False
    assert s["per_channel_absmax"][3] == 0.0


def test_time_varying_fails_on_a_frozen_channel():
    """Defect: the buffer is filled at reset and the per-step update never runs.

    Note this is NOT caught by `nonzero` -- a frozen channel is large and constant, which is
    exactly why the two checks are separate.
    """
    x = _healthy()
    x[..., 0] = x[0, :, 0][None, :]
    s = summarize_student_extra(x, hold_steps=2)
    assert s["nonzero"] is True
    assert s["time_varying"] is False


@pytest.mark.parametrize("broken, label", [(-1.0, "sign flip"), (0.0, "gravity subtracted out")])
def test_gravity_ok_fails_on_a_convention_slip(broken, label):
    """Defect: a_imu_b loses the gravity-included convention (R^T(a - g) becomes R^T(a) or -R^T(a - g))."""
    x = _healthy()
    x[..., 2] = (x[..., 2] - 9.81) + broken * 9.81
    s = summarize_student_extra(x, hold_steps=2)
    assert s["gravity_ok"] is False, label


def test_hold_ok_fails_when_the_zero_order_hold_is_bypassed():
    """Defect: extra_obs_hold_steps is ignored and the channel updates every tick.

    This is the one that would make a GO verdict FALSE rather than merely noisy -- the run would
    have validated a 50 Hz channel the robot cannot deliver.
    """
    fresh_every_tick = _healthy(hold=1)
    s = summarize_student_extra(fresh_every_tick, hold_steps=2)
    assert s["hold_ok"] is False
    assert s["repeat_fraction"] == pytest.approx(0.0, abs=1e-9)
    assert s["expected_repeat_fraction"] == pytest.approx(0.5)


def test_hold_ok_fails_when_the_hold_is_longer_than_declared():
    """Defect: the hold is applied with the wrong period (e.g. cfg read once and stale at 4)."""
    s = summarize_student_extra(_healthy(hold=4), hold_steps=2)
    assert s["hold_ok"] is False
    assert s["repeat_fraction"] == pytest.approx(0.75, abs=0.01)


def _pure_noise_heave(T: int = 40000, E: int = 8, sigma: float = 0.01,
                      tau: float = 0.05, sensor_dt: float = 0.04, seed: int = 1) -> np.ndarray:
    """The heave channel a run produces when TRUE heave is exactly zero.

    Reproduces the producer's real chain (observations.py): a first difference of two INDEPENDENT
    noisy depth samples, then the first-order LPF `y += alpha*(raw - y)`. This is the realistic
    degenerate case -- the channel is wired, moving, and carries nothing.
    """
    rng = np.random.default_rng(seed)
    d = rng.normal(0.0, sigma, size=(T, E))
    raw = (d[1:] - d[:-1]) / sensor_dt
    alpha = sensor_dt / (tau + sensor_dt)
    y = np.zeros(E)
    out = []
    for step in raw:
        y = y + alpha * (step - y)
        out.append(y.copy())
    return np.array(out[1000:])


def test_noise_floor_matches_the_producers_actual_chain_not_sigma_over_dt():
    """Defect: taking the floor as depth_noise_std/sensor_dt.

    That naive form ignores BOTH the sqrt(2) from differencing two independent draws AND the LPF
    (with its MA(1) correlation), and overstates the floor by ~2x at the defaults -- which made a
    100%-noise channel score 0.504 and read as "well below its own noise". Measured against a
    simulation of the real chain, not against the algebra that produced it.
    """
    noise = _pure_noise_heave()
    x = np.zeros((noise.shape[0], noise.shape[1], 4))
    x[..., 3] = noise
    s = summarize_student_extra(x, hold_steps=2, depth_noise_std=0.01, heave_lag_tau=0.05)
    assert s["heave_noise_floor"] == pytest.approx(noise.std(), rel=0.05)
    naive = 0.01 / 0.04  # depth_noise_std / sensor_dt, the rejected form
    assert naive / s["heave_noise_floor"] == pytest.approx(1.985, rel=0.05)


def test_heave_snr_is_zero_for_a_channel_that_is_pure_sensor_noise():
    """The realistic degenerate case: present, moving, carrying nothing.

    Defect this pins: any floor that is not the true noise std makes this case score far from 0,
    and an H2 "channels carry nothing" verdict would then cite a number that means something else.
    """
    noise = _pure_noise_heave()
    x = np.zeros((noise.shape[0], noise.shape[1], 4))
    x[..., 3] = noise
    s = summarize_student_extra(x, hold_steps=2, depth_noise_std=0.01, heave_lag_tau=0.05)
    assert s["heave_total_to_noise"] == pytest.approx(1.0, abs=0.1)
    assert s["heave_snr"] < 0.5


def test_heave_snr_recovers_a_known_signal_to_noise_ratio():
    """Inverse guard: a channel with real signal must NOT read as unusable.

    A gate that flags healthy data gets deleted by the next person, which is worse than no gate.
    Signal amplitude is set to 2x the noise std, so heave_snr must land near 2.
    """
    noise = _pure_noise_heave()
    T, E = noise.shape
    signal = 2.0 * noise.std() * np.sin(np.arange(T) * 0.01)[:, None] * np.ones((1, E))
    x = np.zeros((T, E, 4))
    x[..., 3] = noise + signal
    s = summarize_student_extra(x, hold_steps=2, depth_noise_std=0.01, heave_lag_tau=0.05)
    assert s["heave_snr"] > 1.0
    assert s["heave_snr"] == pytest.approx(2.0 / np.sqrt(2), rel=0.25)  # rms of a sine = A/sqrt(2)


def test_a_single_dead_env_is_caught_and_not_averaged_away():
    """Defect: judging delivery on a pooled aggregate instead of per env.

    Every piece of the producer's state is per-env and _reset_idx zeroes the held buffer per env,
    so one dead env is the plausible shape. A mean over envs hides it behind seven healthy ones.
    """
    x = _healthy(E=8)
    x[:, 3, :] = 0.0
    s = summarize_student_extra(x, hold_steps=2)
    assert s["nonzero"] is False
    assert s["n_env_degenerate"] == 1


def test_a_single_frozen_env_is_caught_and_not_averaged_away():
    """Same axis, the frozen variant: one env stops updating while the rest keep moving."""
    x = _healthy(E=8)
    x[:, 5, :] = x[0, 5, :][None, :]
    s = summarize_student_extra(x, hold_steps=2)
    assert s["nonzero"] is True
    assert s["time_varying"] is False
    assert s["n_env_degenerate"] == 1


def test_latent_npz_writer_still_carries_exactly_l_hat_and_l_true():
    """The identity property this whole change is justified by, pinned in source rather than prose.

    The extra channels go to their OWN file so `latent_<level>.npz` stays identical to what the
    unpatched eval.py produced -- that identity is what licenses comparing a new arm against C3's
    stored numbers. A future edit that folds `extra=` into this call would silently void it, and
    nothing else in the tree would notice. Fails on exactly that change.

    Source-level because eval.py cannot be imported without a booted Isaac Sim.
    """
    import ast

    src = Path(__file__).resolve().parents[1] / "constrained_albc" / "analysis" / "eval.py"
    tree = ast.parse(src.read_text())
    latent_writes = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not (isinstance(node.func, ast.Attribute) and node.func.attr == "savez_compressed"):
            continue
        target = ast.unparse(node.args[0]) if node.args else ""
        if "latent_" in target:
            latent_writes.append({kw.arg for kw in node.keywords})

    assert latent_writes, "no savez_compressed writing latent_<level>.npz found in eval.py"
    for kwargs in latent_writes:
        assert kwargs == {"l_hat", "l_true"}, (
            f"latent_<level>.npz writer gained/lost keys: {sorted(kwargs)}. That file must stay "
            "identical to the unpatched instrument's output; put new arrays in their own file."
        )


def test_rejects_a_wrong_rank_array_loudly():
    """A flattened or per-step array must raise, not silently summarize the wrong axes."""
    with pytest.raises(ValueError, match="expects"):
        summarize_student_extra(np.zeros((200, 4)), hold_steps=2)
