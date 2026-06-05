"""CPU-only unit tests for the eval analysis wiring (no Isaac Sim)."""
import os
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(REPO, ".omx", "profile", "metrics.yaml")


def test_eval_is_a_profile_source():
    """exp-analyze routes by profile sources; eval must be one."""
    with open(PROFILE) as f:
        prof = yaml.safe_load(f)
    assert "eval" in prof["sources"], f"sources={prof['sources']}"
