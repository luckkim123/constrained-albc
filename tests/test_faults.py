"""Tests for the pure fault-injection helpers in envs/main/mdp/faults.py.

The env wiring (when to call these, which buffers to write) is sim-bound and lives
in albc_env.py. The NUMERICAL core -- how a fault sample is drawn and how sensor
noise is added -- is factored into pure torch functions here so it is unit-testable
on plain torch without booting Isaac Sim.

Two contracts under test:
  1. Sampling: thruster health (Bernoulli fail * residual health), per-env sensor
     noise scale, per-env joint health -- all in their documented ranges, per-env.
  2. Sensor-noise application: the toggle-off path (scale is None) returns the obs
     UNCHANGED (byte-identical), and the on path adds scale[:,None]*noise.

Run headless: python3 -m pytest tests/test_faults.py
"""
from __future__ import annotations

import os
import sys

import torch

# faults.py is pure torch (no Isaac-Sim imports at module level); import by file path
# so the sim-bound albc_env package is never triggered.
_MDP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "constrained_albc",
    "envs",
    "main",
    "mdp",
)
sys.path.insert(0, _MDP)
import faults  # noqa: E402


class _FaultCfg:
    """Minimal stand-in for FaultInjectionCfg (avoids importing isaaclab configclass)."""

    thruster_fail_prob = 0.5
    thruster_health_range = (0.0, 0.5)
    sensor_noise_scale_range = (0.0, 2.0)
    joint_health_range = (0.5, 1.0)


# ---- 1. sensor-noise application: toggle-off is byte-identical ----------------


def test_apply_sensor_noise_disabled_is_identity():
    """scale=None -> obs returned unchanged (same object, no math)."""
    obs = torch.randn(4, 10)
    out = faults.apply_sensor_noise(obs, None, base_std=torch.ones(10))
    assert out is obs  # identity: not even a copy


def test_apply_sensor_noise_adds_scaled_noise():
    """scale provided -> obs + scale[:,None] * noise * base_std (deterministic noise)."""
    obs = torch.zeros(3, 4)
    scale = torch.tensor([0.0, 1.0, 2.0])
    base_std = torch.full((4,), 0.5)
    noise = torch.ones(3, 4)  # injected (deterministic) instead of randn
    out = faults.apply_sensor_noise(obs, scale, base_std=base_std, noise=noise)
    # env 0: +0; env 1: +1*1*0.5 = 0.5; env 2: +2*1*0.5 = 1.0
    assert torch.allclose(out[0], torch.zeros(4))
    assert torch.allclose(out[1], torch.full((4,), 0.5))
    assert torch.allclose(out[2], torch.full((4,), 1.0))


def test_apply_sensor_noise_does_not_mutate_input():
    """The on-path must not modify obs in place (returns a new tensor)."""
    obs = torch.zeros(2, 4)
    obs_ref = obs.clone()
    faults.apply_sensor_noise(obs, torch.ones(2), base_std=torch.ones(4), noise=torch.ones(2, 4))
    assert torch.equal(obs, obs_ref)


def test_two_stacked_sensor_noise_layers_none_is_identity():
    """Fault layer + DR layer, both off (scale None) -> obs byte-identical."""
    torch.manual_seed(0)
    obs = torch.randn(8, 69)
    base = torch.ones(69)
    out = faults.apply_sensor_noise(obs, None, base_std=base)   # fault layer off
    out = faults.apply_sensor_noise(out, None, base_std=base)   # DR layer off
    assert torch.equal(out, obs)  # same object, unchanged


def test_dr_layer_off_preserves_fault_layer():
    """DR layer off must not perturb an active fault layer's output."""
    torch.manual_seed(0)
    obs = torch.randn(4, 69)
    base = torch.ones(69)
    fault_scale = torch.full((4,), 0.5)
    fault_noise = torch.randn(4, 69)
    after_fault = faults.apply_sensor_noise(obs, fault_scale, base_std=base, noise=fault_noise)
    after_dr = faults.apply_sensor_noise(after_fault, None, base_std=base)  # DR off
    assert torch.equal(after_dr, after_fault)


def test_dr_layer_adds_scaled_noise_on_top():
    """DR layer on: adds dr_scale[:,None]*noise*base_std to whatever came before."""
    torch.manual_seed(0)
    obs = torch.zeros(4, 69)
    base = torch.full((69,), 2.0)
    dr_scale = torch.full((4,), 0.5)
    dr_noise = torch.ones(4, 69)
    out = faults.apply_sensor_noise(obs, dr_scale, base_std=base, noise=dr_noise)
    # 0 + 0.5 * 1.0 * 2.0 = 1.0 per element
    assert torch.allclose(out, torch.ones(4, 69))


# ---- 2. thruster health sampling ---------------------------------------------


def test_sample_thruster_health_shape_and_range():
    cfg = _FaultCfg()
    h = faults.sample_thruster_health(8, 6, cfg, device="cpu", generator=torch.Generator().manual_seed(0))
    assert h.shape == (8, 6)
    # Every value is either exactly 1.0 (healthy) or within the failed-health range.
    healthy = h == 1.0
    failed = (h >= cfg.thruster_health_range[0]) & (h <= cfg.thruster_health_range[1])
    assert torch.all(healthy | failed)


def test_sample_thruster_health_zero_prob_all_nominal():
    """fail_prob=0 -> every thruster healthy (1.0)."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 0.0
    h = faults.sample_thruster_health(16, 6, cfg, device="cpu", generator=torch.Generator().manual_seed(1))
    assert torch.all(h == 1.0)


def test_sample_thruster_health_full_prob_all_failed():
    """fail_prob=1 -> every thruster in the failed-health range (none at 1.0)."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 1.0
    cfg.thruster_health_range = (0.0, 0.5)
    h = faults.sample_thruster_health(16, 6, cfg, device="cpu", generator=torch.Generator().manual_seed(2))
    assert torch.all(h <= 0.5)
    assert torch.all(h >= 0.0)


# ---- 3. scalar per-env fault sampling (sensor noise scale, joint health) ------


def test_sample_uniform_per_env_in_range():
    rng = torch.Generator().manual_seed(3)
    s = faults.sample_uniform_per_env(64, (0.0, 2.0), device="cpu", generator=rng)
    assert s.shape == (64,)
    assert torch.all(s >= 0.0) and torch.all(s <= 2.0)

    j = faults.sample_uniform_per_env(64, (0.5, 1.0), device="cpu", generator=rng)
    assert torch.all(j >= 0.5) and torch.all(j <= 1.0)


# ---- 4. joint health applied as effort-limit scale ---------------------------


def test_apply_joint_health_scales_effort():
    """effort_limit * health, per env, broadcast over joints."""
    effort = torch.full((4, 2), 10.0)
    health = torch.tensor([1.0, 0.5, 0.0, 0.75])
    out = faults.apply_joint_health(effort, health)
    assert torch.allclose(out[:, 0], torch.tensor([10.0, 5.0, 0.0, 7.5]))
    assert torch.allclose(out[:, 1], torch.tensor([10.0, 5.0, 0.0, 7.5]))


def test_apply_joint_health_none_is_identity():
    effort = torch.full((4, 2), 10.0)
    out = faults.apply_joint_health(effort, None)
    assert out is effort
