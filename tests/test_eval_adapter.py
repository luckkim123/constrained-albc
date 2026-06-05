"""CPU-only unit tests for the eval analysis wiring (no Isaac Sim)."""
import importlib.util
import json
import os
import subprocess
import sys

import yaml

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PROFILE = os.path.join(REPO, ".omx", "profile", "metrics.yaml")
ADAPTER = os.path.join(REPO, ".omx", "profile", "eval_adapter.py")
FIXTURE_DIR = os.path.join(REPO, "tests", "fixtures", "eval")
_FIXTURE_NPZ = os.path.join(FIXTURE_DIR, "data_none.npz")


def _load_adapter():
    spec = importlib.util.spec_from_file_location("eval_adapter", ADAPTER)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_eval_is_a_profile_source():
    """exp-analyze routes by profile sources; eval must be one."""
    with open(PROFILE) as f:
        prof = yaml.safe_load(f)
    assert "eval" in prof["sources"], f"sources={prof['sources']}"


def test_adapter_imports_sim_free_engine():
    """Adapter must reach _analyze.eval_dr without booting Isaac Sim."""
    mod = _load_adapter()
    assert hasattr(mod, "analyze_eval"), "adapter must expose analyze_eval()"
    assert "isaacsim" not in sys.modules and "isaaclab" not in sys.modules


def test_analyze_eval_returns_driver_dict():
    """analyze_eval delegates to _ed_analyze_run and returns its structure."""
    if not os.path.exists(_FIXTURE_NPZ):
        import pytest
        pytest.skip("fixture absent — copy from SOURCE.txt")
    mod = _load_adapter()
    out = mod.analyze_eval(FIXTURE_DIR)
    assert "levels" in out
    assert "none" in out["levels"], f"levels present: {list(out['levels'])}"
    roll = out["levels"]["none"]["axes"]["roll"]["heavy_tail"]
    assert "peak_max" in roll and "peak_mean" in roll and "pct_peak_gt_thresh" in roll
    assert roll["peak_max"] >= roll["peak_mean"] >= 0.0


def test_cli_emits_json():
    """The adapter is runnable as a subprocess emitting JSON (exp-analyze code-exec)."""
    result = subprocess.run(
        [sys.executable, ADAPTER, "heavy-tail", FIXTURE_DIR],
        capture_output=True, text=True, timeout=60,
    )
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["levels"]["none"]["axes"]["roll"]["heavy_tail"]["peak_max"] >= 0.0
