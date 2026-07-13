# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Sim-free checks for the bias-ema-obs experiment toggle (use_bias_ema_obs).

Three independent, no-Isaac-Sim checks:

(1) Static config contract (AST, mirrors test_attitude_only_dims.py): the toggle
    defaults to False and observation_space stays 69 -- the off-state is byte-
    identical to today by construction, not by a runtime property this file can
    cheaply exercise (that would require booting the full env; see NOTE below).

(2) The real apply_bias_ema_obs() function body, extracted via ast.unparse() from
    config.py and exec'd in an isolated namespace (zero imports needed -- the
    function only does attribute/tuple arithmetic). This runs the ACTUAL shipped
    source, not a hand copy, while avoiding config.py's own heavy top-of-file
    imports (isaaclab.sim, marinelab.assets, doraemon, mdp.constraints/.rewards --
    loading config.py directly needs a full isaaclab.utils.configclass emulation
    that correctly handles the module's bare-mutable-default ConstraintTermCfg(...)
    kwargs instantiations at import time; the repo's own test_tdc_controller.py
    hits the same wall and replicates TDCControllerCfg instead of loading config.py).

(3) The real ConstraintEncoderRunner.__init__ policy_obs_dim auto-sync, loaded
    standalone via importlib (bypasses constrained_albc.__init__'s isaaclab chain --
    the runner's own imports are json/logging/os/torch/rsl_rl/..utils.logging, none
    of which need Isaac Sim). Needs rsl_rl importable; skips cleanly otherwise
    (system python3 in this dev container lacks it -- run under
    /isaac-sim/python.sh, which has rsl_rl without needing pxr).

