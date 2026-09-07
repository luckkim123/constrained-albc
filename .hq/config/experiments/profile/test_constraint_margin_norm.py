"""Tests for constraint margin normalization (J_C/d_k) in analyze_training.py.

The dr-harder teacher report flipped because the TIER2 "this repo" branch printed
ABSOLUTE Constraint/margin/<name> with no d_k normalization. Budgets span 40x
(d_k = budget/(1-cost_gamma) = budget*100), so absolute margin reflects BUDGET SIZE,
not headroom: attitude margin=0.997 was misread as BINDING when it is the DEEPEST
slack (J_C/d_k=0.003); the truly binding channel is thruster_util (J_C/d_k=0.870).

These tests pin the normalized binding ratio J_C/d_k = 1 - margin/d_k against the
verified teacher table, and require a loud failure when budgets can't be resolved.

Run headless (no Isaac Sim): python3 -m pytest test_constraint_margin_norm.py
"""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent))
import analyze_training as at  # noqa: E402


def _curve(last_val, n=300):
    return [(i, last_val) for i in range(n)]


# --- VERIFIED teacher ground truth (raw TB w200): name -> (budget, margin, expected J_C/d_k) ---
# d_k = budget / (1 - cost_gamma) = budget * 100 (cost_gamma=0.99).
# J_C/d_k = 1 - margin/d_k, valid because viol == -margin (slack regime).
_TEACHER = {
    "thruster_util":   (0.40, 5.208,  0.870),  # binding (max ratio)
    "rp_vel_settling": (0.20, 10.893, 0.455),
    "arm_torque":      (0.08, 4.742,  0.407),
    "rp_rate":         (0.10, 6.815,  0.319),
    "yaw_rate":        (0.10, 8.621,  0.138),
    "manipulability":  (0.05, 4.811,  0.038),
    "arm_joint_vel":   (0.02, 1.938,  0.031),
    "joint1_pos":      (0.01, 0.995,  0.005),
    "attitude":        (0.01, 0.997,  0.003),  # DEEPEST slack (NOT binding)
    "cumul_yaw":       (0.01, 1.000,  0.000),  # inert
}


def _teacher_data():
    data = {}
    for name, (_budget, margin, _ratio) in _TEACHER.items():
        data[f"Constraint/margin/{name}"] = _curve(margin)
        data[f"Constraint/viol/{name}"] = _curve(-margin)
    data["Constraint/barrier_penalty"] = _curve(-0.12)
    return data


def _budget_map():
    return {name: budget for name, (budget, _m, _r) in _TEACHER.items()}


# ---- 1. binding ratio formula ----

def test_binding_ratio_matches_teacher_table():
    """J_C/d_k = 1 - margin/(budget/(1-cost_gamma)) must match the verified table."""
    for name, (budget, margin, expected) in _TEACHER.items():
        ratio = at._constraint_binding_ratio(margin, budget, cost_gamma=0.99)
        assert ratio == pytest.approx(expected, abs=2e-3), (
            f"{name}: got {ratio:.3f}, expected {expected:.3f}"
        )


def test_thruster_util_is_the_binding_channel():
    """The MAX J_C/d_k constraint is the binding one — thruster_util, NOT attitude."""
    ratios = {
        name: at._constraint_binding_ratio(margin, budget, cost_gamma=0.99)
        for name, (budget, margin, _r) in _TEACHER.items()
    }
    binding = max(ratios, key=ratios.get)
    assert binding == "thruster_util", f"expected thruster_util binding, got {binding}"
    # attitude is the DEEPEST slack despite tiny absolute margin
    assert ratios["attitude"] < 0.01
    assert ratios["thruster_util"] > ratios["attitude"]  # the flip the report got wrong


def test_binding_ratio_guards_zero_dk():
    """d_k must be > 0; a zero/negative budget yields a guarded result, not a crash."""
    # budget 0 -> d_k 0 -> division guard
    r = at._constraint_binding_ratio(1.0, 0.0, cost_gamma=0.99)
    assert r is None or (isinstance(r, float) and r != r) or r == 0.0  # None/nan/0 sentinel, not exception


# ---- 2. budget resolution ----

def test_budgets_resolve_from_explicit_map():
    """When a budget source is provided, the 10 teacher budgets resolve."""
    budgets = at._constraint_budgets(_teacher_data(), budget_source=_budget_map())
    for name, (budget, _m, _r) in _TEACHER.items():
        assert budgets[name] == pytest.approx(budget)


def test_budgets_unresolvable_raises_loud():
    """If budgets can't be resolved from ANY source (no explicit map, no env.yaml,
    and the discovered constraints are NOT the known full-DOF set), LOUD-FAIL —
    never silently emit margin-only (that re-creates the binding-flip bug).
    rule: don't trust empty/zero engine output."""
    # An unknown constraint name the fallback table cannot cover.
    data = {"Constraint/margin/mystery_constraint": _curve(0.5)}
    with pytest.raises((ValueError, RuntimeError, KeyError, FileNotFoundError)):
        at._constraint_budgets(data, budget_source=None, run_dir=None)


def test_known_fulldof_set_resolves_from_fallback_table():
    """When no explicit source/env.yaml is given but every discovered constraint
    is a known full-DOF term, the verified config.py-mirrored fallback table
    resolves them — this is NOT silent margin-only, it's a checked constant."""
    budgets = at._constraint_budgets(_teacher_data(), budget_source=None, run_dir=None)
    assert budgets["thruster_util"] == pytest.approx(0.40)
    assert budgets["attitude"] == pytest.approx(0.01)


# ---- 3. legacy branch untouched ----

def test_legacy_branch_still_has_dk():
    """The legacy cost_return_/d_k_ branch already normalizes; it must be unchanged."""
    data = {}
    data["Constraint/cost_return_attitude"] = _curve(0.5)
    data["Constraint/d_k_attitude"] = _curve(1.0)
    # legacy path should still discover the name and have d_k available
    names = at._discover_constraint_names(data)
    assert "attitude" in names


# ---- 4. TIER2 integration: the report no longer mis-flags the binding channel ----

def test_tier2_output_flags_thruster_util_binding_not_attitude():
    """format_tier2 on the teacher data must (a) print a JC/dk column on the
    this-repo rows and (b) name thruster_util — NOT attitude — as binding."""
    out = "\n".join(at.format_tier2(_teacher_data())[0])
    assert "JC/dk=" in out, "normalized ratio column missing from TIER2"
    assert "binding (max JC/dk): thruster_util" in out, out
    # the historical mis-read: attitude must NOT be called binding
    assert "binding (max JC/dk): attitude" not in out


def test_tier2_still_prints_absolute_margin():
    """The fix ADDS a column; it must not remove the absolute margin/viol data."""
    out = "\n".join(at.format_tier2(_teacher_data())[0])
    assert "m=" in out and "viol=" in out


def test_tier2_omits_ratio_when_budget_unknown():
    """If constraints are unknown (no budget source), the ratio column is omitted
    gracefully — legacy/foreign workspaces are not broken."""
    data = {"Constraint/margin/mystery": _curve(0.5), "Constraint/viol/mystery": _curve(-0.5)}
    out = "\n".join(at.format_tier2(data)[0])
    assert "mystery" in out          # row still printed
    assert "JC/dk=" not in out       # but no fabricated ratio
