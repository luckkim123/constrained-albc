#!/usr/bin/env python3
"""Entry point for the deploy exporter (the launcher _isolation.py's docstring names).

``python -m constrained_albc.deploy`` cannot work on its own: ``-m`` runs the
top-level ``constrained_albc/__init__.py`` first, which registers the gym tasks and
cascades into ``isaaclab.sim -> pxr``. The export itself is sim-free, so this
launcher injects the ``constrained_albc`` package stub BEFORE the first import --
the bootstrap step ``_isolation.bootstrap_constrained_albc_stub`` exists for -- and
then delegates to the CLI unchanged.

``_isolation`` is loaded straight from its file (not imported as
``constrained_albc.deploy._isolation``, which would trigger the very ``__init__``
being bypassed), so the stub's path logic stays in one place.

Usage mirrors the module CLI exactly:
    cd /workspace/constrained-albc
    /isaac-sim/python.sh scripts/export_deploy_pack.py --list-specs
    /isaac-sim/python.sh scripts/export_deploy_pack.py --batch attitude_only_5000 \
        --student-ckpt PATH --teacher-ckpt PATH \
        --run-group <group> --tag pack_<label> --device cpu --golden --report

--out is cwd-relative, so run this from the repo root: packs belong in
constrained-albc/deploy/, never in the pristine isaaclab fork.
"""
import importlib.util
import pathlib
import sys

_ISOLATION = (pathlib.Path(__file__).resolve().parent.parent
              / "constrained_albc" / "deploy" / "_isolation.py")


def _bootstrap() -> None:
    spec = importlib.util.spec_from_file_location("_albc_deploy_isolation", _ISOLATION)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.bootstrap_constrained_albc_stub()


if __name__ == "__main__":
    _bootstrap()
    from constrained_albc.deploy.__main__ import main

    sys.exit(main())
