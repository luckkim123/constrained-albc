# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free unit tests for compute_student_extra_obs (E1/B2 gen-1 side-channel).

Also covers the student config/model widening for the extra channels (A3), the
GRU rollout collector's extra-channel round-trip (A4), the --extra_obs_dim launch
flag + student/env cross-check (A9), and the 2026-08-03 fix-wave regressions
(train/eval sensor-cfg round-trip, full_dof/TDC AttributeError guard, the shared
STUDENT_EXTRA_OBS_KEY constant, and the clone-on-return safety fix).

Loads observations.py standalone (bypasses constrained_albc/__init__ -> isaaclab.sim
-> pxr). See _load_observations() docstring.
"""

import ast
import importlib.util
import logging
import os
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


# ---------------------------------------------------------------------------
# A9: --extra_obs_dim launch flag + student/env cross-check
# (scripts/train_student.py calls AppLauncher() at module import time -- not
# importable standalone -- so the check function is AST-extracted and exec'd,
# same pattern as tests/test_bias_ema_obs.py's apply_bias_ema_obs extraction.)
# ---------------------------------------------------------------------------

_TRAIN_STUDENT_PATH = (
    Path(__file__).resolve().parent.parent / "scripts" / "train_student.py"
)


def _load_check_extra_obs_consistency():
    """Extract _check_extra_obs_consistency's source via AST and exec it standalone.

    The function body only references builtins (bool, ValueError, f-string formatting
    of its two scalar args), so it needs no mocking.
    """
    tree = ast.parse(_TRAIN_STUDENT_PATH.read_text())
    func_node = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_check_extra_obs_consistency"
    )
    namespace: dict = {}
    exec(compile(ast.unparse(func_node), "<_check_extra_obs_consistency>", "exec"), namespace)
    return namespace["_check_extra_obs_consistency"]


def test_extra_obs_cross_check_passes_when_both_off():
    check = _load_check_extra_obs_consistency()
    check(0, False)  # must not raise


def test_extra_obs_cross_check_passes_when_both_on():
    check = _load_check_extra_obs_consistency()
    check(4, True)  # must not raise


def test_extra_obs_cross_check_raises_when_dim_set_but_env_flag_off():
    """extra_obs_dim>0 + env flag off: env never publishes the key (today caught by
    collector.py's assert -- loud, but assert-dependent)."""
    check = _load_check_extra_obs_consistency()
    with pytest.raises(ValueError, match=r"extra_obs_dim=4"):
        check(4, False)


def test_extra_obs_cross_check_raises_when_env_flag_on_but_dim_zero():
    """extra_obs_dim==0 + env flag on: the env computes the channels and nobody reads
    them -- completely silent today, the direction that would corrupt a verdict."""
    check = _load_check_extra_obs_consistency()
    with pytest.raises(ValueError, match=r"use_student_extra_obs=True"):
        check(0, True)


def test_extra_obs_dim_argparse_default_is_zero():
    """Static contract: --extra_obs_dim defaults to 0 -- every existing recipe stays
    byte-identical unless a launch explicitly opts in."""
    tree = ast.parse(_TRAIN_STUDENT_PATH.read_text())
    call = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.Call)
        and isinstance(n.func, ast.Attribute) and n.func.attr == "add_argument"
        and any(isinstance(a, ast.Constant) and a.value == "--extra_obs_dim" for a in n.args)
    )
    default_kw = next(kw for kw in call.keywords if kw.arg == "default")
    assert isinstance(default_kw.value, ast.Constant)
    assert default_kw.value.value == 0


def test_extra_obs_cross_check_raises_when_dim_is_not_0_or_4():
    """Minor item 1: bool(dim) != bool(flag) only checks truthiness, so --extra_obs_dim 3
    against a flag-on env used to pass this check and die later in collector.py with a
    bare shape mismatch. The env always emits exactly 4 channels."""
    check = _load_check_extra_obs_consistency()
    with pytest.raises(ValueError, match=r"must be 0 \(off\) or 4 \(on\)"):
        check(3, True)


