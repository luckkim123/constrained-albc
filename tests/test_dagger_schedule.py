"""Sim-free unit test for the DAgger on-policy correction.

Loads student/config.py STANDALONE (by path) to avoid the constrained_albc package
__init__ -> isaaclab.sim -> pxr import chain (mirrors tests/test_student_eval_obs_width.py).
The beta schedule is exercised functionally; the runner's beta-mix is verified by source
inspection because it needs a live Isaac env + teacher to actually run.
"""
from __future__ import annotations

import importlib.util
import re
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
STUDENT = REPO / "constrained_albc" / "envs" / "_core" / "student"


def _load_config():
    spec = importlib.util.spec_from_file_location("student_config_standalone", STUDENT / "config.py")
    mod = importlib.util.module_from_spec(spec)
    # Register before exec so dataclass field resolution (dataclasses.py looks up
    # sys.modules[cls.__module__]) finds this standalone module.
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def test_default_beta_is_pure_teacher_every_iter():
    """Defaults (start=end=1.0, anneal=0) must give beta==1.0 at every iter: DAgger inert,
    the rollout is exactly the current teacher-only recipe."""
    m = _load_config()
    cfg = m.StudentCfg()
    for it in (0, 1, 100, 999, 5000):
        assert m.dagger_beta_at(cfg, it) == 1.0


def test_beta_anneals_linearly_then_holds():
    m = _load_config()
    cfg = m.StudentCfg()
    cfg.dagger_beta_start, cfg.dagger_beta_end, cfg.dagger_anneal_iters = 1.0, 0.0, 600
    assert m.dagger_beta_at(cfg, 0) == 1.0
    assert abs(m.dagger_beta_at(cfg, 300) - 0.5) < 1e-9
    assert abs(m.dagger_beta_at(cfg, 600) - 0.0) < 1e-9
    assert m.dagger_beta_at(cfg, 900) == 0.0  # held at beta_end past the anneal window


def test_zero_anneal_is_constant_beta_end():
    m = _load_config()
    cfg = m.StudentCfg()
    cfg.dagger_beta_start, cfg.dagger_beta_end, cfg.dagger_anneal_iters = 1.0, 0.0, 0
    for it in (0, 5, 999):
        assert m.dagger_beta_at(cfg, it) == 0.0


def test_runner_beta_mix_and_relabeling_unchanged():
    """The single-variable contract, checked in source: env stepped with the beta-mixed
    action (teacher-only when beta==1), student action no-grad, teacher relabeling intact."""
    src = (STUDENT / "runner.py").read_text()
    assert "use_student = beta < 1.0" in src
    assert "a_exec = self._dagger_action(obs, a_t, beta) if use_student else a_t" in src
    assert "obs_next, _rew, dones, extras = self.env.step(a_exec)" in src
    assert "beta * a_teacher + (1.0 - beta) * a_student" in src
    # student action is distribution-shaping only, must not carry gradient
    assert re.search(r"@torch\.no_grad\(\)\s*\n\s*def _dagger_action", src)
    # DAgger relabeling: buffer still records the TEACHER's l_t, a_t as the BC targets
    assert "self.buffer.add(obs, privileged, l_t.detach(), a_t.detach(), prev_dones)" in src
    # deploy parity: collection-time student runs in eval mode, restored to train after
    assert "self.student.eval()" in src
    assert "self.student.train()" in src
