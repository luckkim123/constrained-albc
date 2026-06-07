"""Tests for the per-env DR <-> failure join in _analyze/failure_dr.py.

Pure numpy (no sim, no GPU): given an eval data dict (what data_<level>.npz holds —
error_roll[T,N], dr_<name>[N], warmup_steps), the join identifies the worst-k envs by
steady-state error and tests whether their DR distribution is shifted vs the population.
This is the correlational->causal bridge (rule03 differential diagnosis at env level):
the encoder z-sweep flagged lateral CoG/CoB; here we check if the failing envs actually
got larger CoG/CoB offsets.

Run headless: python3 -m pytest test_failure_dr.py
"""
from __future__ import annotations

import os
import sys

import numpy as np

_PKG = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "constrained_albc",
    "analysis",
)
sys.path.insert(0, _PKG)
from _analyze import failure_dr as fd  # noqa: E402


def _data(n=64, t=200, warmup=50, seed=0):
    """Synthetic eval dict where envs with large dr_cog_y also have large roll error.

    Constructed so the causal signal is unambiguous: roll steady-state error is a
    monotone function of dr_cog_y plus small noise -> the worst-k envs MUST have the
    largest dr_cog_y, and the join must detect a strong positive correlation.
    """
    rng = np.random.default_rng(seed)
    cog_y = np.linspace(0.0, 0.1, n).astype(np.float32)  # env i gets increasing CoG-y
    rng.shuffle(cog_y)                                    # break index<->magnitude order
    # roll error grows with cog_y; steady-state (post-warmup) reflects it.
    base_err = cog_y[None, :] * 100.0 + rng.normal(0, 0.05, (t, n)).astype(np.float32)
    return {
        "error_roll": base_err,
        "error_pitch": rng.normal(0, 0.1, (t, n)).astype(np.float32),
        "warmup_steps": warmup,
        "terminated": np.zeros((t, n), dtype=bool),
        "dr_cog_y": cog_y,
        "dr_cog_x": rng.normal(0, 0.01, n).astype(np.float32),   # irrelevant noise DR
        "dr_payload_mass": (1.5 + rng.normal(0, 0.3, n)).astype(np.float32),  # irrelevant
    }


# ---- 1. per-env steady-state error: shape [N], uses post-warmup window ----

def test_per_env_ss_error_shape_and_post_warmup():
    d = _data(n=64, t=200, warmup=50)
    ss = fd.per_env_ss_error(d, axis="roll")
    assert ss.shape == (64,)
    assert np.all(np.isfinite(ss))
    # env with the largest cog_y must have (near) the largest ss error
    assert np.argmax(ss) == np.argmax(d["dr_cog_y"])


def test_per_env_ss_error_norm_combines_roll_pitch():
    d = _data()
    ss = fd.per_env_ss_error(d, axis="att_norm")
    assert ss.shape == (64,)
    assert np.all(ss >= 0)  # norm is non-negative


# ---- 2. failing-env selection: top-k by ss error ----

def test_failing_env_mask_selects_top_k():
    d = _data(n=64)
    ss = fd.per_env_ss_error(d, axis="roll")
    mask = fd.failing_env_mask(ss, k=10)
    assert mask.dtype == bool
    assert mask.sum() == 10
    # the 10 worst-ss envs are exactly the 10 largest-cog_y envs
    top10_cog = set(np.argsort(d["dr_cog_y"])[-10:])
    assert set(np.where(mask)[0]) == top10_cog


def test_failing_env_mask_k_caps_at_n():
    ss = np.arange(5, dtype=float)
    mask = fd.failing_env_mask(ss, k=100)  # k > N
    assert mask.sum() == 5  # all envs, no crash


# ---- 3. the join: detects which DR is shifted in the failing envs ----

def test_join_flags_cog_y_as_the_culprit():
    d = _data(n=64, seed=1)
    result = fd.join_failure_dr(d, axis="roll", k=10)
    # result lists per-DR stats sorted by |correlation|; the top one is dr_cog_y
    assert result["axis"] == "roll"
    assert result["n_failing"] == 10
    top = result["dr_ranking"][0]
    assert top["name"] == "dr_cog_y", f"expected dr_cog_y culprit, got {top['name']}"
    assert top["correlation"] > 0.5            # strong positive corr
    assert top["failing_mean"] > top["population_mean"]  # failing envs got larger cog_y


def test_join_irrelevant_dr_has_low_correlation():
    d = _data(n=64, seed=2)
    result = fd.join_failure_dr(d, axis="roll", k=10)
    ranking = {r["name"]: r for r in result["dr_ranking"]}
    assert abs(ranking["dr_payload_mass"]["correlation"]) < 0.4  # noise DR, weak corr


def test_join_includes_all_dr_channels():
    d = _data()
    result = fd.join_failure_dr(d, axis="roll", k=10)
    names = {r["name"] for r in result["dr_ranking"]}
    assert {"dr_cog_y", "dr_cog_x", "dr_payload_mass"} <= names


def test_join_no_dr_channels_returns_empty_ranking():
    d = _data()
    for k in list(d):
        if k.startswith("dr_"):
            del d[k]
    result = fd.join_failure_dr(d, axis="roll", k=10)
    assert result["dr_ranking"] == []   # nothing to join, graceful


# ---- 4. axis-generic: same join works for a different axis ----

def test_join_axis_generic_pitch():
    d = _data()
    # make pitch the failing axis instead
    t = d["error_roll"].shape[0]
    d["error_pitch"] = np.broadcast_to(d["dr_cog_x"][None, :] * 100.0, (t, 64)).copy()
    result = fd.join_failure_dr(d, axis="pitch", k=10)
    assert result["axis"] == "pitch"
    top = result["dr_ranking"][0]
    assert top["name"] == "dr_cog_x"


# ---- 5. multi-level analysis: levels derived from data keys, NOT static DR_LEVELS ----

def test_analyze_levels_uses_present_levels_only():
    """The audit's P2 bug: static DR_LEVELS drops ood. Here levels come from all_data,
    so an ood-only or 3-level run is handled without fabricating absent levels."""
    all_data = {"none": _data(seed=1), "hard": _data(seed=2), "ood": _data(seed=3)}
    out = fd.analyze_failure_dr_levels(all_data, axis="roll", k=10)
    assert set(out["levels"]) == {"none", "hard", "ood"}  # ood included, soft/medium absent OK
    for lvl in out["levels"]:
        assert out["levels"][lvl]["axis"] == "roll"


def test_analyze_levels_skips_levels_without_error_data():
    all_data = {"hard": _data(), "broken": {"dr_cog_y": np.zeros(64)}}  # no error_roll
    out = fd.analyze_failure_dr_levels(all_data, axis="roll", k=10)
    assert "hard" in out["levels"]
    assert "broken" not in out["levels"]  # skipped, not crashed


# ---- 6. plot data preparation (pure; savefig itself is smoke-verified) ----

def test_build_plot_data_orders_by_abs_correlation():
    d = _data(seed=5)
    join = fd.join_failure_dr(d, axis="roll", k=10)
    pdata = fd.build_failure_dr_plot_data(join, top_n=3)
    assert len(pdata["bars"]) == 3                       # top-3 by |corr|
    assert pdata["bars"][0]["name"] == "dr_cog_y"        # strongest first
    corrs = [abs(b["correlation"]) for b in pdata["bars"]]
    assert corrs == sorted(corrs, reverse=True)          # descending


def test_build_plot_data_empty_ranking_safe():
    pdata = fd.build_failure_dr_plot_data({"axis": "roll", "dr_ranking": []}, top_n=5)
    assert pdata["bars"] == []
