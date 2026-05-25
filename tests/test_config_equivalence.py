# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Config equivalence regression net for the de-duplication refactor.

The FullDOF runner cfgs duplicate shared constants (seed, num_steps_per_env,
max_iterations, save_interval) and the constraint runners' obs_groups dict. The
de-dup refactor moves these into a base class; this test pins the values so the
refactor cannot silently change any of them. It passes before the refactor (the
values are the frozen golden) and must keep passing after.

Isaac-Sim-free: the cfg module imports isaaclab / isaaclab_rl / rsl_rl and three
sibling env modules at import time, all of which pull in Isaac Sim. We stub them
so the cfg classes load standalone, then load the module by path (avoiding the
constrained_albc package __init__, which registers Gym envs and needs Isaac Sim).
"""

import importlib.util
import sys
import types

import pytest


def _install_stubs() -> None:
    """Register minimal stand-ins for the cfg module's heavy import-time deps."""

    def stub(name: str, **attrs) -> types.ModuleType:
        mod = types.ModuleType(name)
        for key, value in attrs.items():
            setattr(mod, key, value)
        sys.modules[name] = mod
        return mod

    # isaaclab.utils.configclass: identity decorator (it wraps a dataclass).
    isaaclab = stub("isaaclab")
    isaaclab.utils = stub("isaaclab.utils", configclass=lambda cls: cls)

    # rsl_rl.runners.on_policy_runner: side-effect registration target.
    rsl_rl = stub("rsl_rl")
    rsl_rl.runners = stub("rsl_rl.runners")
    rsl_rl.runners.on_policy_runner = stub("rsl_rl.runners.on_policy_runner")

    # isaaclab_rl.rsl_rl base cfgs: minimal classes with a to_dict() reading attrs.
    class _BaseCfg:
        def to_dict(self) -> dict:
            out = {}
            for key in dir(self):
                if key.startswith("_"):
                    continue
                value = getattr(self, key)
                if callable(value):
                    continue
                out[key] = value
            return out

    isaaclab_rl = stub("isaaclab_rl")
    isaaclab_rl.rsl_rl = stub(
        "isaaclab_rl.rsl_rl",
        RslRlOnPolicyRunnerCfg=_BaseCfg,
        RslRlPpoActorCriticCfg=_BaseCfg,
        RslRlPpoAlgorithmCfg=_BaseCfg,
    )

    # Sibling relative imports (..algorithms / ..encoder / ..runners): the cfg
    # module only registers these symbols on the runner module; it does not call
    # them at class-definition time, so empty placeholders suffice.
    pkg = "constrained_albc.envs.constrained_full_albc"
    for name in ["constrained_albc", "constrained_albc.envs", pkg,
                 f"{pkg}.algorithms", f"{pkg}.encoder", f"{pkg}.runners"]:
        if name not in sys.modules:
            stub(name)
    sys.modules[f"{pkg}.algorithms"].ConstraintTRPO = type("ConstraintTRPO", (), {})
    sys.modules[f"{pkg}.encoder"].ActorCriticAsymConstrained = type("ActorCriticAsymConstrained", (), {})
    sys.modules[f"{pkg}.encoder"].ActorCriticEncoder = type("ActorCriticEncoder", (), {})
    sys.modules[f"{pkg}.runners"].ConstraintEncoderRunner = type("ConstraintEncoderRunner", (), {})


def _load_by_path(name: str, path: str):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _load_cfg_modules():
    _install_stubs()
    pkg = "constrained_albc.envs.constrained_full_albc"
    base = "constrained_albc/envs/constrained_full_albc/agents"
    main = _load_by_path(f"{pkg}.agents.rsl_rl_ppo_cfg", f"{base}/rsl_rl_ppo_cfg.py")
    ablation = _load_by_path(f"{pkg}.agents.ablation_cfgs", f"{base}/ablation_cfgs.py")
    return main, ablation


_MAIN, _ABLATION = _load_cfg_modules()

# Frozen golden per runner (captured pre-refactor). seed/steps/iters are uniform;
# save_interval differs intentionally for the PPO-Enc ablation (100), which must
# survive the de-dup as an explicit override.
_GOLDEN = {
    "FullDOFTRPORunnerCfg": (_MAIN, {"seed": 30, "num_steps_per_env": 64, "max_iterations": 2500, "save_interval": 50}),
    "FullDOFNoEncoderRunnerCfg": (_MAIN, {"seed": 30, "num_steps_per_env": 64, "max_iterations": 2500, "save_interval": 50}),
    "FullDOFPPORunnerCfg": (_MAIN, {"seed": 30, "num_steps_per_env": 64, "max_iterations": 2500, "save_interval": 50}),
    "FullDOFTRPONoIPORunnerCfg": (_ABLATION, {"seed": 30, "num_steps_per_env": 64, "max_iterations": 2500, "save_interval": 50}),
    "FullDOFPPOEncRunnerCfg": (_ABLATION, {"seed": 30, "num_steps_per_env": 64, "max_iterations": 2500, "save_interval": 100}),
}

_OBS_GROUPS = {"policy": ["policy", "privileged"], "critic": ["policy", "privileged"]}
_CONSTRAINT_RUNNERS = ["FullDOFTRPORunnerCfg", "FullDOFNoEncoderRunnerCfg"]


@pytest.mark.parametrize("cls_name", list(_GOLDEN))
def test_runner_cfg_constants(cls_name):
    module, golden = _GOLDEN[cls_name]
    cfg = getattr(module, cls_name)()
    for field, expected in golden.items():
        assert getattr(cfg, field) == expected, f"{cls_name}.{field} = {getattr(cfg, field)} != {expected}"


@pytest.mark.parametrize("cls_name", _CONSTRAINT_RUNNERS)
def test_constraint_runner_obs_groups(cls_name):
    cfg = getattr(_MAIN, cls_name)()
    assert cfg.obs_groups == _OBS_GROUPS, f"{cls_name}.obs_groups changed: {cfg.obs_groups}"
