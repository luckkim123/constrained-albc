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
"""
import importlib.util
import sys
import types
from pathlib import Path

# Repo root: this conftest lives at tests/envs/main/conftest.py
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONSTRAINED_ALBC_PKG = _REPO_ROOT / "constrained_albc"


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
_stub_constrained_albc()
_stub_marinelab_assets()
_preload_kinematics()
_stub_envs_main()
