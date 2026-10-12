# Copyright (c) 2026 Seungmin Kim. SPDX-License-Identifier: MIT
"""Resolve the local analysis-profile directory for the CPU-only adapter tests.

The profile (metrics.yaml + the eval/encoder adapters) is local tooling state and is
not tracked in this repository. The two adapter test modules skip when it is absent.
"""

import os

import pytest

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DIR = os.path.join(REPO, ".hq", "config", "experiments", "profile")

requires_profile = pytest.mark.skipif(
    not os.path.isdir(PROFILE_DIR), reason="local analysis profile not present"
)
