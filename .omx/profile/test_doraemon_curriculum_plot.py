"""Tests for the DORAEMON curriculum band plot in analyze_training.py (GAP 3).

No plot rendered the curriculum trajectory as DORAEMON/mean/<p> line +
+-DORAEMON/std/<p> band vs iteration (grep: DORAEMON/mean/ used nowhere). The fix
adds 05_doraemon_curriculum.png that auto-discovers DORAEMON/mean/* params, plots
each as a line with a fill_between(+-std) band, and SKIPS CLEANLY (with a logged
message, not a silent blank -- that was GAP 2's lesson) when no such tags exist.

Run headless (no Isaac Sim): python3 -m pytest test_doraemon_curriculum_plot.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_training as at  # noqa: E402


def _curve(val, n=300):
    return [(i, float(val)) for i in range(n)]


def _rising(start, slope, n=300):
    return [(i, float(start + slope * i)) for i in range(n)]


def _dora_data():
    data = {"Train/mean_reward": _rising(100.0, 1.0)}
    data["DORAEMON/mean/payload_mass"] = _rising(1.5, 0.001)
    data["DORAEMON/std/payload_mass"] = _curve(0.4)
    data["DORAEMON/mean/buoyancy_force"] = _curve(26.0)
    data["DORAEMON/std/buoyancy_force"] = _curve(2.0)
    return data


def _no_dora_data():
    return {
        "Train/mean_reward": _rising(100.0, 0.1),
        "Policy/mean_noise_std": _curve(0.5),
        "Constraint/barrier_penalty": _curve(-0.1),
    }


def test_discover_doraemon_params_finds_mean_tags():
    params = at._discover_doraemon_params(_dora_data())
    assert set(params) == {"payload_mass", "buoyancy_force"}


def test_discover_doraemon_params_empty_when_absent():
    assert at._discover_doraemon_params(_no_dora_data()) == []


def test_discover_doraemon_params_ignores_std_only():
    # A param with std but no mean has no trajectory to anchor -> not discovered.
    data = {"DORAEMON/std/orphan": _curve(1.0)}
    assert at._discover_doraemon_params(data) == []


def test_curriculum_band_png_produced_when_tags_present():
    data = _dora_data()
    with tempfile.TemporaryDirectory() as td:
        saved = at.generate_deep_plots(data, td)
        p = Path(td) / "analysis" / "05_doraemon_curriculum.png"
        assert p.exists(), "curriculum band PNG must be produced when DORAEMON/mean/* present"
        assert str(p) in saved


def test_curriculum_band_clean_skip_when_absent():
    # No DORAEMON tags -> no curriculum PNG, and NOT a silent blank one.
    data = _no_dora_data()
    with tempfile.TemporaryDirectory() as td:
        saved = at.generate_deep_plots(data, td)
        p = Path(td) / "analysis" / "05_doraemon_curriculum.png"
        assert not p.exists()
        assert not any("doraemon" in Path(s).name.lower() for s in saved)


def test_curriculum_band_handles_mean_without_std():
    # mean present, std missing for one param -> still plots the line (no band),
    # PNG produced, no crash.
    data = {
        "Train/mean_reward": _rising(0.0, 1.0),
        "DORAEMON/mean/payload_mass": _rising(1.5, 0.001),
        # no std for payload_mass
    }
    with tempfile.TemporaryDirectory() as td:
        saved = at.generate_deep_plots(data, td)
        p = Path(td) / "analysis" / "05_doraemon_curriculum.png"
        assert p.exists()
        assert str(p) in saved
