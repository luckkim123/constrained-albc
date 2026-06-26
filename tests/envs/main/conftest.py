"""Pytest configuration for tests/envs/main.

Stubs the top-level constrained_albc package so that its __init__.py
(which imports albc_env -> isaaclab.sim, requiring a full Isaac Sim runtime)
is never executed. Subpackages still load from disk.

Also stubs marinelab.assets (provides ALBC arm link-length constants) and
pre-loads constrained_albc.envs.tdc.controllers.kinematics directly so that
ee_action.py can use the clean dotted import without triggering
controllers/__init__.py -> tdc.py -> isaaclab.utils (which also needs Isaac Sim).

constrained_albc.envs.main is stubbed as a namespace package so that its
__init__.py (which imports albc_env -> isaaclab.sim) is never executed while
ee_action.py still loads normally from disk.

Extended stubs for config.py / rewards.py (Task 2):
  - isaaclab.utils.configclass is stubbed as a dataclass-compatible decorator
    that handles mutable defaults (mimicking isaaclab's own behavior).
  - isaaclab.sim, isaaclab.envs, isaaclab.scene, isaaclab.terrains,
    isaaclab.utils.noise are stubbed with permissive sentinel classes.
  - marinelab.assets is extended with all symbols config.py imports.
  - constrained_albc.envs.main.doraemon and mdp.constraints are stubbed so
    config.py's relative imports do not trigger Isaac Sim.
  - rewards.py and config.py are pre-loaded via spec_from_file_location (same
    pattern as kinematics.py) so ALBCRewardCfg and ALBCEnvCfg are importable
    sim-free.
"""
import copy
import dataclasses
import importlib.util
import sys
import types
from pathlib import Path

# Repo root: this conftest lives at tests/envs/main/conftest.py
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONSTRAINED_ALBC_PKG = _REPO_ROOT / "constrained_albc"


# ---------------------------------------------------------------------------
# Permissive sentinel used to satisfy isaaclab/marinelab stub slots.
# __deepcopy__ returns self so dataclasses.field(default_factory) works.
# __call__ returns self so e.g. sim_utils.RigidBodyMaterialCfg(...) is a no-op.
# replace() mirrors the isaaclab configclass API used in ALBCEnvCfg field defs.
# ---------------------------------------------------------------------------
class _Stub:
    """Permissive stub: absorbs attribute access, calls, and deepcopy."""

    def __init__(self, *args, **kwargs):
        pass

    def __getattr__(self, key: str) -> "_Stub":
        return self

    def __call__(self, *args, **kwargs) -> "_Stub":
        return self

    def __deepcopy__(self, memo: dict) -> "_Stub":
        return self

    def replace(self, **kwargs) -> "_Stub":
        return self


_STUB = _Stub()


# ---------------------------------------------------------------------------
# configclass stub: behaves like isaaclab's configclass decorator, which wraps
# Python's dataclass but allows mutable defaults without explicit field().
# ---------------------------------------------------------------------------
def _stub_configclass(cls):
    """Minimal configclass replacement for sim-free tests.

    Converts mutable-default class attributes (other dataclasses, lists, dicts)
    into dataclasses.field(default_factory=...) so that @dataclass succeeds.
    Plain scalars and tuples are left as-is (dataclass handles them natively).
    """
    annotations: dict = {}
    for klass in reversed(cls.__mro__):
        annotations.update(getattr(klass, "__annotations__", {}))

    for name, value in list(cls.__dict__.items()):
        if name.startswith("_") or name in ("__dict__", "__weakref__"):
            continue
        if name not in annotations:
            continue
        if isinstance(value, dataclasses.Field):
            continue
        if dataclasses.is_dataclass(value) or isinstance(value, (dict, list)):
            captured = value
            setattr(cls, name, dataclasses.field(default_factory=lambda v=captured: copy.deepcopy(v)))

    return dataclasses.dataclass(cls)


