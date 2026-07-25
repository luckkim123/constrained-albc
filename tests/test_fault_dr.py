# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Tests for the FaultDR-AB code delta (next-20260725-175508).

Four independent, no-Isaac-Sim checks:

(A) faults.sample_thruster_health's new ``severity`` kwarg (the DORAEMON
    fault-severity curriculum): u=0 -> byte-identical all-healthy regardless of
    thruster_fail_prob; u=1 -> statistically matches the base Bernoulli rate;
    severity=None (every pre-existing caller) is untouched.

(B) doraemon.py registers "fault_severity" in _PARAM_DEFS with nominal 0
    (mirrors test_doraemon.py's build_param_specs check for the other two
    DORAEMON-managed [0,1] knobs, ocean_current_strength / obs_noise_scale).

(C) config.apply_privileged_fault_obs: the Arm-B state_space materializer,
    AST-extracted + exec'd (mirrors test_bias_ema_obs.py's apply_bias_ema_obs
    check) to avoid config.py's heavy isaaclab.sim/marinelab top-of-file imports.

(D) The runners' new sync_privileged_dim auto-sync (mirrors test_bias_ema_obs.py's
    policy_obs_dim runner check): privileged_dim follows env.cfg.state_space.

Run headless: python3 -m pytest tests/test_fault_dr.py
"""
from __future__ import annotations

import ast
import importlib.util
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest
import torch

# ---------------------------------------------------------------------------
# (A) faults.sample_thruster_health severity kwarg
# ---------------------------------------------------------------------------

_MDP = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "constrained_albc",
    "envs",
    "main",
    "mdp",
)
if _MDP not in sys.path:
    sys.path.insert(0, _MDP)
import faults  # noqa: E402


class _FaultCfg:
    """Minimal stand-in for FaultInjectionCfg (avoids importing isaaclab configclass)."""

    thruster_fail_prob = 0.5
    thruster_health_range = (0.0, 0.5)
    thruster_fixed_health = None


def test_severity_zero_is_all_healthy_regardless_of_fail_prob():
    """u=0 -> effective_prob=0 for every env/thruster -> all ones, byte-identical,
    even at fail_prob=1.0 (the DORAEMON curriculum-off starting point)."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 1.0
    severity = torch.zeros(64)
    h = faults.sample_thruster_health(64, 6, cfg, device="cpu", severity=severity)
    assert torch.equal(h, torch.ones(64, 6))


def test_severity_one_matches_base_bernoulli_statistically():
    """u=1 -> effective_prob == cfg.thruster_fail_prob, so the failed fraction over
    a large sample matches the un-scaled Bernoulli rate within tolerance."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 0.3
    severity = torch.ones(4096)
    gen = torch.Generator().manual_seed(0)
    h = faults.sample_thruster_health(4096, 6, cfg, device="cpu", generator=gen, severity=severity)
    failed_frac = (h != 1.0).float().mean().item()
    assert abs(failed_frac - 0.3) < 0.02


def test_severity_none_default_matches_legacy_bernoulli_byte_identical():
    """severity=None (every pre-existing caller) reproduces the un-scaled path
    exactly -- same seed, same draws, no behavior change for old call sites."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 0.4
    h_legacy = faults.sample_thruster_health(
        32, 6, cfg, device="cpu", generator=torch.Generator().manual_seed(5)
    )
    h_default = faults.sample_thruster_health(
        32, 6, cfg, device="cpu", generator=torch.Generator().manual_seed(5), severity=None
    )
    assert torch.equal(h_legacy, h_default)


def test_severity_intermediate_scales_effective_prob():
    """u=0.5 halves the effective fail probability relative to u=1."""
    cfg = _FaultCfg()
    cfg.thruster_fail_prob = 0.6
    gen = torch.Generator().manual_seed(1)
    h = faults.sample_thruster_health(4096, 6, cfg, device="cpu", generator=gen, severity=torch.full((4096,), 0.5))
    failed_frac = (h != 1.0).float().mean().item()
    assert abs(failed_frac - 0.3) < 0.02


def test_fixed_health_override_ignores_severity():
    """The deterministic eval instrument (thruster_fixed_health) is checked BEFORE
    severity is consulted -- severity must not perturb it either way."""
    cfg = _FaultCfg()
    cfg.thruster_fixed_health = (1.0, 1.0, 1.0, 1.0, 0.0, 1.0)
    h = faults.sample_thruster_health(16, 6, cfg, device="cpu", severity=torch.zeros(16))
    expected = torch.tensor([1.0, 1.0, 1.0, 1.0, 0.0, 1.0]).unsqueeze(0).expand(16, 6)
    assert torch.equal(h, expected)


# ---------------------------------------------------------------------------
# (B) doraemon.py: fault_severity registered with nominal 0
# ---------------------------------------------------------------------------

_DORAEMON_PATH = (
    Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "doraemon.py"
)


