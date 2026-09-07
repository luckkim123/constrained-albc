"""Per-dim DORAEMON curriculum verdicts (G3, 2026-07-27).

The fault-DR incident: fault_severity ended at ~8% of its [0,1] range and was
still rising at the last iter, but no text line said so. These tests pin the
four verdicts on synthetic trajectories.

Run: /isaac-sim/python.sh -m pytest test_doraemon_param_verdicts.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_training as at  # noqa: E402


def _series(vals):
    return [(i * 10, float(v)) for i, v in enumerate(vals)]


def _one(name, mean_vals, std_vals, bounds):
    data = {f"DORAEMON/mean/{name}": _series(mean_vals),
            f"DORAEMON/std/{name}": _series(std_vals)}
    out = at._doraemon_param_verdicts(data, {name: bounds})
    assert len(out) == 1
    return out[0]


def test_expanding_one_sided_mean():
    n = 100
    v = _one("fault_severity", [0.001 * i for i in range(n)], [0.02] * n, (0.0, 1.0))
    assert v["verdict"] == "EXPANDING"
    assert abs(v["frac"] - 0.099) < 0.01
    assert v["trend_channel"] == "mean" and v["trend_per_1k"] > 0


def test_saturated_at_bound():
    v = _one("p", [1.0] * 100, [0.05] * 100, (0.0, 1.0))
    assert v["verdict"] == "SATURATED"


def test_saturated_at_uniform_width():
    # centered mean, std ~ uniform width (rng/sqrt(12) = 0.577 for rng=2), both flat
    v = _one("p", [1.0] * 100, [0.55] * 100, (0.0, 2.0))
    assert v["verdict"] == "SATURATED"


def test_stalled_below_bound():
    v = _one("p", [0.3] * 100, [0.02] * 100, (0.0, 1.0))
    assert v["verdict"] == "STALLED"


def test_flat_at_nominal_bound_is_stalled_not_saturated():
    # M2 review fix: a one-sided dim (nominal at lo) that never left nominal is
    # STALLED; only the far bound (frac >= 0.98) saturates.
    v = _one("fault_severity", [0.005] * 100, [0.004] * 100, (0.0, 1.0))
    assert v["verdict"] == "STALLED"


def test_missing_std_tag_reports_mean_channel():
    # m3 review fix: no DORAEMON/std tag -> trend channel must not claim "std".
    data = {"DORAEMON/mean/p": _series([0.3] * 100)}
    out = at._doraemon_param_verdicts(data, {"p": (0.0, 1.0)})
    assert out[0]["trend_channel"] == "mean"
    assert out[0]["std"] is None


def test_contracted_back_toward_start():
    rise = [0.005 * i for i in range(60)]           # 0 -> 0.295
    fall = [0.295 - 0.004 * i for i in range(40)]   # heading back to nominal
    v = _one("p", rise + fall, [0.02] * 100, (0.0, 1.0))
    assert v["verdict"] == "CONTRACTED"


def test_expanding_centered_via_std():
    v = _one("p", [1.0] * 100, [0.001 * i for i in range(100)], (0.0, 2.0))
    assert v["verdict"] == "EXPANDING"
    assert v["trend_channel"] == "std"


def test_diagnosis_carries_expanding_dim():
    n = 100
    data = {"DORAEMON/mean/fault_severity": _series([0.001 * i for i in range(n)]),
            "DORAEMON/std/fault_severity": _series([0.02] * n)}
    lines = at.format_diagnosis({}, data, run_path=None)
    text = "\n".join(lines)
    assert "EXPANDING" in text and "fault_severity" in text
