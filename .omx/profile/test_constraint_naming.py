"""Tests for constraint discovery in analyze_training.py — the dr-harder
engine-output-unverified incident.

This workspace logs constraints as Constraint/margin/<name> + Constraint/viol/<name>
(+ Constraint/barrier_penalty), but the engine only scanned the legacy
Constraint/cost_return_* / barrier_margin_* / d_k_* naming. Result: the engine
printed "constraints=0" + an empty TIER 2 table while the TB held 11 live
constraints. These tests pin BOTH namings so the table fills either way.

Run headless (no Isaac Sim): python3 -m pytest test_constraint_naming.py
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_training as at  # noqa: E402


def _curve(last_val, n=300):
    """A flat-ish curve [(step, val)] whose last value is `last_val`."""
    return [(i, last_val) for i in range(n)]


# --- this workspace's real naming: margin/<name> + viol/<name> ---
# margin > 0 = satisfied; viol = -margin (verified: +0.9968 <-> -0.9968).
_WS_NAMES = ["attitude", "cumul_yaw", "yaw_rate", "thruster_util"]


def _ws_data():
    data = {}
    for name, margin in zip(_WS_NAMES, [0.9968, 0.9997, 8.6206, 5.2082]):
        data[f"Constraint/margin/{name}"] = _curve(margin)
        data[f"Constraint/viol/{name}"] = _curve(-margin)
    data["Constraint/barrier_penalty"] = _curve(-0.12)
    return data


# --- legacy naming: cost_return_/d_k_/barrier_margin_ ---
def _legacy_data():
    data = {}
    for name, cr, dk in [("attitude", 0.3, 1.0), ("yaw_rate", 0.1, 1.0)]:
        data[f"Constraint/cost_return_{name}"] = _curve(cr)
        data[f"Constraint/d_k_{name}"] = _curve(dk)
        data[f"Constraint/barrier_margin_{name}"] = _curve(dk - cr)
    data["Constraint/barrier_penalty"] = _curve(0.02)
    return data


def test_discover_finds_workspace_margin_viol_names():
    names = at._discover_constraint_names(_ws_data())
    assert set(names) == set(_WS_NAMES)


def test_discover_finds_legacy_cost_return_names():
    names = at._discover_constraint_names(_legacy_data())
    assert set(names) == {"attitude", "yaw_rate"}


def test_discover_unions_both_namings():
    data = {**_ws_data(), **_legacy_data()}
    names = at._discover_constraint_names(data)
    # union: ws 4 names + legacy yaw_rate already in ws; legacy adds nothing new here
    assert set(names) >= set(_WS_NAMES)


def test_tier2_table_fills_for_workspace_naming():
    # THE regression: previously this produced an empty constraint section.
    lines, _viol = at.format_tier2(_ws_data())
    text = "\n".join(lines)
    assert "[TIER 2] Constraints" in text
    # every workspace constraint name appears as a row
    for name in _WS_NAMES:
        assert name in text, f"{name} missing from TIER2 table"


def test_tier2_margin_value_is_shown_for_workspace_naming():
    lines, _viol = at.format_tier2(_ws_data())
    text = "\n".join(lines)
    # the margin column must carry the actual value, not N/A. yaw_rate margin
    # 8.6206 renders as 8.62 (precision 2; attitude 0.9968 rounds to 1.00).
    assert "8.62" in text
    assert "5.21" in text  # thruster_util margin 5.2082
    assert "m=" in text and "viol=" in text  # the margin/viol columns exist
    assert "N/A" not in text  # no constraint row fell through to N/A


def test_tier2_table_still_fills_for_legacy_naming():
    lines, _viol = at.format_tier2(_legacy_data())
    text = "\n".join(lines)
    assert "[TIER 2] Constraints" in text
    assert "attitude" in text
    assert "yaw_rate" in text


def test_violation_flagged_when_margin_negative():
    # a margin < 0 (= viol > 0) means the constraint is OVER its budget.
    data = {
        "Constraint/margin/attitude": _curve(-0.5),   # violated
        "Constraint/viol/attitude": _curve(0.5),
        "Constraint/margin/yaw_rate": _curve(2.0),    # satisfied
        "Constraint/viol/yaw_rate": _curve(-2.0),
    }
    lines, _viol = at.format_tier2(data)
    text = "\n".join(lines)
    assert "OVER" in text  # attitude is over-budget
    # the satisfied one must NOT be flagged OVER on its own row
    over_rows = [ln for ln in lines if "OVER" in ln]
    assert any("attitude" in ln for ln in over_rows)
    assert not any("yaw_rate" in ln for ln in over_rows)