# ---------------------------------------------------------------------------
# isaaclab stub modules
# ---------------------------------------------------------------------------
def _stub_isaaclab() -> None:
    """Stub isaaclab.* modules consumed by config.py at import time."""
    if "isaaclab.utils" in sys.modules:
        return  # already stubbed (e.g. by a previous conftest run)

    ilu = types.ModuleType("isaaclab")
    ilu.__path__ = []
    sys.modules.setdefault("isaaclab", ilu)

    # isaaclab.utils: only configclass is used at module level in rewards.py
    ilu_utils = types.ModuleType("isaaclab.utils")
    ilu_utils.__path__ = []
    ilu_utils.configclass = _stub_configclass
    sys.modules["isaaclab.utils"] = ilu_utils

    # isaaclab.utils.noise: real minimal dataclasses so tests can call len() on
    # noise_cfg.std / bias_noise_cfg.n_min / bias_noise_cfg.n_max.
    @dataclasses.dataclass
    class _GaussianNoiseCfg:
        mean: float = 0.0
        std: tuple = ()

    @dataclasses.dataclass
    class _UniformNoiseCfg:
        n_min: tuple = ()
        n_max: tuple = ()

    @dataclasses.dataclass
    class _NoiseModelWithAdditiveBiasCfg:
        noise_cfg: object = dataclasses.field(default_factory=_GaussianNoiseCfg)
        bias_noise_cfg: object = dataclasses.field(default_factory=_UniformNoiseCfg)

    ilu_noise = types.ModuleType("isaaclab.utils.noise")
    ilu_noise.__path__ = []
    ilu_noise.GaussianNoiseCfg = _GaussianNoiseCfg
    ilu_noise.NoiseModelWithAdditiveBiasCfg = _NoiseModelWithAdditiveBiasCfg
    ilu_noise.UniformNoiseCfg = _UniformNoiseCfg
    sys.modules["isaaclab.utils.noise"] = ilu_noise

    # isaaclab.sim: accessed as `sim_utils.X(...)` so needs auto-attr via _Stub
    class _AutoSim(types.ModuleType):
        PhysxCfg = _Stub
        SimulationCfg = _Stub

        def __getattr__(self, key: str):
            return _Stub

    ilu_sim = _AutoSim("isaaclab.sim")
    ilu_sim.__path__ = []
    sys.modules["isaaclab.sim"] = ilu_sim

    # isaaclab.envs: DirectRLEnvCfg is the base class of ALBCEnvCfg
    ilu_envs = types.ModuleType("isaaclab.envs")
    ilu_envs.__path__ = []
    ilu_envs.DirectRLEnvCfg = object  # must be a real class for inheritance
    ilu_envs.ViewerCfg = _Stub
    sys.modules["isaaclab.envs"] = ilu_envs

    # isaaclab.scene / isaaclab.terrains
    for mod_name, attrs in (
        ("isaaclab.scene", {"InteractiveSceneCfg": _Stub}),
        ("isaaclab.terrains", {"TerrainImporterCfg": _Stub}),
    ):
        mo = types.ModuleType(mod_name)
        mo.__path__ = []
        for k, v in attrs.items():
            setattr(mo, k, v)
        sys.modules[mod_name] = mo


