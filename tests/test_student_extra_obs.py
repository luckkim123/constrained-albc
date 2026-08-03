# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free unit tests for compute_student_extra_obs (E1/B2 gen-1 side-channel).

Also covers the student config/model widening for the extra channels (A3) and the
GRU rollout collector's extra-channel round-trip (A4).

Loads observations.py standalone (bypasses constrained_albc/__init__ -> isaaclab.sim
-> pxr). See _load_observations() docstring.
"""

import importlib.util
import sys
import types
from pathlib import Path

import pytest
import torch

_OBS_PATH = (
    Path(__file__).resolve().parent.parent
    / "constrained_albc" / "envs" / "main" / "mdp" / "observations.py"
)


def _load_observations():
    """Standalone module load -- bypasses constrained_albc/__init__ -> isaaclab.sim -> pxr.
    Same pattern as tests/test_dagger_schedule.py. Works because observations.py's only
    runtime import is torch (isaaclab is TYPE_CHECKING-only there); keep it that way.
    """
    spec = importlib.util.spec_from_file_location("albc_observations_standalone", _OBS_PATH)
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def _fake_env(n=4, dt=0.02, tau=0.05, depth_noise=0.0, hold=1):
    env = types.SimpleNamespace()
    env.cfg = types.SimpleNamespace(
        accel_noise_std=0.0, depth_noise_std=depth_noise, heave_lag_tau=tau,
        extra_obs_hold_steps=hold,
    )
    env.step_dt = dt
    env.device = "cpu"
    env._gravity_w = torch.tensor([0.0, 0.0, -9.81])
    env._depth_meas_prev = torch.zeros(n)
    env._heave_rate_filt = torch.zeros(n)
    env._extra_reset_pending = torch.ones(n, dtype=torch.bool)
    env._extra_tick = 0
    env._student_extra_held = torch.zeros(n, 4)
    return env


def _robot(n=4, depth=5.0):
    return types.SimpleNamespace(data=types.SimpleNamespace(
        body_lin_acc_w=torch.zeros(n, 1, 3),
        root_quat_w=torch.tensor([[1.0, 0, 0, 0]] * n),
        root_pos_w=torch.tensor([[0.0, 0.0, -depth]] * n),
    ))

def test_heave_lpf_no_reset_spike():
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env()
    robot = types.SimpleNamespace(data=types.SimpleNamespace(
        body_lin_acc_w=torch.zeros(4, 1, 3),
        root_quat_w=torch.tensor([[1.0, 0, 0, 0]] * 4),
        root_pos_w=torch.tensor([[0.0, 0.0, -5.0]] * 4),  # depth 5 m
    ))
    out = compute_student_extra_obs(env, robot)
    # First call after reset: differentiator re-anchored, heave rate must be ~0,
    # NOT depth/dt (= 250 m/s spike).
    assert out.shape == (4, 4)
    assert torch.allclose(out[:, 3], torch.zeros(4), atol=1e-6)
    # Constant depth afterwards -> heave stays 0; specific force = -g rotated = (0,0,9.81)
    out2 = compute_student_extra_obs(env, robot)
    assert torch.allclose(out2[:, 3], torch.zeros(4), atol=1e-6)
    assert torch.allclose(out2[:, 2], torch.full((4,), 9.81), atol=1e-4)

def test_heave_lpf_tracks_descent():
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env()
    depth = 5.0
    for _ in range(60):
        out = compute_student_extra_obs(env, _robot(depth=depth))
        depth += 0.02  # descending 1 m/s at dt=0.02
    # LPF settled: heave rate ~= +1.0 m/s (depth increasing)
    assert torch.allclose(out[:, 3], torch.full((4,), 1.0), atol=0.05)


def test_zero_order_hold_serves_stale_sample_and_uses_sensor_dt():
    """hold=2 (25 Hz): the vector must repeat on odd ticks, and the differentiator
    must divide by the SENSOR period (2*step_dt), not the control tick -- dividing by
    step_dt would report 2 m/s for a 1 m/s descent."""
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env(hold=2)
    depth, seen = 5.0, []
    for _ in range(120):
        seen.append(compute_student_extra_obs(env, _robot(depth=depth)).clone())
        depth += 0.02  # still 1 m/s of true descent per 0.02 s control tick
    # Held: every refresh is followed by one repeat of the identical vector.
    assert torch.equal(seen[-1], seen[-2]) or torch.equal(seen[-2], seen[-3])
    n_distinct = sum(1 for a, b in zip(seen[1:], seen[:-1]) if not torch.equal(a, b))
    assert n_distinct <= len(seen) // 2, f"refreshed too often: {n_distinct} of {len(seen)}"
    # Settled magnitude is still the TRUE 1 m/s -- proves sensor_dt, not step_dt.
    assert torch.allclose(seen[-1][:, 3], torch.full((4,), 1.0), atol=0.05)


_STUDENT_DIR = (
    Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "_core" / "student"
)


def _load_student(*module_names):
    """Exec _core/student modules by path without importing constrained_albc.
    Verbatim shape of tests/test_student_eval_obs_width.py::_load_student_models."""
    for pkg in ("constrained_albc", "constrained_albc.envs",
                "constrained_albc.envs._core", "constrained_albc.envs._core.student"):
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = []
            sys.modules[pkg] = m
    out = []
    for name in module_names:
        full = f"constrained_albc.envs._core.student.{name}"
        spec = importlib.util.spec_from_file_location(full, _STUDENT_DIR / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.envs._core.student"
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        out.append(mod)
    return out


def test_gru_input_widening():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 72
    cfg.extra_obs_dim = 4
    enc = models_mod.make_student_encoder(cfg)
    z, h = enc(torch.zeros(2, 5, 76))
    assert z.shape == (2, 5, 9)


def test_tcn_extra_rejected():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg(); cfg.encoder_type = "tcn"; cfg.extra_obs_dim = 4
    with pytest.raises(ValueError, match="GRU student only"):
        models_mod.make_student_encoder(cfg)


def test_extra_scale_tensor_off_when_extra_obs_dim_zero():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    assert models_mod.extra_scale_tensor(cfg, torch.device("cpu")) is None


def test_extra_scale_tensor_raises_on_short_scale():
    cfg_mod, models_mod = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.extra_obs_dim = 4
    cfg.extra_obs_scale = (10.0, 10.0)  # shorter than extra_obs_dim
    with pytest.raises(ValueError, match="extra_obs_scale has 2 entries but extra_obs_dim is 4"):
        models_mod.extra_scale_tensor(cfg, torch.device("cpu"))


def test_collector_extra_roundtrip():
    cfg_mod, coll_mod = _load_student("config", "collector")
    cfg = cfg_mod.StudentCfg(); cfg.encoder_type = "gru"; cfg.extra_obs_dim = 4
    cfg.num_envs = 3; cfg.n_steps_per_rollout = 2; cfg.minibatch_size = 6
    buf = coll_mod.RolloutBuffer(cfg, torch.device("cpu"))
    for t in range(2):
        # Per-env values must differ (not torch.full/uniform): iter_minibatches_gru
        # permutes envs via torch.randperm, so uniform data would still pass even if
        # extra_seq used a DIFFERENT permutation than obs_seq -- exactly the silent
        # env-mispairing corruption this test exists to catch.
        env_val = 100.0 * torch.arange(3, dtype=torch.float32) + t
        obs = env_val.unsqueeze(-1).expand(3, cfg.policy_obs_dim)
        extra = (env_val + 0.5).unsqueeze(-1).expand(3, 4)
        buf.add(obs, torch.zeros(3, cfg.privileged_dim), torch.zeros(3, 9),
                torch.zeros(3, 8), torch.zeros(3, dtype=torch.bool), extra=extra)
    (batch,) = buf.iter_minibatches_gru()
    assert batch.extra_seq.shape == (3, 2, 4)
    # Pairing invariant: holds under ANY permutation as long as obs_seq and extra_seq
    # used the SAME one; breaks the moment they diverge (e.g. reversed idx for one).
    assert torch.allclose(batch.extra_seq[:, :, 0], batch.obs_seq[:, :, 0] + 0.5)
