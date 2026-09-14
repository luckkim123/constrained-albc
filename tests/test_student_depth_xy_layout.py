# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Student input layout against a depth_xy teacher (80D policy_obs).

Env order (albc_env._get_observations): [core 72 | gen-2 IMU+heave 4 | depth_xy e_z, int, u_x, u_y 4].
The deployable recipe (R3a: tail mode off) feeds the teacher-normalized 80D unchanged. Tail mode
must take the RAW gen-2 block at [72:76] and leave the depth_xy block normalized; before the fix
it took the last 4 dims, i.e. the depth/XY task channels, and scaled them as IMU/heave.

Loads _core/student/{config,models}.py standalone (same pattern as test_student_extra_parity.py).
"""
from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import torch

REPO = Path(__file__).resolve().parents[1]
STUDENT_DIR = REPO / "constrained_albc" / "envs" / "_core" / "student"


def _load_student(*module_names: str):
    for pkg in (
        "constrained_albc",
        "constrained_albc.envs",
        "constrained_albc.envs._core",
        "constrained_albc.envs._core.student",
    ):
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = []
            sys.modules[pkg] = m
    out = []
    for name in module_names:
        full = f"constrained_albc.envs._core.student.{name}"
        spec = importlib.util.spec_from_file_location(full, STUDENT_DIR / f"{name}.py")
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.envs._core.student"
        sys.modules[full] = mod
        spec.loader.exec_module(mod)
        out.append(mod)
    return out


def _obs(width: int):
    """Every dim distinct, so any shifted slice is visible; obs_n = affine elementwise stand-in."""
    raw = torch.arange(width, dtype=torch.float32).expand(3, width).clone()
    return raw, raw * 2.0 + 1000.0


def test_policy_tail_after_reads_depth_xy_from_env_cfg():
    _, m = _load_student("config", "models")
    assert m.policy_tail_after(SimpleNamespace(depth_xy=SimpleNamespace(enable=True))) == 4
    assert m.policy_tail_after(SimpleNamespace(depth_xy=SimpleNamespace(enable=False))) == 0
    assert m.policy_tail_after(SimpleNamespace()) == 0  # full_dof/TDC cfg: no depth_xy field
    assert m.DEPTH_XY_OBS_N == 4 and m.POLICY_TAIL_N == 4
    assert cfg_default_is_zero()


def cfg_default_is_zero() -> bool:
    cfg_mod, _ = _load_student("config", "models")
    return cfg_mod.StudentCfg().policy_tail_after == 0


def test_plain_student_sees_teacher_normalized_80d_unchanged():
    """The deployable recipe: tail off, so the encoder input IS the teacher actor's normalized obs."""
    cfg_mod, m = _load_student("config", "models")
    cfg = cfg_mod.StudentCfg()
    cfg.encoder_type = "gru"
    cfg.policy_obs_dim = 80
    raw, obs_n = _obs(80)
    x = m.student_input(obs_n, None, m.extra_scale_tensor(cfg, torch.device("cpu")))
    assert torch.equal(x, obs_n)
    assert m.make_student_encoder(cfg).gru.input_size == 80


def test_tail_split_with_depth_xy_takes_the_gen2_block_not_the_last_four():
    _, m = _load_student("config", "models")
    raw, obs_n = _obs(80)
    core, extra = m.split_policy_tail(
        obs_raw=raw, obs_n=obs_n, n_tail=m.POLICY_TAIL_N, n_after=m.DEPTH_XY_OBS_N
    )
    # Off by 4 either way fails here: [76:80] would be the depth/XY channels, [68:72] bias_ema.
    assert torch.equal(extra, raw[:, 72:76])
    assert torch.equal(core, torch.cat([obs_n[:, :72], obs_n[:, 76:80]], dim=-1))
    x = m.student_input(core, extra, torch.tensor((10.0, 10.0, 10.0, 1.0)))
    assert x.shape == (3, 80)
    # depth/XY channels reach the encoder with the teacher's normalization, never the IMU scale.
    assert torch.equal(x[:, 72:76], obs_n[:, 76:80])
    assert torch.equal(x[:, 76:80], raw[:, 72:76] / torch.tensor((10.0, 10.0, 10.0, 1.0)))


def test_tail_split_without_depth_xy_is_the_pre_fix_split():
    _, m = _load_student("config", "models")
    raw, obs_n = _obs(76)
    core, extra = m.split_policy_tail(obs_raw=raw, obs_n=obs_n, n_tail=4)
    core0, extra0 = m.split_policy_tail(obs_raw=raw, obs_n=obs_n, n_tail=4, n_after=0)
    assert torch.equal(core, obs_n[:, :72]) and torch.equal(extra, raw[:, 72:76])
    assert torch.equal(core0, core) and torch.equal(extra0, extra)


_CONSUMERS = [
    REPO / "constrained_albc" / "envs" / "_core" / "student" / "runner.py",
    REPO / "constrained_albc" / "analysis" / "student_policy.py",
    REPO / "constrained_albc" / "analysis" / "eval.py",
]


def test_every_tail_split_call_passes_the_offset():
    """A consumer that omits n_after silently falls back to the pre-depth_xy split."""
    for path in _CONSUMERS:
        tree = ast.parse(path.read_text())
        calls = [
            n for n in ast.walk(tree)
            if isinstance(n, ast.Call) and getattr(n.func, "id", None) == "split_policy_tail"
        ]
        assert calls, f"{path.name}: no split_policy_tail call"
        for call in calls:
            assert any(kw.arg == "n_after" for kw in call.keywords), f"{path.name}:{call.lineno}"


def test_offset_comes_from_the_env_and_round_trips_through_the_checkpoint():
    runner = _CONSUMERS[0].read_text()
    policy = _CONSUMERS[1].read_text()
    evalpy = _CONSUMERS[2].read_text()
    assert "cfg.policy_tail_after = policy_tail_after(env.unwrapped.cfg)" in runner
    assert '"policy_tail_after")' in policy  # restored from the saved cfg
    assert "policy_tail_after(env_cfg)" in evalpy  # eval refuses a disagreeing env
