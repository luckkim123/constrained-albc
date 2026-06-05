"""CPU-only unit tests for the encoder z-sweep adapter (no Isaac Sim, no GPU)."""
import importlib.util
import json
import os
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(REPO, ".omx", "profile", "metrics.yaml")
ADAPTER = os.path.join(REPO, ".omx", "profile", "encoder_adapter.py")
FIXTURE = os.path.join(REPO, "tests", "fixtures", "encoder", "mini_encoder_24d.pt")


def test_encoder_is_a_profile_source():
    """exp-analyze routes by profile sources; encoder must be one."""
    with open(PROFILE) as f:
        prof = yaml.safe_load(f)
    assert "encoder" in prof["sources"], f"sources={prof['sources']}"