# ---------------------------------------------------------------------------
# Extended marinelab.assets stubs (config.py needs more than kinematics.py did)
# ---------------------------------------------------------------------------
def _extend_marinelab_assets() -> None:
    """Add the extra symbols config.py imports from marinelab.assets."""
    maa = sys.modules.get("marinelab.assets")
    if maa is None:
        return
    # These are base classes or cfg objects; _Stub satisfies both roles.
    # ALBC_CFG is used as ALBC_CFG.replace(...) so needs the instance (_STUB).
    # The *Cfg class names are used as base classes so need the class (_Stub).
    _class_syms = {
        "ALBCBuoyHydrodynamicsCfg",
        "ALBCHydrodynamicsCfg",
        "HydrodynamicsCfg",
        "OceanCurrentCfg",
        "ThrusterCfg",
    }
    for sym in (
        "ALBC_CFG",
        "ALBCBuoyHydrodynamicsCfg",
        "ALBCHydrodynamicsCfg",
        "HydrodynamicsCfg",
        "OceanCurrentCfg",
        "ThrusterCfg",
        "ALBC_JOINT_NAMES",
    ):
        if not hasattr(maa, sym):
            if sym == "ALBC_JOINT_NAMES":
                setattr(maa, sym, [])
            elif sym in _class_syms:
                setattr(maa, sym, _Stub)  # class — used as base class in config.py
            else:
                setattr(maa, sym, _STUB)  # instance — used as ALBC_CFG.replace(...)


# ---------------------------------------------------------------------------
# Stub doraemon and mdp.constraints so config.py's relative imports resolve
# ---------------------------------------------------------------------------
def _stub_config_deps() -> None:
    """Stub constrained_albc.envs.main.doraemon and mdp.constraints."""
    # doraemon: config.py does `from .doraemon import DoraemonCfg`
    dm_dotted = "constrained_albc.envs.main.doraemon"
    if dm_dotted not in sys.modules:
        dm_mod = types.ModuleType(dm_dotted)
        dm_mod.DoraemonCfg = _Stub
        sys.modules[dm_dotted] = dm_mod

    # mdp namespace
    mdp_dotted = "constrained_albc.envs.main.mdp"
    if mdp_dotted not in sys.modules:
        mdp_mod = types.ModuleType(mdp_dotted)
        mdp_mod.__path__ = [str(_CONSTRAINED_ALBC_PKG / "envs" / "main" / "mdp")]
        mdp_mod.__package__ = mdp_dotted
        sys.modules[mdp_dotted] = mdp_mod

    # constraints: config.py does `from .mdp.constraints import ALBCConstraintCfg, ...`
    constraints_dotted = "constrained_albc.envs.main.mdp.constraints"
    if constraints_dotted not in sys.modules:
        cmod = types.ModuleType(constraints_dotted)
        for sym in (
            "ALBCConstraintCfg",
            "ConstraintTermCfg",
            "attitude_limit_cost",
            "cumulative_yaw_cost",
            "joint1_position_cost",
            "manipulability_cost",
            "rp_rate_cost",
            "rp_vel_settling_cost",
            "thruster_utilization_cost",
            "torque_limit_cost",
            "velocity_limit_cost",
            "yaw_rate_cost",
        ):
            setattr(cmod, sym, _Stub)
        sys.modules[constraints_dotted] = cmod


