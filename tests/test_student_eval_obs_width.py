# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free checks for the student-eval obs-width propagation fix.

Regression guard for the E4 (in-loop latent diagnostic) blocker: eval's
`StudentInLoopPolicy` restored the TCN/GRU architecture fields from the student's
saved cfg but NOT `policy_obs_dim`, leaving it at StudentCfg's stale default (69).
Once `use_bias_ema_obs` bumps the env to 72, the student encoder then builds its
channel transform at 69 while the checkpoint is 72 -> `load_state_dict` raises a
shape mismatch (`channel_transform.0.weight` (32,72) vs (32,69)). FrozenTeacher
already reads its width off the checkpoint; the eval student path must do the same.

Two no-Isaac-Sim checks:
(1) Runtime: `StudentEncoderTCN` width tracks `policy_obs_dim`, and a 72D checkpoint
    only loads into a 72D-built encoder -- loaded standalone via importlib so no
    Isaac Sim import chain is triggered (`_core/student/{config,models}.py` are pure
    torch + dataclass).
(2) Source: `StudentInLoopPolicy.__init__` restores `policy_obs_dim` from the saved
    cfg and guards student/teacher obs-width agreement (the shipped fix, checked on
    the real source so a future refactor that drops it fails here).
"""
from __future__ import annotations

import importlib.util
import sys
import types
from pathlib import Path

import pytest
import torch

REPO = Path(__file__).resolve().parents[1]
STUDENT_DIR = REPO / "constrained_albc" / "envs" / "_core" / "student"


def _load_student_models():
    """Load StudentCfg + StudentEncoderTCN without importing constrained_albc.

    Mirrors test_bias_ema_obs.py: register empty parent packages, then exec the two
    pure modules by file path with __package__ set so `from .config import ...`
    resolves. Avoids constrained_albc.__init__ -> envs -> isaaclab.sim -> pxr.
    """
    for pkg in (
        "constrained_albc",
        "constrained_albc.envs",
        "constrained_albc.envs._core",
        "constrained_albc.envs._core.student",
    ):
        if pkg not in sys.modules:
            m = types.ModuleType(pkg)
            m.__path__ = []  # mark as a package so submodule specs resolve
            sys.modules[pkg] = m

    def _exec(name: str, path: Path):
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        mod.__package__ = "constrained_albc.envs._core.student"
        sys.modules[name] = mod
        spec.loader.exec_module(mod)
        return mod

    cfg_mod = _exec("constrained_albc.envs._core.student.config", STUDENT_DIR / "config.py")
    models_mod = _exec("constrained_albc.envs._core.student.models", STUDENT_DIR / "models.py")
    return cfg_mod.StudentCfg, models_mod.StudentEncoderTCN


def test_tcn_encoder_width_tracks_policy_obs_dim_and_gates_load():
    StudentCfg, StudentEncoderTCN = _load_student_models()

    def build(obs_dim: int):
        cfg = StudentCfg()
        cfg.encoder_type = "tcn"
        cfg.policy_obs_dim = obs_dim
        return StudentEncoderTCN(cfg)

    enc72 = build(72)
    assert enc72.channel_transform[0].in_features == 72
    sd72 = enc72.state_dict()

    enc69 = build(69)
    assert enc69.channel_transform[0].in_features == 69

    # The DGX crash: a 72D student checkpoint must NOT silently load into a 69D-built
    # encoder -- the stale default would have to be caught by exactly this mismatch.
    with pytest.raises(RuntimeError):
        enc69.load_state_dict(sd72)

    # The fix's effect: restore policy_obs_dim=72 -> the encoder builds at 72 and the
    # checkpoint loads cleanly.
    build(72).load_state_dict(sd72)  # must not raise


def test_student_policy_restores_obs_width_and_guards_teacher_match():
    src = (REPO / "constrained_albc" / "analysis" / "student_policy.py").read_text()
    # restore the true obs width from the student's own saved cfg (not StudentCfg's default)
    assert 'cfg.policy_obs_dim = saved_cfg["policy_obs_dim"]' in src
    # and refuse a student/teacher obs-width mismatch instead of building a broken policy
    assert "self.teacher.obs_dim" in src and "cannot be paired" in src
