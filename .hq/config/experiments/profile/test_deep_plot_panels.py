"""Tests for dynamic Plot-1 panels in analyze_training.py (GAP 2).

The dr-harder deep-plot blank-panel incident: Plot 1
(01_metrics_changepoints.png) used a FIXED subplots(5,1). When this workspace's
runs log reward but NO Attitude*/roll_deg / *pitch_deg tags, the roll+pitch
panels were rendered BLANK. The fix builds the Plot-1 panel list DYNAMICALLY:
a panel appears only if its tag is present in data, with one uniform legend policy.

Run headless (no Isaac Sim): python3 -m pytest test_deep_plot_panels.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_training as at  # noqa: E402


def _curve(val, n=300):
    """A flat curve [(step, val), ...] of length n."""
    return [(i, float(val)) for i in range(n)]


def _rising(start, slope, n=300):
    return [(i, float(start + slope * i)) for i in range(n)]


# Workspace data: reward + exploration + barrier present, NO roll/pitch under
# EITHER naming. This is exactly what the dr-harder runs logged.
def _ws_no_attitude():
    return {
        "Train/mean_reward": _rising(100.0, 0.1),
        "Policy/mean_noise_std": _curve(0.5),
        "Policy/entropy": _curve(-1.0),
        "Constraint/barrier_penalty": _curve(-0.1),
    }


def _with_attitude(naming="Attitude"):
    data = _ws_no_attitude()
    data[f"{naming}/roll_deg"] = _curve(5.0)
    data[f"{naming}/pitch_deg"] = _curve(3.0)
    return data


def test_plot1_panels_skips_absent_roll_pitch():
    # THE regression: missing roll/pitch must NOT produce panels.
    panels = at._plot1_panels(_ws_no_attitude())
    keys = [k for k, _, _, _ in panels]
    assert "reward" in keys
    assert "exploration" in keys
    assert "barrier" in keys
    assert "roll" not in keys, "roll panel must be absent when its tag is missing"
    assert "pitch" not in keys, "pitch panel must be absent when its tag is missing"


def test_plot1_panels_includes_present_roll_pitch():
    panels = at._plot1_panels(_with_attitude("Attitude"))
    keys = [k for k, _, _, _ in panels]
    assert "roll" in keys and "pitch" in keys


def test_plot1_panels_resolves_attitude_error_naming():
    panels = at._plot1_panels(_with_attitude("Attitude_Error"))
    keys = [k for k, _, _, _ in panels]
    assert "roll" in keys and "pitch" in keys


def test_plot1_panel_count_matches_present_tags():
    # n_present panels exactly -- no blank ones.
    data_full = _with_attitude("Attitude")
    data_none = _ws_no_attitude()
    assert len(at._plot1_panels(data_full)) == 5    # reward,roll,pitch,expl,barrier
    assert len(at._plot1_panels(data_none)) == 3    # reward,expl,barrier


def test_plot1_panels_minimal_single_panel():
    # Only reward present -> exactly one panel; must not crash on subplots.
    data = {"Train/mean_reward": _rising(0.0, 1.0)}
    panels = at._plot1_panels(data)
    assert [k for k, _, _, _ in panels] == ["reward"]


def test_generate_deep_plots_no_blank_panel_when_attitude_absent():
    # End-to-end: the saved figure has axis count == present-panel count, i.e.
    # NO empty axes. We assert via the testable helper + that the PNG saves.
    data = _ws_no_attitude()
    n_present = len(at._plot1_panels(data))
    assert n_present == 3
    with tempfile.TemporaryDirectory() as td:
        saved = at.generate_deep_plots(data, td)
        p1 = Path(td) / "analysis" / "01_metrics_changepoints.png"
        assert p1.exists()
        assert str(p1) in saved
