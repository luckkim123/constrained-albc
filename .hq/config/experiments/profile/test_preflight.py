"""Preflight contract for analyze_training.py (G1, 2026-07-27).

Under ANY interpreter the engine must either run or fail with the actionable
[PREFLIGHT] message naming /isaac-sim/python.sh -- never a raw scipy/tensorboard
ImportError traceback.

Run headless (no Isaac Sim): python3 -m pytest test_preflight.py
"""
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).resolve().parent / "analyze_training.py"


def test_preflight_contract():
    r = subprocess.run(
        [sys.executable, str(SCRIPT), "--list"],
        capture_output=True, text=True, timeout=180,
    )
    if r.returncode == 0:
        return  # healthy interpreter: engine ran
    assert r.returncode == 2, f"unexpected exit {r.returncode}: {r.stderr[-500:]}"
    assert "[PREFLIGHT]" in r.stderr
    assert "/isaac-sim/python.sh" in r.stderr
    assert "Traceback" not in r.stderr


def test_deep_banner_names_fallback_backend():
    try:
        sys.path.insert(0, str(SCRIPT.parent))
        import analyze_training as at
        import tslib
    except (ImportError, SystemExit):
        import pytest
        pytest.skip("engine deps unavailable under this interpreter")
    saved = (tslib.HAS_RUPTURES, tslib.HAS_HMMLEARN)
    try:
        tslib.HAS_RUPTURES = False
        tslib.HAS_HMMLEARN = False
        lines = at.format_deep({"Train/mean_reward": [(i, float(i)) for i in range(300)]})
        text = "\n".join(lines)
        assert "CUSUM fallback" in text
        assert "hmmlearn unavailable" in text
    finally:
        tslib.HAS_RUPTURES, tslib.HAS_HMMLEARN = saved