# ---------------------------------------------------------------------------
# Pre-load rewards.py and config.py (same pattern as kinematics.py)
# ---------------------------------------------------------------------------
def _preload_rewards() -> None:
    """Load mdp/rewards.py directly, bypassing mdp/__init__.py."""
    dotted = "constrained_albc.envs.main.mdp.rewards"
    if dotted in sys.modules:
        return
    mdp_dotted = "constrained_albc.envs.main.mdp"
    rewards_path = _CONSTRAINED_ALBC_PKG / "envs" / "main" / "mdp" / "rewards.py"
    spec = importlib.util.spec_from_file_location(dotted, rewards_path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = mdp_dotted
    sys.modules[dotted] = mod  # register before exec so __module__ resolves
    spec.loader.exec_module(mod)
    # Attach to parent so `from constrained_albc.envs.main.mdp.rewards import` works
    mdp_mod = sys.modules.get(mdp_dotted)
    if mdp_mod is not None:
        mdp_mod.rewards = mod


def _preload_config() -> None:
    """Load envs/main/config.py directly, bypassing envs/main/__init__.py."""
    dotted = "constrained_albc.envs.main.config"
    if dotted in sys.modules:
        return
    config_path = _CONSTRAINED_ALBC_PKG / "envs" / "main" / "config.py"
    spec = importlib.util.spec_from_file_location(dotted, config_path)
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "constrained_albc.envs.main"
    sys.modules[dotted] = mod  # register before exec so relative imports resolve
    spec.loader.exec_module(mod)


def _stub_constrained_albc() -> None:
    """Register a namespace-package stub for constrained_albc.

    Mirrors the mechanism in tests/deploy/conftest.py: the real __init__.py
    is never executed, but all subpackages and modules load normally from disk
    because __path__ points at the package directory.
    """
    if "constrained_albc" in sys.modules:
        return  # real runtime already loaded it; leave it alone
    m = types.ModuleType("constrained_albc")
    m.__path__ = [str(_CONSTRAINED_ALBC_PKG)]
    m.__package__ = "constrained_albc"
    sys.modules["constrained_albc"] = m


def _stub_marinelab_assets() -> None:
    """Stub marinelab.assets with the two ALBC link-length constants.

    marinelab/__init__.py pulls in isaaclab.sim (needs pxr / Isaac Sim).
    kinematics.py only uses ALBC_LINK1_LENGTH and ALBC_LINK2_LENGTH, so a
    minimal stub is sufficient.
    """
    if "marinelab" not in sys.modules:
        ma = types.ModuleType("marinelab")
        ma.__path__ = []
        sys.modules["marinelab"] = ma
    if "marinelab.assets" not in sys.modules:
        maa = types.ModuleType("marinelab.assets")
        maa.ALBC_LINK1_LENGTH = 0.233
        maa.ALBC_LINK2_LENGTH = 0.233
        sys.modules["marinelab.assets"] = maa


def _preload_kinematics() -> None:
    """Load kinematics.py directly and register it under its dotted module name.

    controllers/__init__.py re-exports tdc.py and thruster_pd.py, both of which
    import isaaclab.utils (needs pxr). Loading kinematics.py via
    spec_from_file_location and registering it directly bypasses that chain while
    keeping the import in ee_action.py clean:
        from constrained_albc.envs.tdc.controllers.kinematics import ALBCKinematics
    """
    dotted = "constrained_albc.envs.tdc.controllers.kinematics"
    if dotted in sys.modules:
        return

    # Register intermediate namespace packages so the dotted lookup resolves.
    for pkg in (
        "constrained_albc.envs",
        "constrained_albc.envs.tdc",
        "constrained_albc.envs.tdc.controllers",
    ):
        if pkg not in sys.modules:
            p = types.ModuleType(pkg)
            p.__path__ = []
            sys.modules[pkg] = p

    kin_path = _CONSTRAINED_ALBC_PKG / "envs" / "tdc" / "controllers" / "kinematics.py"
    spec = importlib.util.spec_from_file_location(dotted, kin_path)
    kin_mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(kin_mod)
    sys.modules[dotted] = kin_mod


def _stub_envs_main() -> None:
    """Stub constrained_albc.envs.main as a namespace package.

    constrained_albc/envs/main/__init__.py imports albc_env -> isaaclab.sim,
    which requires Isaac Sim. Registering a namespace stub with __path__ pointing
    at the directory lets ee_action.py load from disk without running __init__.py.
    """
    pkg = "constrained_albc.envs.main"
    if pkg in sys.modules:
        return
    main_mod = types.ModuleType(pkg)
    main_mod.__path__ = [str(_CONSTRAINED_ALBC_PKG / "envs" / "main")]
    main_mod.__package__ = pkg
    sys.modules[pkg] = main_mod


# Run all stubs at collection time (before any test module is imported).
# Order matters: base stubs first, then extended stubs, then preloads.
_stub_constrained_albc()
_stub_marinelab_assets()
_preload_kinematics()
_stub_envs_main()
# Task-2 additions: enable sim-free import of config.py and rewards.py
_stub_isaaclab()
_extend_marinelab_assets()
_stub_config_deps()
_preload_rewards()
_preload_config()
