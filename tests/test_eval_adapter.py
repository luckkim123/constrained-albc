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


import importlib.util

ADAPTER = os.path.join(REPO, ".omx", "profile", "eval_adapter.py")


def _load_adapter():
    spec = importlib.util.spec_from_file_location("eval_adapter", ADAPTER)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_adapter_imports_sim_free_engine():
    """Adapter must reach _analyze.eval_dr without booting Isaac Sim."""
    mod = _load_adapter()
    assert hasattr(mod, "analyze_eval"), "adapter must expose analyze_eval()"
    assert "isaacsim" not in sys.modules and "isaaclab" not in sys.modules
