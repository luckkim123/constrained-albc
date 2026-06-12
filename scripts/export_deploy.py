"""Repo-root launcher for the deploy export CLI.

Run this instead of ``python -m constrained_albc.deploy`` on an export host that
lacks the Isaac Sim USD runtime (no ``pxr``). Importing the ``constrained_albc``
package directly fires its gym-registering ``__init__`` -> sim stack -> ``pxr``
and dies before any checkpoint is read. This launcher injects the import-isolation
stubs *before* the package is ever imported, then hands off to the real CLI.

The isolation module is loaded by file path (not ``import constrained_albc...``)
precisely so loading it does not trigger the package ``__init__`` we are trying
to bypass.

Usage (same flags as the CLI):
    cd /workspace/constrained-albc && python scripts/export_deploy.py --list-specs
    python scripts/export_deploy.py --batch attitude_only_5000 \
        --student-ckpt PATH --teacher-ckpt PATH --out DIR --report
"""
from __future__ import annotations

import importlib.util
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_ISOLATION_PY = _REPO_ROOT / "constrained_albc" / "deploy" / "_isolation.py"


def _load_isolation_module():
    """Load deploy/_isolation.py by path, bypassing the package __init__."""
    spec = importlib.util.spec_from_file_location("_deploy_isolation", _ISOLATION_PY)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def main() -> int:
    if str(_REPO_ROOT) not in sys.path:
        sys.path.insert(0, str(_REPO_ROOT))
    iso = _load_isolation_module()
    iso._isolate_training_imports()  # stubs in place before constrained_albc import
    from constrained_albc.deploy.__main__ import main as cli_main
    return cli_main()


if __name__ == "__main__":
    sys.exit(main())