NOTE: a runtime, byte-identical-off _get_observations() test would require
instantiating a real ALBCEnv (Isaac Sim GPU boot), which is exactly the heavy
scaffolding this suite's no-Isaac-Sim tests are designed to avoid. Skipped; the
static + extracted-function checks above cover the off-state contract instead.
"""

from __future__ import annotations

import ast
import importlib.util
import sys
import types
from pathlib import Path
from types import SimpleNamespace

import pytest

_CONFIG_PATH = (
    Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "main" / "config.py"
)


def _config_ast() -> ast.Module:
    return ast.parse(_CONFIG_PATH.read_text())


# ---------------------------------------------------------------------------
# (1) Static config contract
# ---------------------------------------------------------------------------


def test_default_toggle_off_and_obs_space_unchanged():
    """use_bias_ema_obs defaults to False; observation_space is still 69 (byte-identical)."""
    assigns = {}
    for node in ast.walk(_config_ast()):
        if isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            if isinstance(node.value, ast.Constant):
                assigns[node.target.id] = node.value.value
    assert assigns.get("use_bias_ema_obs") is False
    assert assigns.get("observation_space") == 69


# ---------------------------------------------------------------------------
# (2) apply_bias_ema_obs(): extracted + exec'd, exercised against fake cfgs
# ---------------------------------------------------------------------------


def _load_apply_bias_ema_obs():
    """Extract apply_bias_ema_obs's source via AST and exec it standalone.

    The function body has zero external references (only builtins: tuple,
    ValueError, attribute access on the passed-in cfg), so this needs no mocking.
    """
    tree = _config_ast()
    func_node = next(
        n
        for n in ast.walk(tree)
        if isinstance(n, ast.FunctionDef) and n.name == "apply_bias_ema_obs"
    )
    namespace: dict = {}
    exec(compile(ast.unparse(func_node), "<apply_bias_ema_obs>", "exec"), namespace)
    return namespace["apply_bias_ema_obs"]


def _make_fake_cfg(*, use_bias_ema_obs: bool, observation_space: int, k_bias: float):
    return SimpleNamespace(
        use_bias_ema_obs=use_bias_ema_obs,
        observation_space=observation_space,
        reward=SimpleNamespace(k_bias=k_bias),
        observation_noise_model=SimpleNamespace(
            noise_cfg=SimpleNamespace(std=tuple(0.01 for _ in range(69))),
            bias_noise_cfg=SimpleNamespace(
                n_min=tuple(-0.01 for _ in range(69)),
                n_max=tuple(0.01 for _ in range(69)),
            ),
        ),
    )


def test_materializer_off_is_noop():
    apply_bias_ema_obs = _load_apply_bias_ema_obs()
    cfg = _make_fake_cfg(use_bias_ema_obs=False, observation_space=69, k_bias=-2.0)
    apply_bias_ema_obs(cfg)
    assert cfg.observation_space == 69
    assert len(cfg.observation_noise_model.noise_cfg.std) == 69


def test_materializer_on_bumps_dims_and_extends_vectors_with_zeros():
    apply_bias_ema_obs = _load_apply_bias_ema_obs()
    cfg = _make_fake_cfg(use_bias_ema_obs=True, observation_space=69, k_bias=-2.0)
    apply_bias_ema_obs(cfg)
    assert cfg.observation_space == 72
    std = cfg.observation_noise_model.noise_cfg.std
    n_min = cfg.observation_noise_model.bias_noise_cfg.n_min
    n_max = cfg.observation_noise_model.bias_noise_cfg.n_max
    assert len(std) == len(n_min) == len(n_max) == 72
    assert std[-3:] == (0.0, 0.0, 0.0)
    assert n_min[-3:] == (0.0, 0.0, 0.0)
    assert n_max[-3:] == (0.0, 0.0, 0.0)


def test_materializer_bumps_space_when_noise_model_none_eval_path():
    # Regression: eval nulls observation_noise_model, but the 72D policy still needs the +3
    # space bump. The materializer must bump the space and skip the tuple extension (no model
    # to extend) instead of AttributeError-ing on None.noise_cfg. The DR/fault base_std is
    # reconstructed at 72D in ALBCEnv._obs_noise_base_std.
    apply_bias_ema_obs = _load_apply_bias_ema_obs()
    cfg = _make_fake_cfg(use_bias_ema_obs=True, observation_space=69, k_bias=-2.0)
    cfg.observation_noise_model = None
    apply_bias_ema_obs(cfg)
    assert cfg.observation_space == 72
    assert cfg.observation_noise_model is None


def test_materializer_raises_when_k_bias_zero():
    apply_bias_ema_obs = _load_apply_bias_ema_obs()
    cfg = _make_fake_cfg(use_bias_ema_obs=True, observation_space=69, k_bias=0.0)
    with pytest.raises(ValueError, match="k_bias"):
        apply_bias_ema_obs(cfg)


def test_materializer_raises_on_double_apply():
    apply_bias_ema_obs = _load_apply_bias_ema_obs()
    cfg = _make_fake_cfg(use_bias_ema_obs=True, observation_space=72, k_bias=-2.0)
    with pytest.raises(ValueError, match="observation_space"):
        apply_bias_ema_obs(cfg)


# ---------------------------------------------------------------------------
# (3) ConstraintEncoderRunner policy_obs_dim auto-sync
# ---------------------------------------------------------------------------


def _load_runner_standalone():
    pytest.importorskip("rsl_rl", reason="ConstraintEncoderRunner needs rsl_rl (not installed here)")
    core_dir = Path(__file__).resolve().parent.parent / "constrained_albc" / "envs" / "_core"

    for pkg_name in [
        "constrained_albc",
        "constrained_albc.envs",
        "constrained_albc.envs._core",
        "constrained_albc.envs._core.runners",
        "constrained_albc.envs._core.utils",
    ]:
        if pkg_name not in sys.modules:
            sys.modules[pkg_name] = types.ModuleType(pkg_name)

    logging_spec = importlib.util.spec_from_file_location(
        "constrained_albc.envs._core.utils.logging", core_dir / "utils" / "logging.py"
    )
    logging_mod = importlib.util.module_from_spec(logging_spec)
    sys.modules[logging_spec.name] = logging_mod
    logging_spec.loader.exec_module(logging_mod)

    runner_spec = importlib.util.spec_from_file_location(
        "constrained_albc.envs._core.runners.constraint_encoder_runner",
        core_dir / "runners" / "constraint_encoder_runner.py",
    )
    runner_mod = importlib.util.module_from_spec(runner_spec)
    runner_mod.__package__ = "constrained_albc.envs._core.runners"
    sys.modules[runner_spec.name] = runner_mod
    runner_spec.loader.exec_module(runner_mod)
    return runner_mod


def _patch_super_init(monkeypatch, OnPolicyRunner):
    def _fake_init(self, env, train_cfg, log_dir=None, device="cpu"):
        self.alg = SimpleNamespace(policy=SimpleNamespace())

    monkeypatch.setattr(OnPolicyRunner, "__init__", _fake_init)


def test_runner_auto_syncs_policy_obs_dim_on_mismatch(monkeypatch):
    """use_bias_ema_obs bumps env.cfg.observation_space to 72; the runner must
    follow, or the actor/critic networks silently build at the wrong (stale 69)
    input width instead of failing loud."""
    runner_mod = _load_runner_standalone()
    _patch_super_init(monkeypatch, runner_mod.OnPolicyRunner)

    env = SimpleNamespace(unwrapped=SimpleNamespace(cfg=SimpleNamespace(observation_space=72)))
    train_cfg = {"algorithm": {}, "policy": {"policy_obs_dim": 69}}

    runner_mod.ConstraintEncoderRunner(env, train_cfg, log_dir=None, device="cpu")

    assert train_cfg["policy"]["policy_obs_dim"] == 72


def test_runner_leaves_policy_obs_dim_when_already_matching(monkeypatch):
    runner_mod = _load_runner_standalone()
    _patch_super_init(monkeypatch, runner_mod.OnPolicyRunner)

    env = SimpleNamespace(unwrapped=SimpleNamespace(cfg=SimpleNamespace(observation_space=69)))
    train_cfg = {"algorithm": {}, "policy": {"policy_obs_dim": 69}}

    runner_mod.ConstraintEncoderRunner(env, train_cfg, log_dir=None, device="cpu")

    assert train_cfg["policy"]["policy_obs_dim"] == 69
