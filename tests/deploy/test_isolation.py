"""Regression tests for the training-import isolation shim.

The deploy export runs on hosts where `constrained_albc`'s package __init__
(`from .envs import main` -> albc_env -> isaaclab.sim -> pxr) cannot import
because pxr is absent. The student/teacher *build* code is sim-free, so the
isolation shim pre-injects lightweight stubs for the three heavy import roots
(`constrained_albc`, `constrained_albc.envs.main`, `isaaclab.utils`) and the
deep submodules load against the unmodified source.

Each test runs in a fresh subprocess that reproduces the launcher's bootstrap
(load `_isolation.py` by file path, inject stubs, THEN import the package), so
each asserts on a clean interpreter exactly as the export host experiences it.
"""
from __future__ import annotations

import subprocess
import sys
import textwrap

REPO = "/workspace/constrained-albc"

# Bootstrap prelude: every subprocess loads _isolation.py by path (never via the
# package, which would fire the __init__ we are bypassing) and injects stubs.
_PRELUDE = """
import importlib.util, pathlib, sys
sys.path.insert(0, "/workspace/constrained-albc")
_iso_py = pathlib.Path("/workspace/constrained-albc/constrained_albc/deploy/_isolation.py")
_spec = importlib.util.spec_from_file_location("_deploy_isolation", _iso_py)
_iso = importlib.util.module_from_spec(_spec); _spec.loader.exec_module(_iso)
_iso._isolate_training_imports()
"""


def _run(body: str) -> subprocess.CompletedProcess:
    code = _PRELUDE + textwrap.dedent(body)
    return subprocess.run(
        [sys.executable, "-c", code],
        cwd=REPO, capture_output=True, text=True, timeout=180,
    )


def test_isolate_lets_student_module_import_without_pxr():
    """After the shim, the student model module imports though pxr is absent."""
    r = _run(
        """
        import constrained_albc.envs.main.student.models as m
        assert hasattr(m, "StudentEncoderTCN"), "student model class missing"
        print("STUDENT_IMPORT_OK")
        """
    )
    assert "STUDENT_IMPORT_OK" in r.stdout, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "pxr" not in r.stderr, f"pxr leaked: {r.stderr!r}"


def test_isolate_lets_encoder_import_without_pxr():
    """The teacher build needs ActorCriticEncoder; it must import pxr-free."""
    r = _run(
        """
        from constrained_albc.envs.main.encoder import ActorCriticEncoder
        assert ActorCriticEncoder is not None
        print("ENCODER_IMPORT_OK")
        """
    )
    assert "ENCODER_IMPORT_OK" in r.stdout, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "pxr" not in r.stderr, f"pxr leaked: {r.stderr!r}"


def test_teacher_build_path_does_not_import_sim_stack():
    """Building the teacher imports the encoder but must NOT pull rsl_rl_ppo_cfg
    -> isaaclab_rl -> the sim stack (which would need pxr). The encoder import
    alone, after the shim, leaves the sim stack out of sys.modules."""
    r = _run(
        """
        from constrained_albc.envs.main.encoder import ActorCriticEncoder  # noqa: F401
        assert "isaaclab_rl.rsl_rl" not in sys.modules, "sim stack leaked in"
        print("TEACHER_PATH_CLEAN")
        """
    )
    assert "TEACHER_PATH_CLEAN" in r.stdout, f"stdout={r.stdout!r} stderr={r.stderr!r}"
    assert "pxr" not in r.stderr, f"pxr leaked: {r.stderr!r}"


def test_isolate_is_idempotent():
    """Calling the shim twice must not raise (CLI builds student then teacher)."""
    r = _run(
        """
        _iso._isolate_training_imports()
        _iso._isolate_training_imports()
        print("IDEMPOTENT_OK")
        """
    )
    assert "IDEMPOTENT_OK" in r.stdout, f"stdout={r.stdout!r} stderr={r.stderr!r}"
