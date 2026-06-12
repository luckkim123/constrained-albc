"""Isolate deploy from the training package's heavy import side effects.

Why this exists
---------------
`import constrained_albc` runs the package ``__init__`` whose ``from .envs import
main`` registers the gym tasks -- correct for training, but it cascades into
``albc_env -> isaaclab.sim -> pxr``. On an export host without the Isaac Sim USD
runtime ``pxr`` is absent, so the import dies before any checkpoint is touched.

The student/teacher *build* code is sim-free (torch + stock rsl_rl only). The
three import roots that drag in the sim stack are:

1. ``constrained_albc``            -- top-level ``__init__`` (gym register)
2. ``constrained_albc.envs.main``  -- ``from .albc_env import ALBCEnv``
3. ``isaaclab.utils``              -- ``from .mesh import *`` -> ``pxr``

``_isolate_training_imports`` pre-injects lightweight package stubs for these
three so Python skips the real ``__init__`` files and the deep submodules
(``...student.models``, ``...encoder``) load against the unmodified source on
disk. Training code is never edited; this only changes *import resolution* at
export time.

Bootstrapping note: the very first stub (``constrained_albc``) must be injected
*before* ``import constrained_albc`` ever runs, otherwise the real ``__init__``
fires first. Entry points (the repo-root launcher, the test conftest) call
``bootstrap_constrained_albc_stub`` before importing anything under the package;
``_isolate_training_imports`` then adds the remaining two stubs and is safe to
call repeatedly.
"""
from __future__ import annotations

import pathlib
import sys
import types

# Package dir = .../constrained-albc/constrained_albc
_PKG_DIR = pathlib.Path(__file__).resolve().parent.parent


def _stub_package(name: str, package_subpath: str) -> None:
    """Inject a namespace-style stub module that keeps __path__ pointing at the
    real source dir, so deeper submodules still import from disk -- but the
    real __init__.py body (with its heavy side effects) never runs."""
    if name in sys.modules:
        return  # real or stubbed already; leave it alone
    mod = types.ModuleType(name)
    mod.__path__ = [str(_PKG_DIR.parent / package_subpath)]
    mod.__package__ = name
    sys.modules[name] = mod


def bootstrap_constrained_albc_stub() -> None:
    """Inject ONLY the top-level ``constrained_albc`` stub. Must run before the
    first ``import constrained_albc`` so the real gym-registering __init__ is
    bypassed. Idempotent."""
    _stub_package("constrained_albc", "constrained_albc")


def _stub_isaaclab_utils() -> None:
    """Stub ``isaaclab.utils`` with a passthrough ``configclass`` decorator.

    ``rsl_rl_ppo_cfg`` (imported transitively when the teacher path touches it)
    does ``from isaaclab.utils import configclass``; the real ``isaaclab/utils
    /__init__`` eagerly imports ``mesh`` -> ``pxr``. The deploy path only needs
    ``configclass`` to be a no-op decorator at class-definition time, so a stub
    that returns the class unchanged is sufficient. isaaclab (pristine fork) is
    never modified -- this only shadows it in ``sys.modules`` during export."""
    if "isaaclab.utils" in sys.modules:
        return
    iu = types.ModuleType("isaaclab.utils")

    def configclass(cls=None, **kwargs):
        return cls if cls is not None else (lambda c: c)

    setattr(iu, "configclass", configclass)
    setattr(iu, "__all__", ["configclass"])
    sys.modules["isaaclab.utils"] = iu


def _isolate_training_imports() -> None:
    """Inject all three stubs so sim-free student/teacher submodules import
    cleanly on a host without pxr. Idempotent; safe to call before each build."""
    bootstrap_constrained_albc_stub()
    _stub_package("constrained_albc.envs", "constrained_albc/envs")
    _stub_package("constrained_albc.envs.main", "constrained_albc/envs/main")
    _stub_isaaclab_utils()