# ---------------------------------------------------------------------------
# IMPORTANT-2: _resolve_extra_obs_env_flag tolerates env variants (full_dof, TDC)
# that have no 'use_student_extra_obs' field at all, instead of a bare AttributeError.
# ---------------------------------------------------------------------------


def _load_resolve_extra_obs_env_flag():
    tree = ast.parse(_TRAIN_STUDENT_PATH.read_text())
    func_node = next(
        n for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "_resolve_extra_obs_env_flag"
    )
    namespace: dict = {}
    exec(compile(ast.unparse(func_node), "<_resolve_extra_obs_env_flag>", "exec"), namespace)
    return namespace["_resolve_extra_obs_env_flag"]


def test_resolve_extra_obs_env_flag_no_longer_raises_attributeerror_when_field_absent():
    """The regression: full_dof/config.py's ALBCEnvCfg has no 'use_student_extra_obs'
    field, so reading it unconditionally used to raise AttributeError before gym.make
    ever ran. --extra_obs_dim==0 (the default) against such a cfg must resolve to False,
    not raise."""
    resolve = _load_resolve_extra_obs_env_flag()
    full_dof_like_cfg = types.SimpleNamespace()  # no use_student_extra_obs attribute
    assert resolve(full_dof_like_cfg, 0) is False


def test_resolve_extra_obs_env_flag_raises_named_error_when_dim_set_but_field_absent():
    """extra_obs_dim>0 against a variant with no field is a genuine user mistake and
    must get a named ValueError, not a bare AttributeError."""
    resolve = _load_resolve_extra_obs_env_flag()
    full_dof_like_cfg = types.SimpleNamespace()
    with pytest.raises(ValueError, match="has no 'use_student_extra_obs' field"):
        resolve(full_dof_like_cfg, 4)


def test_resolve_extra_obs_env_flag_passes_through_when_field_present():
    resolve = _load_resolve_extra_obs_env_flag()
    main_like_cfg = types.SimpleNamespace(use_student_extra_obs=True)
    assert resolve(main_like_cfg, 4) is True
    main_like_cfg2 = types.SimpleNamespace(use_student_extra_obs=False)
    assert resolve(main_like_cfg2, 0) is False


# ---------------------------------------------------------------------------
# IMPORTANT-1: the 4 sensor-model knobs must round-trip through the student
# checkpoint (train -> eval), not silently default at eval time.
# ---------------------------------------------------------------------------


_RUNNER_PATH = _STUDENT_DIR / "runner.py"


def _load_save_checkpoint():
    """AST-extract StudentRunner._save_checkpoint standalone (same extraction pattern as
    _load_check_extra_obs_consistency above), deliberately WITHOUT importing runner.py as
    a module: runner.py does `import wandb` at module level, which is fragile mid-suite
    (some other test's omni/pxr/carb/warp mock stubs left in sys.modules corrupt wandb's
    own import chain when it is first imported later in the session -- see conftest.py's
    docstring for the general failure class). The method body only touches os/torch/
    logger, none of which need the rest of runner.py.
    """
    tree = ast.parse(_RUNNER_PATH.read_text())
    class_node = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "StudentRunner")
    func_node = next(
        n for n in ast.walk(class_node) if isinstance(n, ast.FunctionDef) and n.name == "_save_checkpoint"
    )
    namespace: dict = {"os": os, "torch": torch, "logger": logging.getLogger("test_save_checkpoint")}
    exec(compile(ast.unparse(func_node), "<_save_checkpoint>", "exec"), namespace)
    return namespace["_save_checkpoint"]


def _fake_student_runner_self(tmp_path, env_cfg_ns, models_mod, cfg_mod):
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 4
    cfg.privileged_dim = 2
    cfg.latent_dim = 2
    cfg.gru_hidden = 4
    cfg.gru_head_hidden = 0
    student = models_mod.make_student_encoder(cfg)
    fake_env = types.SimpleNamespace(unwrapped=types.SimpleNamespace(cfg=env_cfg_ns))
    (tmp_path / "models").mkdir()
    return types.SimpleNamespace(log_dir=str(tmp_path), student=student, cfg=cfg, env=fake_env)


