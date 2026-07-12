# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""CLI shim for the analyze package (recompute / eval_dr / switching / student_latent).

The implementation lives in the sibling `_analyze/` package. This shim keeps the
historical invocation path (`python constrained_albc/analysis/analyze.py
<subcommand>`) working and puts the analysis directory on sys.path so both this
module's `import _analyze` and `_analyze`'s `from common import ...` resolve.

Pure Python (no Isaac Sim). Run with plain python3.

Usage:
    python3 constrained_albc/analysis/analyze.py recompute logs/.../run_dir
    python3 constrained_albc/analysis/analyze.py eval_dr 0 1 --labels A B
    python3 constrained_albc/analysis/analyze.py student_latent logs/.../latent_diagnostic
"""

from __future__ import annotations

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from _analyze import main  # type: ignore[import-not-found]

if __name__ == "__main__":
    raise SystemExit(main())
