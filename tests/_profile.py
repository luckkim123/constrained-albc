# Copyright (c) 2026.
"""Resolve the omx profile directory for the CPU-only adapter tests.

The store moved `.omx/profile/` -> `.hq/config/experiments/profile/` on 2026-09-01 and
these two test modules were the only things still pointing at the old path, so they failed
with FileNotFoundError in every clone. One constant here so the next store move is a
one-line edit rather than a grep (rule R4: tests never hardcode a store layout).
"""

import os

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE_DIR = os.path.join(REPO, ".hq", "config", "experiments", "profile")