def _load_doraemon_standalone():
    if "isaaclab" not in sys.modules:
        _isaaclab = types.ModuleType("isaaclab")
        _utils = types.ModuleType("isaaclab.utils")
        _utils.configclass = lambda cls: cls
        _isaaclab.utils = _utils
        sys.modules["isaaclab"] = _isaaclab
        sys.modules["isaaclab.utils"] = _utils

    _marinelab_root = Path("/workspace/marinelab/marinelab")
    if "marinelab" not in sys.modules:
        _marinelab = types.ModuleType("marinelab")
        _marinelab.__path__ = [str(_marinelab_root)]
        sys.modules["marinelab"] = _marinelab
        _ml_algorithms = types.ModuleType("marinelab.algorithms")
        _ml_algorithms.__path__ = [str(_marinelab_root / "algorithms")]
        sys.modules["marinelab.algorithms"] = _ml_algorithms

    spec = importlib.util.spec_from_file_location("fault_dr_doraemon", _DORAEMON_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_fault_severity_registered_in_param_defs_with_nominal_zero():
    doraemon = _load_doraemon_standalone()
    names = [name for name, _field, _lo, _hi in doraemon._PARAM_DEFS]
    assert "fault_severity" in names
    field_by_name = {name: field for name, field, _lo, _hi in doraemon._PARAM_DEFS}
    assert field_by_name["fault_severity"] == "fault_severity_range"
    assert doraemon._NOMINAL_OVERRIDES["fault_severity"] == 0.0


def test_fault_severity_specs_start_at_zero_nominal_via_build_param_specs():
    doraemon = _load_doraemon_standalone()

    class _FakeDRCfg:
        fault_severity_range = (0.0, 1.0)

        def __getattr__(self, name):  # any other _PARAM_DEFS field defaults to (0, 1)
            return (0.0, 1.0)

    specs = doraemon.build_param_specs(_FakeDRCfg(), doraemon._PARAM_DEFS, doraemon._NOMINAL_OVERRIDES)
    by_name = {s.name: s for s in specs}
    assert by_name["fault_severity"].min_bound == 0.0
    assert by_name["fault_severity"].max_bound == 1.0
    assert by_name["fault_severity"].nominal == pytest.approx(0.0)


# ---------------------------------------------------------------------------
# (C) config.apply_privileged_fault_obs materializer
# ---------------------------------------------------------------------------

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "config.py"
)


def _load_apply_privileged_fault_obs():
    tree = ast.parse(_CONFIG_PATH.read_text())
    func_node = next(
        n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == "apply_privileged_fault_obs"
    )
    namespace: dict = {}
    exec(compile(ast.unparse(func_node), "<apply_privileged_fault_obs>", "exec"), namespace)
    return namespace["apply_privileged_fault_obs"]


def test_arm_a_default_off_leaves_state_space_at_28():
    apply_privileged_fault_obs = _load_apply_privileged_fault_obs()
    cfg = SimpleNamespace(use_privileged_fault_obs=False, state_space=28)
    apply_privileged_fault_obs(cfg)
    assert cfg.state_space == 28


def test_arm_b_on_bumps_state_space_28_to_34():
    apply_privileged_fault_obs = _load_apply_privileged_fault_obs()
    cfg = SimpleNamespace(use_privileged_fault_obs=True, state_space=28)
    apply_privileged_fault_obs(cfg)
    assert cfg.state_space == 34


# ---------------------------------------------------------------------------
# (D) runners.sync_privileged_dim auto-sync
# ---------------------------------------------------------------------------


def _load_runners_init_standalone():
    core_dir = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "_core"
    runners_pkg = "constrained_albc.envs._core.runners"
    for pkg_name in ["constrained_albc", "constrained_albc.envs", "constrained_albc.envs._core"]:
        if pkg_name not in sys.modules:
            sys.modules[pkg_name] = types.ModuleType(pkg_name)
    if not hasattr(sys.modules.get(runners_pkg), "sync_privileged_dim"):
        spec = importlib.util.spec_from_file_location(runners_pkg, core_dir / "runners" / "__init__.py")
        module = importlib.util.module_from_spec(spec)
        sys.modules[runners_pkg] = module
        spec.loader.exec_module(module)
    return sys.modules[runners_pkg]


def test_sync_privileged_dim_follows_state_space_on_mismatch():
    runners = _load_runners_init_standalone()
    env = SimpleNamespace(unwrapped=SimpleNamespace(cfg=SimpleNamespace(state_space=34)))
    train_cfg = {"policy": {"privileged_dim": 28}}
    runners.sync_privileged_dim(env, train_cfg)
    assert train_cfg["policy"]["privileged_dim"] == 34


def test_sync_privileged_dim_leaves_matching_value_untouched():
    runners = _load_runners_init_standalone()
    env = SimpleNamespace(unwrapped=SimpleNamespace(cfg=SimpleNamespace(state_space=28)))
    train_cfg = {"policy": {"privileged_dim": 28}}
    runners.sync_privileged_dim(env, train_cfg)
    assert train_cfg["policy"]["privileged_dim"] == 28


def test_sync_privileged_dim_does_not_invent_key_when_absent():
    runners = _load_runners_init_standalone()
    env = SimpleNamespace(unwrapped=SimpleNamespace(cfg=SimpleNamespace(state_space=34)))
    train_cfg = {"policy": {"class_name": "ActorCritic"}}
    runners.sync_privileged_dim(env, train_cfg)
    assert "privileged_dim" not in train_cfg["policy"]