def test_checkpoint_roundtrips_env_sensor_cfg(tmp_path):
    """_save_checkpoint must persist extra_obs_hold_steps/heave_lag_tau/depth_noise_std/
    accel_noise_std under 'env_sensor_cfg' -- without this, eval silently measures a
    different sensor model than the one the student was trained on."""
    cfg_mod, models_mod = _load_student("config", "models")
    env_cfg = types.SimpleNamespace(
        extra_obs_hold_steps=3, heave_lag_tau=0.07, depth_noise_std=0.02, accel_noise_std=0.01,
    )
    fake_self = _fake_student_runner_self(tmp_path, env_cfg, models_mod, cfg_mod)

    _load_save_checkpoint()(fake_self, 0)

    blob = torch.load(str(tmp_path / "models" / "student_0.pt"), weights_only=False)
    assert blob["env_sensor_cfg"] == {
        "extra_obs_hold_steps": 3,
        "heave_lag_tau": 0.07,
        "depth_noise_std": 0.02,
        "accel_noise_std": 0.01,
    }


def test_checkpoint_env_sensor_cfg_falls_back_when_env_variant_lacks_fields(tmp_path):
    """Degrades gracefully (getattr defaults) rather than crashing for env variants
    (full_dof/TDC) that have no sensor-cfg fields at all -- those variants never enable
    extra_obs_dim, so the fallback values are inert."""
    cfg_mod, models_mod = _load_student("config", "models")
    fake_self = _fake_student_runner_self(tmp_path, types.SimpleNamespace(), models_mod, cfg_mod)

    _load_save_checkpoint()(fake_self, 0)

    blob = torch.load(str(tmp_path / "models" / "student_0.pt"), weights_only=False)
    assert blob["env_sensor_cfg"] == {
        "extra_obs_hold_steps": 2,
        "heave_lag_tau": 0.05,
        "depth_noise_std": 0.01,
        "accel_noise_std": 0.0,
    }


# ---------------------------------------------------------------------------
# Minor item 6: compute_student_extra_obs must return a COPY, not the live
# env._student_extra_held reference (which _reset_task_and_state zeroes in place).
# ---------------------------------------------------------------------------


def test_compute_student_extra_obs_return_is_not_aliased_to_stored_buffer():
    compute_student_extra_obs = _load_observations().compute_student_extra_obs
    env = _fake_env()
    out = compute_student_extra_obs(env, _robot(depth=5.0))
    before = out.clone()
    # Simulate _reset_task_and_state's in-place reset of the stored buffer.
    env._student_extra_held[:] = 0.0
    assert torch.equal(out, before), "returned tensor was mutated by a later in-place reset"


# ---------------------------------------------------------------------------
# Minor item 7: "student_extra" must be ONE shared constant, not 5 independent
# string literals a rename could silently desync.
# ---------------------------------------------------------------------------


def test_student_extra_obs_key_is_a_shared_constant():
    cfg_mod, models_mod = _load_student("config", "models")
    assert models_mod.STUDENT_EXTRA_OBS_KEY == "student_extra"

    repo = Path(__file__).resolve().parent.parent
    albc_env = (repo / "constrained_albc" / "envs" / "main" / "albc_env.py").read_text()
    runner_src = (repo / "constrained_albc" / "envs" / "_core" / "student" / "runner.py").read_text()
    student_policy_src = (repo / "constrained_albc" / "analysis" / "student_policy.py").read_text()

    assert "STUDENT_EXTRA_OBS_KEY" in albc_env
    assert "observations[STUDENT_EXTRA_OBS_KEY]" in albc_env
    assert albc_env.count('"student_extra"') == 0

    assert runner_src.count("STUDENT_EXTRA_OBS_KEY") >= 3  # import + 2 call sites
    assert runner_src.count('"student_extra"') == 0

    assert student_policy_src.count("STUDENT_EXTRA_OBS_KEY") >= 3  # import + 2 call sites
    # One literal legitimately remains: the human-readable RuntimeError message text
    # (single-quoted, embedded in a double-quoted string -- not a dict-key usage).
    assert student_policy_src.count("'student_extra'") == 1
    assert student_policy_src.count('"student_extra"') == 0
