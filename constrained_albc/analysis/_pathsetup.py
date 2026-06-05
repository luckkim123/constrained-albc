# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Idempotent sys.path setup for analysis sub-packages.

The analysis/ directory is not a proper Python package (it has no __init__.py
at the top level because it would conflict with Isaac Sim bootstrapping).
Sub-packages (_analyze/, _encoder/) import siblings (common, paths, eval_plots)
via sys.path rather than relative imports.

Import this module at the top of any sub-package __init__.py that needs to
reach analysis/ siblings before they are on sys.path.  Idempotent: safe to
call from multiple modules.

Usage (in any sub-package module that needs to reach analysis/ siblings; the
analysis/ dir is on sys.path via the entrypoint shim, so import by bare name):
    import _pathsetup  # noqa: F401
"""
from __future__ import annotations

import os
import sys

# Insert the analysis/ directory (parent of this file) onto sys.path so that
# sibling modules (common, paths, eval_plots, etc.) resolve without Isaac Sim.
_ANALYSIS_DIR = os.path.dirname(os.path.abspath(__file__))
if _ANALYSIS_DIR not in sys.path:
    sys.path.insert(0, _ANALYSIS_DIR)
