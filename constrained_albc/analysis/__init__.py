# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Evaluation and training-analysis tooling.

Why the modules in here import each other by BARE name (``from common import ...``)
rather than by package path
--------------------------------------------------------------------------------
This IS a package -- but importing anything through it runs the parent
``constrained_albc/__init__.py``, whose ``from .envs import main`` registers the gym
tasks and cascades into ``albc_env -> isaaclab.sim -> pxr``. Measured 2026-09-07::

    from constrained_albc.analysis.common import DR_LEVELS
        -> ModuleNotFoundError: No module named 'pxr'

Most of this package is deliberately Isaac-Sim-free: the whole sim-free pytest suite,
``analyze.py`` (documented "Pure Python (no Isaac Sim). Run with plain python3"),
``encoder_tools.py`` (sim-free, but it needs torch, so in this container run it under
``/isaac-sim/python.sh``), and ``tools/compare_arms.py`` / ``tools/paper_figures.py`` all
import these modules without a simulator. A package-path import would break every one.

The convention is therefore: the entry points (``eval.py``, ``analyze.py``,
``encoder_tools.py``, and each test) put THIS directory on ``sys.path``, and siblings
import each other by bare name. Those ``sys.path.insert`` lines are load-bearing, not
leftovers -- do not "clean them up". ``_pathsetup.py``, which existed only to repeat that
insert for one sub-module and whose docstring claimed (wrongly) that this directory had
no ``__init__.py``, was deleted in the 2026-09 cleanup.

The one exception is code that already requires Isaac Sim -- ``eval.py`` reaches
``constrained_albc.analysis.student_policy`` and ``constrained_albc.algorithms.*`` by
package path, which is safe there because the simulator is booted by then.
"""
