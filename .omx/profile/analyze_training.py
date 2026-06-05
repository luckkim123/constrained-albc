#!/usr/bin/env python3
"""Token-efficient training log analyzer for Constrained ALBC RL training.

Reads TensorBoard event files and produces a compact tiered summary
designed to minimize token usage when read by an LLM agent.

Usage:
    python analyze_training.py                    # latest run, auto tier
    python analyze_training.py /path/to/run       # specific run
    python analyze_training.py 0                  # latest run (index 0)
    python analyze_training.py 3                  # 4th most recent run
    python analyze_training.py --tier 1           # core health only
    python analyze_training.py --tier 3           # full detail
    python analyze_training.py --last 50          # last 50 data points only
    python analyze_training.py --deep             # time-series analysis
    python analyze_training.py --list             # list available runs
"""

import argparse
import os
import sys
from pathlib import Path

import numpy as np
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))
import tslib

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

LOGS_ROOT = os.environ.get("ALBC_LOGS_ROOT", "/workspace/constrained-albc/logs/rsl_rl")

# ==================================================================
# 1. CONSTANTS & CONFIG
# ==================================================================

ANOMALY_RULES = {
    "Policy/entropy":             lambda v: "COLLAPSED" if v < 0 else ("LOW" if v < 0.5 else ""),
    "Policy/mean_noise_std":      lambda v: "LOW" if v < 0.25 else ("CEILING" if v >= 0.95 else ""),
    "Encoder/z_min":              lambda v: "SAT" if v < -0.98 else "",
    "Encoder/z_max":              lambda v: "SAT" if v > 0.98 else "",
    "Encoder/z_std":              lambda v: "LOW" if v < 0.1 else "",
    "Encoder/grad_norm":          lambda v: "DEAD" if v < 1e-4 else "",
    "Policy/line_search_success": lambda v: "FAIL" if v < 0.5 else "",
    "Constraint/barrier_penalty": lambda v: "SPIKE" if v > 0.1 else "",
    "Train/mean_reward":          lambda v: "NEG" if v < 0 else "",
    # Attitude (both tag variants for hero_agent and constrained_full_albc)
    "Attitude_Error/roll_deg":    lambda v: "HIGH" if v > 20 else "",
    "Attitude_Error/pitch_deg":   lambda v: "HIGH" if v > 25 else "",
    "Attitude/roll_deg":          lambda v: "HIGH" if v > 20 else "",
    "Attitude/pitch_deg":         lambda v: "HIGH" if v > 25 else "",
    # Action (both tag variants)
    "Action/rate_mean":           lambda v: "HIGH" if v > 1.0 else "",
    "Action/arm_rate":            lambda v: "HIGH" if v > 1.0 else "",
    "Dynamics/joint_vel_abs_max": lambda v: "HIGH" if v > 3.0 else "",
    # constrained_full_albc specific
    "Episode_Termination/too_fast_ang": lambda v: "HIGH" if v > 0.5 else "",
    "Episode_Termination/too_fast_lin": lambda v: "HIGH" if v > 0.5 else "",
    "Thruster/utilization_max":   lambda v: "HIGH" if v > 0.95 else "",
}

# --deep: full time-series analysis (phase + plateau + changepoint)
# NOTE: Uses _resolve_full_analysis_metrics() at runtime for env-specific tags.
FULL_ANALYSIS_METRICS = [
    ("reward",    "Train/mean_reward",          True),   # increasing
    ("roll_err",  "Attitude_Error/roll_deg",    False),  # decreasing
    ("pitch_err", "Attitude_Error/pitch_deg",   False),  # decreasing
]


def _resolve(data, *candidates):
    """Return first tag from candidates that exists in data, or first candidate."""
    for tag in candidates:
        if tag in data:
            return tag
    return candidates[0]


def _resolve_full_analysis_metrics(data):
    """Return FULL_ANALYSIS_METRICS with environment-specific tags resolved."""
    return [
        ("reward",    "Train/mean_reward", True),
        ("roll_err",  _resolve(data, "Attitude/roll_deg", "Attitude_Error/roll_deg"), False),
        ("pitch_err", _resolve(data, "Attitude/pitch_deg", "Attitude_Error/pitch_deg"), False),
    ]

# ==================================================================
# 2. CONFIG READING
# ==================================================================

def load_config(run_path):
    """Load training config from params/agent.yaml or config.json."""
    run_path = Path(run_path)
    agent_yaml = run_path / "params" / "agent.yaml"
    env_yaml = run_path / "params" / "env.yaml"
    config_json = run_path / "config.json"

    cfg = {}
    if agent_yaml.exists():
        try:
            with open(agent_yaml) as f:
                cfg["agent"] = yaml.full_load(f) or {}
        except Exception:
            cfg["agent"] = {}
    if env_yaml.exists():
        try:
            with open(env_yaml) as f:
                cfg["env"] = yaml.full_load(f) or {}
        except Exception:
            cfg["env"] = {}
    if not cfg and config_json.exists():
        import json
        try:
            with open(config_json) as f:
                cfg["agent"] = json.load(f)
        except Exception:
            pass
    return cfg


def format_config(cfg):
    """Format config summary as compact lines."""
    if not cfg:
        return []

    agent = cfg.get("agent", {})
    algo = agent.get("algorithm", {})
    policy = agent.get("policy", {})

    lines = ["[CONFIG] key params"]

    # Line 1: TRPO + barrier params
    parts1 = []
    key_map = {
        "max_kl": "max_kl", "beta": "beta", "barrier_t": "barrier_t",
        "barrier_t_final": "barrier_t_final", "cg_damping": "cg_damp",
        "line_search_kl_margin": "ls_kl_margin",
    }
    for key, short in key_map.items():
        v = algo.get(key)
        if v is not None:
            parts1.append(f"{short}={v}")
    if parts1:
        lines.append("  " + ", ".join(parts1))

    # Line 2: entropy + encoder
    parts2 = []
    for key, short in [("entropy_coef", "entropy_coef"), ("min_std", "min_std"),
                        ("encoder_lr", "enc_lr"), ("num_encoder_epochs", "enc_epochs"),
                        ("max_encoder_kl", "max_enc_kl")]:
        v = algo.get(key)
        if v is not None:
            parts2.append(f"{short}={v}")
    if parts2:
        lines.append("  " + ", ".join(parts2))

    # Line 3: constraints + training setup
    parts3 = []
    num_c = algo.get("num_constraints")
    budgets = algo.get("constraint_budgets")
    if num_c is not None:
        parts3.append(f"constraints={num_c}")
    if budgets is not None:
        budget_str = ",".join(f"{b}" for b in budgets)
        parts3.append(f"budgets=({budget_str})")
    max_iters = agent.get("max_iterations")
    if max_iters is not None:
        parts3.append(f"max_iter={max_iters}")
    steps = agent.get("num_steps_per_env")
    if steps is not None:
        parts3.append(f"steps/env={steps}")
    if parts3:
        lines.append("  " + ", ".join(parts3))

    # Store for TB-based constraint count correction (applied after TB load)
    cfg["_yaml_num_constraints"] = num_c

    # Line 4: network architecture if present
    hidden = policy.get("actor_hidden_dims") or policy.get("hidden_dims")
    if hidden:
        enc_hidden = policy.get("encoder_hidden_dims")
        arch = f"actor={hidden}"
        if enc_hidden:
            arch += f", encoder={enc_hidden}"
        lines.append(f"  {arch}")

    return lines if len(lines) > 1 else []


# ==================================================================
# 3. DATA HELPERS
# ==================================================================

def _last(data, tag, default=None):
    if tag not in data or not data[tag]:
        return default
    return data[tag][-1][1]


def _values(data, tag):
    if tag not in data:
        return []
    return [v for _, v in data[tag]]


def _trend(data, tag):
    """Mean of last 20% minus mean of first 20%."""
    vals = _values(data, tag)
    if len(vals) < 5:
        return None
    n = max(1, len(vals) // 5)
    return sum(vals[-n:]) / n - sum(vals[:n]) / n


def _fmt(v, precision=2):
    if v is None:
        return "N/A"
    if abs(v) < 0.001 and v != 0:
        return f"{v:.1e}"
    if abs(v) >= 1000:
        return f"{v:.0f}"
    return f"{v:.{precision}f}"


def _arrow(t):
    if t is None:
        return " "
    return "^" if t > 0.01 else ("v" if t < -0.01 else "=")


def _quartile_arrow_str(data, tag):
    """Return 4-char quartile arrow string, or padded single arrow if <20 points."""
    vals = _values(data, tag)
    slopes = tslib.quartile_slopes(np.array(vals, dtype=np.float64)) if len(vals) >= 20 else None
    if slopes is not None:
        return tslib.quartile_arrows(slopes)
    t = _trend(data, tag)
    return f" {_arrow(t)}  "


# ==================================================================
# 3. RUN DISCOVERY
# ==================================================================

def find_runs(root=LOGS_ROOT):
    """Find all run directories sorted by timestamp (newest first)."""
    runs = []
    root_path = Path(root)
    if not root_path.exists():
        return runs
    for exp_dir in sorted(root_path.iterdir()):
        if not exp_dir.is_dir():
            continue
        for run_dir in sorted(exp_dir.iterdir(), reverse=True):
            if not run_dir.is_dir():
                continue
            if list(run_dir.glob("events.out.tfevents.*")):
                runs.append(run_dir)
    runs.sort(key=lambda p: p.name, reverse=True)
    return runs


def load_events(run_path):
    """Load all scalar metrics from TensorBoard event files."""
    ea = EventAccumulator(str(run_path))
    ea.Reload()
    data = {}
    for tag in ea.Tags().get("scalars", []):
        events = ea.Scalars(tag)
        data[tag] = [(e.step, e.value) for e in events]
    return data


# ==================================================================
# 4. ANOMALY & DIAGNOSIS
# ==================================================================

def _check_arm_frozen(data):
    """Detect arm freeze: joint velocity near zero + action magnitude near zero."""
    jv = _last(data, "Dynamics/joint_vel_abs_max")
    act = _last(data, _resolve(data, "Action/arm_norm", "Action/size_mean"))
    return jv is not None and act is not None and jv < 0.5 and act < 0.15


def _check_reward_plateau(data):
    """Detect reward plateau: last 30% trend is flat despite early improvement.

    Thresholds normalized by data range (scale-invariant).
    """
    vals = _values(data, "Train/mean_reward")
    if len(vals) < 20:
        return False
    n = len(vals)
    data_range = max(vals) - min(vals)
    if data_range < 1e-8:
        return False
    early_trend = sum(vals[n // 3:n * 2 // 3]) / max(1, n // 3) - sum(vals[:n // 3]) / max(1, n // 3)
    late_trend = sum(vals[-n // 5:]) / max(1, n // 5) - sum(vals[-n * 2 // 5:-n // 5]) / max(1, n // 5)
    return early_trend / data_range > 0.1 and abs(late_trend) / data_range < 0.02


def _check_cost_divergence(data):
    """Detect cost divergence: 2+ cost_returns increasing in latter half."""
    diverging = _find_diverging_costs(data)
    return len(diverging) >= 2


def _find_diverging_costs(data):
    """Find costs whose return is increasing in the latter half of training.

    Dual-schema: reconstructs the cost series via _constraint_series so it
    works on both the old cost_return_ tags and new margin//d_k/ tags.
    """
    diverging = []
    for name in _constraint_names(data):
        vals, _dk = _constraint_series(data, name)
        if not vals or len(vals) < 20:
            continue
        n = len(vals)
        mid_start, mid_end = n // 4, n // 2
        mid_mean = sum(vals[mid_start:mid_end]) / max(1, mid_end - mid_start)
        last_mean = sum(vals[-n // 4:]) / max(1, n // 4)
        if mid_mean > 0.1 and last_mean > mid_mean * 1.2:
            diverging.append(name)
    return diverging


def _check_all_quarters_declining(data):
    """Detect all 4 quartile slopes negative for reward."""
    vals = _values(data, "Train/mean_reward")
    if len(vals) < 20:
        return False
    slopes = tslib.quartile_slopes(np.array(vals, dtype=np.float64))
    return slopes is not None and all(s < 0 for s in slopes)


def _check_barrier_spikes(data):
    """Detect barrier penalty spikes above 0.1."""
    bp_vals = _values(data, "Constraint/barrier_penalty")
    if len(bp_vals) < 10:
        return False
    return max(bp_vals) > 0.1


def _check_early_convergence(data):
    """Detect early improvement followed by flat Q3-Q4.

    Thresholds normalized by data range (scale-invariant).
    """
    vals = _values(data, "Train/mean_reward")
    if len(vals) < 40:
        return False
    slopes = tslib.quartile_slopes(np.array(vals, dtype=np.float64))
    if slopes is None:
        return False
    data_range = max(vals) - min(vals)
    if data_range < 1e-8:
        return False
    n = len(vals)
    quarter_len = n / 4.0
    norm = [s * quarter_len / data_range for s in slopes]
    improving_early = norm[0] > 0.1 or norm[1] > 0.1
    flat_late = abs(norm[2]) < 0.02 and abs(norm[3]) < 0.02
    return improving_early and flat_late


def _cost_trend_late_series(vals):
    """Compute trend in latter half only (last 25% mean vs middle 25% mean).

    Operates on a pre-extracted series so it works on costs reconstructed
    from either tag schema (see _constraint_series).
    """
    if not vals or len(vals) < 10:
        return " ", ""
    n = len(vals)
    mid_start, mid_end = n // 4, n // 2
    mid_mean = sum(vals[mid_start:mid_end]) / max(1, mid_end - mid_start)
    last_mean = sum(vals[-n // 4:]) / max(1, n // 4)
    diff = last_mean - mid_mean
    arrow = "^" if diff > 0.01 else ("v" if diff < -0.01 else "=")
    alert = "DIVG" if (mid_mean > 0.1 and last_mean > mid_mean * 1.2) else ""
    return arrow, alert


def _cost_trend_late(data, tag):
    """Compute trend in latter half only (last 25% mean vs middle 25% mean)."""
    return _cost_trend_late_series(_values(data, tag))


def _constraint_names(data):
    """Discover constraint names from either tag schema.

    Two schemas exist in the wild:
      old (synthetic): Constraint/cost_return_{name} + Constraint/d_k_{name}
      new (real runs): Constraint/margin/{name} + Constraint/viol/{name} (+ Constraint/d_k/{name})
    """
    names = set()
    for tag in data:
        if tag.startswith("Constraint/cost_return_"):
            names.add(tag.replace("Constraint/cost_return_", ""))
        elif tag.startswith("Constraint/margin/"):
            names.add(tag.split("Constraint/margin/", 1)[1])
    return sorted(names)


def _constraint_series(data, name):
    """Return (cost_series, d_k) for a constraint across both tag schemas.

    cost is the discounted-sum cost return; d_k is the discounted budget
    D_k/(1-cost_gamma). Returns (cost_list_or_None, d_k_or_None). When the
    new schema is present without a logged d_k (older real runs), cost cannot
    be reconstructed in absolute terms, so cost is None and only margin/viol
    raw values remain available to callers.
    """
    cr = _values(data, f"Constraint/cost_return_{name}")
    if cr:
        dk = _last(data, f"Constraint/d_k_{name}")
        return cr, dk
    # new schema: cost = d_k - margin (per-iter), needs logged d_k
    margin = _values(data, f"Constraint/margin/{name}")
    if not margin:
        return None, None
    dk = _last(data, f"Constraint/d_k/{name}")
    if dk is None or dk <= 0:
        return None, None
    cost = [max(0.0, dk - m) for m in margin]
    return cost, dk


def _cost_ratio_q4(data, name):
    """Mean cost/d_k over the last quarter, or None if unavailable."""
    cost, dk = _constraint_series(data, name)
    if not cost or dk is None or dk <= 0:
        return None
    q4 = cost[int(len(cost) * 0.75):]
    if not q4:
        return None
    return (sum(q4) / len(q4)) / dk


def _find_inert_constraints(data, achieved_below=0.20, loose_above=0.80):
    """Classify constraints that are not shaping learning.

    Returns (achieved, loose): constraints whose Q4 cost/d_k stays below
    achieved_below (cost achieved far under budget -> constraint trivially
    satisfied) vs above loose_above without ever binding (budget so loose the
    cost sits just under it -> constraint near-inert). Both mean the term is
    not actively constraining the policy, for opposite reasons.
    """
    achieved, loose = [], []
    for name in _constraint_names(data):
        r = _cost_ratio_q4(data, name)
        if r is None:
            continue
        if r < achieved_below:
            achieved.append((name, r))
        elif r > loose_above:
            loose.append((name, r))
    return achieved, loose


def _margin_at_floor(data, name):
    """Check if barrier margin is at the floor (0.015 * d_k). Dual-schema."""
    dk = _last(data, f"Constraint/d_k_{name}")
    margin = _last(data, f"Constraint/barrier_margin_{name}")
    if margin is None:  # new schema
        margin = _last(data, f"Constraint/margin/{name}")
        dk = _last(data, f"Constraint/d_k/{name}")
    if margin is None or dk is None or dk <= 0:
        return False
    return margin <= 0.015 * dk


def _check_doraemon_ess_low(data):
    """Detect DORAEMON ESS ratio dropping below threshold."""
    ess = _last(data, "DORAEMON/ess_ratio")
    return ess is not None and ess < 0.05


def _check_velocity_spinout(data):
    """Detect frequent angular velocity threshold violations."""
    v = _last(data, "Episode_Termination/too_fast_ang")
    return v is not None and v > 0.5


def _check_thruster_saturation(data):
    """Detect thrusters near saturation (max utilization > 0.95)."""
    v = _last(data, "Thruster/utilization_max")
    return v is not None and v > 0.95


def _check_gradient_misalignment(data):
    """Detect encoder vanilla gradient opposing natural gradient."""
    cos = _last(data, "GradDecomp/enc_cos_vanilla_natgrad")
    return cos is not None and cos < -0.3


def _check_too_fast_termination(data):
    """Detect high termination from velocity violations (if still used)."""
    term = _last(data, "Episode_Termination/terminated")
    fast_ang = _last(data, "Episode_Termination/too_fast_ang")
    return (term is not None and term > 0.5
            and fast_ang is not None and fast_ang > 0.8)


DIAGNOSIS_PATTERNS = [
    (
        lambda a, _d: "Policy/entropy" in a and "Policy/mean_noise_std" in a,
        "Entropy collapse + low noise -> exploration dead. Check min_std floor and entropy_coef."
    ),
    (
        lambda a, _d: "Encoder/z_min" in a or "Encoder/z_max" in a,
        "Encoder z saturated at boundaries. Check weight_decay and encoder architecture."
    ),
    (
        lambda a, _d: "Encoder/grad_norm" in a,
        "Encoder gradient dead. Encoder not learning. Check max_encoder_kl gating or encoder_lr."
    ),
    (
        lambda a, _d: "Policy/line_search_success" in a,
        "TRPO line search failing. Cost gradient may dominate. Check barrier_t and constraint budgets."
    ),
    (
        lambda _a, d: _check_arm_frozen(d),
        "Arm frozen: low joint velocity + small actions. Constraint budgets may suppress movement."
    ),
    (
        lambda _a, d: _check_reward_plateau(d),
        "Reward plateaued in last 30% of training. May need DORAEMON curriculum or constraint relaxation."
    ),
    (
        lambda a, _d: "Policy/mean_noise_std" in a and a["Policy/mean_noise_std"] == "CEILING",
        "noise_std at ceiling -> entropy bonus too strong. Reduce entropy_coef."
    ),
    (
        lambda _a, d: _check_cost_divergence(d),
        "Cost returns diverging in latter half of training. "
        "Barrier margin at floor. Check constraint budgets."
    ),
    (
        lambda _a, d: _check_all_quarters_declining(d),
        "Reward declining in all 4 quarters. Training diverged."
    ),
    (
        lambda _a, d: _check_early_convergence(d),
        "Reward converged early (Q1-Q2) then plateaued. DORAEMON may be expanding DR too slowly."
    ),
    (
        lambda _a, d: _check_barrier_spikes(d),
        "Barrier penalty spikes (>0.1): barrier gradient overwhelms reward at small margins. "
        "Consider increasing barrier_t or relaxing constraint budgets."
    ),
    (
        lambda _a, d: _check_doraemon_ess_low(d),
        "DORAEMON ESS ratio < 5%: importance sampling quality degraded. "
        "DR distribution may have drifted too far from training distribution."
    ),
    # constrained_full_albc specific
    (
        lambda _a, d: _check_velocity_spinout(d),
        "Angular velocity frequently exceeding threshold (too_fast_ang > 50%). "
        "Check init_noise_std -- Hero Agent TAM yaw coupling causes spin-out at high std."
    ),
    (
        lambda _a, d: _check_thruster_saturation(d),
        "Thruster near saturation (utilization_max > 0.95). Policy using maximum thrust frequently. "
        "Check if wrench commands are too aggressive or init_noise_std too high."
    ),
    (
        lambda _a, d: _check_gradient_misalignment(d),
        "Encoder gradient opposes natural gradient (cos < -0.3). "
        "Trust region may be distorting encoder updates. Check cg_damping and encoder_lr."
    ),
    (
        lambda _a, d: _check_too_fast_termination(d),
        "Most terminations from angular velocity (too_fast_ang > 80%). Death spiral likely: "
        "all-negative rewards make early death optimal. Consider removing velocity termination "
        "or lowering init_noise_std."
    ),
]

# ==================================================================
# 5. TIER FORMATTERS
# ==================================================================

def format_tier1(data):
    """Core health metrics. Always shown."""
    lines = []
    n_iters = len(data.get("Train/mean_reward", []))
    last_step = data["Train/mean_reward"][-1][0] if n_iters else 0
    lines.append(f"  iters={n_iters}  last_step={last_step}")

    roll_tag = _resolve(data, "Attitude/roll_deg", "Attitude_Error/roll_deg")
    pitch_tag = _resolve(data, "Attitude/pitch_deg", "Attitude_Error/pitch_deg")

    metrics = [
        ("reward",     "Train/mean_reward"),
        ("ep_len",     "Train/mean_episode_length"),
        ("roll_err",   roll_tag),
        ("pitch_err",  pitch_tag),
        ("entropy",    "Policy/entropy"),
        ("noise_std",  "Policy/mean_noise_std"),
        ("ent_bonus",  "Policy/entropy_bonus"),
        ("z_mean",     "Encoder/z_mean"),
        ("z_std",      "Encoder/z_std"),
        ("z_range",    None),
        ("enc_grad",   "Encoder/grad_norm"),
        ("ls_success", "Policy/line_search_success"),
        ("lr",         "Loss/learning_rate"),
        ("too_fast_a", "Episode_Termination/too_fast_ang"),
        ("too_fast_l", "Episode_Termination/too_fast_lin"),
    ]

    anomaly_tags = {}
    for name, tag in metrics:
        if name == "z_range":
            zmin = _last(data, "Encoder/z_min")
            zmax = _last(data, "Encoder/z_max")
            if zmin is not None:
                a1 = ANOMALY_RULES.get("Encoder/z_min", lambda v: "")(zmin)
                a2 = ANOMALY_RULES.get("Encoder/z_max", lambda v: "")(zmax)
                alert = "SAT" if (a1 or a2) else ""
                lines.append(f"  {name:12s} [{_fmt(zmin)}, {_fmt(zmax)}]       {alert}")
                if a1:
                    anomaly_tags["Encoder/z_min"] = a1
                if a2:
                    anomaly_tags["Encoder/z_max"] = a2
            continue

        v = _last(data, tag)
        if v is None:
            continue
        arrows = _quartile_arrow_str(data, tag)
        alert = ANOMALY_RULES.get(tag, lambda v: "")(v)
        lines.append(f"  {name:12s} {_fmt(v):>8s} {arrows} {alert}")
        if alert:
            anomaly_tags[tag] = alert

    return lines, anomaly_tags


def format_tier2(data):
    """Constraints + TRPO + DORAEMON + dynamics."""
    lines = []

    # Constraints (dual-schema: old cost_return_ tags or new margin//viol//d_k/ tags)
    constraint_names = _constraint_names(data)

    violations = []
    diverging_costs = _find_diverging_costs(data)
    if constraint_names:
        lines.append("[TIER 2] Constraints")
        for name in constraint_names:
            cost_series, dk = _constraint_series(data, name)
            cr = cost_series[-1] if cost_series else None
            margin = _last(data, f"Constraint/barrier_margin_{name}")
            if margin is None:
                margin = _last(data, f"Constraint/margin/{name}")
            if cr is not None and dk is not None and dk > 0:
                arrow, divg_alert = _cost_trend_late_series(cost_series)
                floor_alert = "FLOOR" if _margin_at_floor(data, name) else ""
                violated = "OVER" if cr > dk else ""
                ratio = cr / dk
                inert_alert = "INERT" if ratio < 0.20 else ("LOOSE" if ratio > 0.80 and not violated else "")
                alerts = " ".join(filter(None, [violated, divg_alert, floor_alert, inert_alert]))
                margin_str = _fmt(margin) if margin is not None else "N/A"
                lines.append(
                    f"  {name:16s} cr={_fmt(cr):>7s} dk={_fmt(dk):>7s} c/dk={ratio:>5.0%} m={margin_str:>7s} {arrow} {alerts}"
                )
                if violated:
                    violations.append(name)
            elif margin is not None:
                # new schema without logged d_k: only raw margin/viol available
                viol = _last(data, f"Constraint/viol/{name}")
                viol_str = _fmt(viol) if viol is not None else "N/A"
                lines.append(f"  {name:16s} m={_fmt(margin):>7s} viol={viol_str:>7s} (no d_k logged)")
            elif cr is not None:
                lines.append(f"  {name:16s} cr={_fmt(cr):>7s}")

        bp_vals = _values(data, "Constraint/barrier_penalty")
        if bp_vals:
            bp_last = bp_vals[-1]
            bp_max = max(bp_vals)
            bp_spikes = sum(1 for v in bp_vals if v > 0.01)
            lines.append(
                f"  barrier_penalty  last={_fmt(bp_last, 4)}  spikes(>0.01)={bp_spikes}  max={_fmt(bp_max, 3)}"
            )

        if diverging_costs:
            lines.append(f"  ** {len(diverging_costs)} costs diverging: {', '.join(diverging_costs)}")

        achieved, loose = _find_inert_constraints(data)
        if achieved or loose:
            n_inert = len(achieved) + len(loose)
            lines.append(
                f"  ** {n_inert}/{len(constraint_names)} constraints inert (not shaping learning): "
                f"{len(achieved)} achieved (c/dk<20%), {len(loose)} loose-budget (c/dk>80%, no breach)"
            )

    # TRPO Step Quality
    trpo_metrics = [
        ("shs",        "TRPO/shs"),
        ("step_norm",  "TRPO/step_norm"),
        ("grad_norm",  "TRPO/grad_norm"),
        ("backtracks", "TRPO/line_search_backtracks"),
        ("val_grad",   "TRPO/value_grad_norm"),
        ("enc_grad",   "TRPO/encoder_grad_norm"),
    ]
    trpo_parts = []
    for name, tag in trpo_metrics:
        v = _last(data, tag)
        if v is not None:
            trpo_parts.append(f"{name}={_fmt(v)}")
    if trpo_parts:
        lines.append("[TIER 2] TRPO Step Quality")
        for i in range(0, len(trpo_parts), 3):
            lines.append("  " + "  ".join(trpo_parts[i:i + 3]))

    # DORAEMON DR Curriculum
    doraemon_metrics = [
        ("success",   "DORAEMON/success_rate"),
        ("entropy",   "DORAEMON/entropy"),
        ("ess_ratio", "DORAEMON/ess_ratio"),
        ("mode",      "DORAEMON/mode"),
        ("reverted",  "DORAEMON/reverted"),
    ]
    dor_parts = []
    for name, tag in doraemon_metrics:
        v = _last(data, tag)
        if v is not None:
            dor_parts.append(f"{name}={_fmt(v)}")
    if dor_parts:
        lines.append("[TIER 2] DORAEMON")
        lines.append("  " + "  ".join(dor_parts))
        # Entropy trend (expanding vs contracting DR distribution)
        ent_arrow = _quartile_arrow_str(data, "DORAEMON/entropy")
        sr = _last(data, "DORAEMON/success_rate")
        if sr is not None:
            sr_arrow = _quartile_arrow_str(data, "DORAEMON/success_rate")
            lines.append(f"  entropy_trend={ent_arrow.strip()}  success_trend={sr_arrow.strip()}")

    # Gradient Decomposition (constrained_full_albc)
    grad_decomp = [
        ("enc_van",     "GradDecomp/enc_vanilla_norm"),
        ("enc_nat",     "GradDecomp/enc_natgrad_norm"),
        ("enc_step",    "GradDecomp/enc_step_norm"),
        ("act_van",     "GradDecomp/actor_vanilla_norm"),
        ("act_nat",     "GradDecomp/actor_natgrad_norm"),
        ("act_step",    "GradDecomp/actor_step_norm"),
        ("enc_cos_vn",  "GradDecomp/enc_cos_vanilla_natgrad"),
        ("enc_cos_vs",  "GradDecomp/enc_cos_vanilla_step"),
    ]
    gd_parts = []
    for name, tag in grad_decomp:
        v = _last(data, tag)
        if v is not None:
            gd_parts.append(f"{name}={_fmt(v)}")
    if gd_parts:
        lines.append("[TIER 2] Gradient Decomposition")
        for i in range(0, len(gd_parts), 4):
            lines.append("  " + "  ".join(gd_parts[i:i + 4]))

    # Velocity Tracking (constrained_full_albc per-axis)
    vel_track = [
        ("lin_x",   "Vel_Tracking/lin_err_x"),
        ("lin_y",   "Vel_Tracking/lin_err_y"),
        ("lin_z",   "Vel_Tracking/lin_err_z"),
        ("ang_r",   "Vel_Tracking/ang_err_roll"),
        ("ang_p",   "Vel_Tracking/ang_err_pitch"),
        ("ang_y",   "Vel_Tracking/ang_err_yaw"),
        ("lin_norm", "Vel_Tracking/lin_vel_err_norm"),
        ("ang_norm", "Vel_Tracking/ang_vel_err_norm"),
    ]
    vt_parts = []
    for name, tag in vel_track:
        v = _last(data, tag)
        if v is not None:
            vt_parts.append(f"{name}={_fmt(v)}")
    if vt_parts:
        lines.append("[TIER 2] Velocity Tracking")
        for i in range(0, len(vt_parts), 4):
            lines.append("  " + "  ".join(vt_parts[i:i + 4]))

    # Thruster Diagnostics (constrained_full_albc)
    thr = [
        ("thr_mean", "Thruster/utilization_mean"),
        ("thr_max",  "Thruster/utilization_max"),
        ("thr_std",  "Thruster/utilization_std"),
    ]
    thr_parts = []
    for name, tag in thr:
        v = _last(data, tag)
        if v is not None:
            thr_parts.append(f"{name}={_fmt(v)}")
    if thr_parts:
        lines.append("[TIER 2] Thruster")
        lines.append("  " + "  ".join(thr_parts))

    # Dynamics (with environment-resolved action tags)
    arm_norm = _resolve(data, "Action/arm_norm", "Action/size_mean")
    arm_rate = _resolve(data, "Action/arm_rate", "Action/rate_mean")
    dyn = [
        ("arm_act",  arm_norm),
        ("arm_rate", arm_rate),
        ("thr_act",  "Action/thruster_norm"),
        ("thr_rate", "Action/thruster_rate"),
        ("jnt_vel",  "Dynamics/joint_vel_abs_max"),
        ("jnt_osc",  "Dynamics/joint_oscillation_hf_rms"),
        ("jnt_pos",  "Dynamics/joint_pos_mean_abs"),
        ("eff_sat",  "Dynamics/effort_saturation_frac"),
        ("vel_sat",  "Dynamics/vel_saturation_frac"),
        ("av_rp",    "Dynamics/angular_velocity_rp_rms"),
        ("av_yaw",   "Dynamics/angular_velocity_yaw_rms"),
    ]

    parts = []
    for name, tag in dyn:
        v = _last(data, tag)
        if v is not None:
            parts.append(f"{name}={_fmt(v)}")

    if parts:
        lines.append("[TIER 2] Dynamics")
        for i in range(0, len(parts), 4):
            lines.append("  " + "  ".join(parts[i:i + 4]))

    return lines, violations


def format_tier3(data):
    """DR, losses, termination, rewards, performance."""
    lines = []

    sections = {
        "[TIER 3] DR": [
            ("buoy_F",  "DR/buoyancy_force_mean"),
            ("I_roll",  "DR/inertia_roll_mean"),
            ("I_pitch", "DR/inertia_pitch_mean"),
            ("payload", "DR/payload_mass_mean"),
            ("current", "DR/ocean_current_mag_mean"),
        ],
        "[TIER 3] Losses": [
            ("value",     "Loss/value_function"),
            ("cost_val",  "Loss/cost_value"),
            ("kl",        "Loss/kl"),
        ],
        "[TIER 3] Termination": [
            ("terminated", "Episode_Termination/terminated"),
            ("timeout",    "Episode_Termination/time_out"),
            ("tilt",       "Episode_Termination/excessive_tilt"),
            ("bad_state",  "Episode_Termination/bad_state"),
            ("fast_ang",   "Episode_Termination/too_fast_ang"),
            ("fast_lin",   "Episode_Termination/too_fast_lin"),
        ],
    }

    # Auto-discover Episode Reward terms from TB tags
    ep_reward_tags = sorted(t for t in data if t.startswith("Episode_Reward/"))
    if ep_reward_tags:
        sections["[TIER 3] Rewards"] = [
            (tag.split("/")[-1], tag) for tag in ep_reward_tags
        ]

    # DORAEMON sensitivity (auto-discover from TB tags)
    dor_sens = sorted(t for t in data if t.startswith("DORAEMON/sensitivity/"))
    if dor_sens:
        sens_items = []
        for tag in dor_sens:
            v = _last(data, tag)
            if v is not None:
                name = tag.replace("DORAEMON/sensitivity/", "")
                sens_items.append((name, v))
        if sens_items:
            sections["[TIER 3] DORAEMON Sensitivity"] = [
                (name, tag) for tag, name in [(t, t.replace("DORAEMON/sensitivity/", "")) for t in dor_sens]
            ]

    for section_name, metrics in sections.items():
        parts = []
        for name, tag in metrics:
            v = _last(data, tag)
            if v is not None:
                parts.append(f"{name}={_fmt(v)}")
        if parts:
            lines.append(section_name)
            for i in range(0, len(parts), 4):
                lines.append("  " + "  ".join(parts[i:i + 4]))

    fps = _last(data, "Perf/total_fps")
    ep_len = _last(data, "Train/mean_episode_length")
    if fps or ep_len:
        parts = []
        if fps:
            parts.append(f"fps={_fmt(fps, 0)}")
        if ep_len:
            parts.append(f"ep_len={_fmt(ep_len, 0)}")
        lines.append("[TIER 3] Perf  " + "  ".join(parts))

    return lines


def format_diagnosis(anomaly_tags, data):
    """Auto-diagnose based on anomaly patterns and data patterns.

    Always runs: checks both anomaly_tags (from tier 1) and data patterns
    (reward plateau, cost divergence, etc.) regardless of whether anomalies exist.
    """
    findings = []
    for check_fn, message in DIAGNOSIS_PATTERNS:
        try:
            if check_fn(anomaly_tags, data):
                findings.append(message)
        except Exception:
            pass

    if not findings:
        return []

    lines = ["[DIAGNOSIS]"]
    for i, f in enumerate(findings, 1):
        lines.append(f"  {i}. {f}")
    return lines


# ==================================================================
# 6. DEEP ANALYSIS
# ==================================================================

def format_deep(data):
    """Time-series analysis for key metrics. Requires --deep flag.

    Uses detect_plateau instead of fit_convergence for more robust results.
    """
    lines = []
    for label, tag, _increasing in _resolve_full_analysis_metrics(data):
        vals = _values(data, tag)
        if not vals:
            continue
        arr = np.array(vals, dtype=np.float64)
        summary = tslib.summarize(arr)

        lines.append(f"[TRENDS] {label}")

        if summary["phase"]:
            lines.append(f"  phase: {summary['phase']}")

        # Oscillation detection (shown before plateau)
        osc = summary.get("oscillation")
        if osc and osc.get("oscillating"):
            osc_parts = [f"period={_fmt(osc['period'], 0)}"]
            osc_parts.append(f"amplitude={_fmt(osc['amplitude'], 2)}")
            osc_parts.append(f"trend={osc['amplitude_trend']}")
            lines.append(f"  OSCILLATING: {', '.join(osc_parts)}")

        # Plateau detection (replaces convergence fit)
        plateau = summary.get("plateau")
        if plateau:
            if plateau["plateaued"]:
                lines.append(f"  plateau: YES since ~{plateau['since_pct']:.0f}%")
            else:
                lines.append(f"  plateau: NO (slope_norm={plateau['last_slope_norm']:.3f})")

        if summary["final_cv"] is not None:
            lines.append(f"  stability: cv={_fmt(summary['final_cv'], 3)} ({summary['stability']})")

        if summary["changepoints"]:
            steps = [s for s, _ in data[tag]]
            cp_iters = []
            for cp in summary["changepoints"]:
                idx = min(cp, len(steps) - 1)
                cp_iters.append(str(steps[idx]))
            lines.append(f"  changepoints: iter {', '.join(cp_iters)}")

    return lines


# ==================================================================
# 6b. MULTI-METRIC DEEP ANALYSIS (PELT, Lag Analysis, HMM)
# ==================================================================

_SKIP_PREFIXES = ("Perf/", "Episode_Termination/", "Episode_Reward/")

def _build_diagnostic_panels(data):
    """Build diagnostic panels dynamically based on available TB tags.

    Returns list of (title, [(tag, label, color), ...], dual_y).
    Constraint panels are auto-discovered from Constraint/cost_return_* tags.
    Action panels adapt to hero_agent (size_mean) vs constrained_full_albc (arm_norm).
    """
    colors6 = ["tab:blue", "tab:orange", "tab:green", "tab:red", "tab:purple", "tab:brown"]
    panels = []

    # --- Exploration ---
    panels.append(("Exploration Health", [
        ("Policy/mean_noise_std", "noise_std", "tab:blue"),
        ("Policy/entropy", "entropy", "tab:orange"),
    ], True))

    # --- Encoder ---
    panels.append(("Encoder z Distribution", [
        ("Encoder/z_min", "z_min", "tab:blue"),
        ("Encoder/z_max", "z_max", "tab:orange"),
        ("Encoder/z_mean", "z_mean", "tab:green"),
    ], False))
    panels.append(("Encoder Learning", [
        ("Encoder/grad_norm", "enc_grad", "tab:blue"),
        ("TRPO/encoder_grad_norm", "enc_clip_grad", "tab:orange"),
    ], True))

    # --- Constraints (dynamic: auto-discover from TB tags) ---
    cr_tags = sorted(t for t in data if t.startswith("Constraint/cost_return_"))
    if cr_tags:
        cr_metrics = []
        for i, tag in enumerate(cr_tags[:6]):
            name = tag.split("cost_return_")[1]
            cr_metrics.append((tag, f"cr_{name}", colors6[i % len(colors6)]))
        panels.append(("Constraint Costs vs Budget", cr_metrics, False))

    margin_tags = sorted(t for t in data if t.startswith("Constraint/barrier_margin_"))
    if margin_tags:
        m_metrics = []
        for i, tag in enumerate(margin_tags[:5]):
            name = tag.split("barrier_margin_")[1]
            m_metrics.append((tag, f"m_{name}", colors6[i % len(colors6)]))
        m_metrics.append(("Constraint/barrier_penalty", "barrier_pen", "tab:red"))
        panels.append(("Constraint Margins + Barrier", m_metrics, False))

    # --- Action (env-aware) ---
    arm_act = _resolve(data, "Action/arm_norm", "Action/size_mean")
    arm_rate = _resolve(data, "Action/arm_rate", "Action/rate_mean")
    action_metrics = [
        (arm_act, arm_act.split("/")[-1], "tab:blue"),
        (arm_rate, arm_rate.split("/")[-1], "tab:orange"),
    ]
    if "Action/thruster_norm" in data:
        action_metrics.append(("Action/thruster_norm", "thruster_norm", "tab:green"))
        action_metrics.append(("Action/thruster_rate", "thruster_rate", "tab:red"))
    panels.append(("Action", action_metrics, len(action_metrics) == 2))

    # --- Thruster (constrained_full_albc) ---
    if "Thruster/utilization_mean" in data:
        panels.append(("Thruster Utilization", [
            ("Thruster/utilization_mean", "util_mean", "tab:blue"),
            ("Thruster/utilization_max", "util_max", "tab:orange"),
            ("Thruster/utilization_std", "util_std", "tab:green"),
        ], False))

    # --- Dynamics ---
    panels.append(("Dynamics", [
        ("Dynamics/angular_velocity_rp_rms", "av_rp_rms", "tab:blue"),
        ("Dynamics/joint_vel_abs_max", "jnt_vel_max", "tab:orange"),
        ("Dynamics/effort_saturation_frac", "effort_sat", "tab:green"),
    ], False))

    # --- Velocity Tracking (constrained_full_albc per-axis) ---
    if "Vel_Tracking/lin_err_x" in data:
        panels.append(("Velocity Tracking (Linear)", [
            ("Vel_Tracking/lin_err_x", "surge_err", "tab:blue"),
            ("Vel_Tracking/lin_err_y", "sway_err", "tab:orange"),
            ("Vel_Tracking/lin_err_z", "heave_err", "tab:green"),
        ], False))
        panels.append(("Velocity Tracking (Angular)", [
            ("Vel_Tracking/ang_err_roll", "roll_rate_err", "tab:blue"),
            ("Vel_Tracking/ang_err_pitch", "pitch_rate_err", "tab:orange"),
            ("Vel_Tracking/ang_err_yaw", "yaw_rate_err", "tab:green"),
        ], False))

    # --- TRPO ---
    panels.append(("TRPO Step Quality", [
        ("TRPO/step_norm", "step_norm", "tab:blue"),
        ("TRPO/grad_norm", "grad_norm", "tab:orange"),
    ], True))
    panels.append(("TRPO Line Search", [
        ("Policy/line_search_success", "ls_success", "tab:blue"),
        ("TRPO/line_search_backtracks", "backtracks", "tab:orange"),
    ], True))

    # --- Gradient Decomposition (constrained_full_albc) ---
    if "GradDecomp/enc_vanilla_norm" in data:
        panels.append(("Gradient Decomposition", [
            ("GradDecomp/enc_vanilla_norm", "enc_vanilla", "tab:blue"),
            ("GradDecomp/enc_natgrad_norm", "enc_natgrad", "tab:orange"),
            ("GradDecomp/enc_cos_vanilla_natgrad", "cos_v_ng", "tab:green"),
        ], False))

    # --- Value Losses ---
    panels.append(("Value Losses", [
        ("Loss/value_function", "value_loss", "tab:blue"),
        ("Loss/cost_value", "cost_value_loss", "tab:orange"),
    ], True))

    # --- DORAEMON ---
    panels.append(("DORAEMON Curriculum", [
        ("DORAEMON/success_rate", "success_rate", "tab:blue"),
        ("DORAEMON/entropy", "entropy", "tab:orange"),
    ], True))

    # --- DR ---
    panels.append(("Domain Randomization", [
        ("DR/inertia_roll_mean", "I_roll", "tab:blue"),
        ("DR/inertia_pitch_mean", "I_pitch", "tab:orange"),
        ("DR/payload_mass_mean", "payload", "tab:green"),
        ("DR/buoyancy_force_mean", "buoyancy", "tab:red"),
    ], False))

    # --- Encoder KL ---
    panels.append(("Encoder KL", [
        ("Policy/pre_encoder_kl", "pre_enc_kl", "tab:blue"),
        ("Loss/kl", "post_kl", "tab:orange"),
    ], True))

    # --- Termination (constrained_full_albc) ---
    if "Episode_Termination/too_fast_ang" in data:
        panels.append(("Termination Diagnostics", [
            ("Episode_Termination/terminated", "terminated", "tab:blue"),
            ("Episode_Termination/too_fast_ang", "too_fast_ang", "tab:orange"),
            ("Episode_Termination/too_fast_lin", "too_fast_lin", "tab:green"),
            ("Episode_Termination/excessive_tilt", "excessive_tilt", "tab:red"),
        ], False))

    return panels


# Legacy constant for backward compatibility
DIAGNOSTIC_PANELS = []


def resolve_analysis_targets(data, focus_patterns=None, auto_top_n=5):
    """Resolve metrics for deep analysis: default + auto-discovered + focused.

    Args:
        data: dict of {tag: [(step, value), ...]} from TensorBoard.
        focus_patterns: comma-separated tag substring patterns (e.g. "Encoder,joint").
        auto_top_n: number of auto-discovered metrics to add.

    Returns:
        (metrics, lag_pairs, auto_added, focus_added) where:
        - metrics: list of TB tags for PELT/HMM
        - lag_pairs: list of (tag_a, tag_b) for lag analysis
        - auto_added: list of (tag, score) auto-discovered
        - focus_added: list of tags matched by focus patterns
    """
    metrics = list(tslib.resolve_key_metrics(data))
    metrics_set = set(metrics)

    # Auto-discover interesting metrics (with cross-correlation dedup)
    ranked = tslib.rank_metrics_by_interest(data)
    auto_added = []
    # Cache value arrays for selected metrics to check cross-correlation
    selected_vals = {}
    for tag in metrics:
        if tag in data and len(data[tag]) >= 20:
            selected_vals[tag] = np.array([v for _, v in data[tag]], dtype=np.float64)
    for tag, score in ranked:
        if tag in metrics_set:
            continue
        if any(tag.startswith(p) for p in _SKIP_PREFIXES):
            continue
        # Dedup: skip if |correlation| > 0.85 with any already-selected metric
        if tag in data and len(data[tag]) >= 20:
            cand_vals = np.array([v for _, v in data[tag]], dtype=np.float64)
            redundant = False
            for sel_tag, sel_vals in selected_vals.items():
                nc = min(len(cand_vals), len(sel_vals))
                if nc >= 20:
                    try:
                        corr = abs(float(np.corrcoef(cand_vals[:nc], sel_vals[:nc])[0, 1]))
                        if np.isfinite(corr) and corr > 0.85:
                            redundant = True
                            break
                    except Exception:
                        pass
            if redundant:
                continue
            selected_vals[tag] = cand_vals
        metrics.append(tag)
        metrics_set.add(tag)
        auto_added.append((tag, score))
        if len(auto_added) >= auto_top_n:
            break

    # Focus-matching metrics
    focus_added = []
    if focus_patterns:
        patterns = [p.strip().lower() for p in focus_patterns.split(",") if p.strip()]
        for tag in sorted(data.keys()):
            if tag in metrics_set:
                continue
            if len(data[tag]) < 20:
                continue
            tag_lower = tag.lower()
            if any(p in tag_lower for p in patterns):
                metrics.append(tag)
                metrics_set.add(tag)
                focus_added.append(tag)

    # Build lag pairs: defaults (resolved) + new metrics paired with reward
    lag_pairs = list(tslib.resolve_lag_pairs(data))
    existing = set((a, b) for a, b in lag_pairs)
    existing.update((b, a) for a, b in lag_pairs)
    reward_tag = "Train/mean_reward"

    new_tags = [t for t, _ in auto_added] + focus_added
    for tag in new_tags:
        if tag == reward_tag:
            continue
        pair = (tag, reward_tag)
        if pair not in existing:
            lag_pairs.append(pair)
            existing.add(pair)
            existing.add((pair[1], pair[0]))

    return metrics, lag_pairs, auto_added, focus_added


def format_deep_multi(data, metrics=None, pairs=None):
    """Multi-metric cross-analysis. Requires --deep flag."""
    lines = []

    # 1. Multi-metric changepoints (PELT) with coincidence filter
    all_cps = tslib.multi_metric_changepoints(data)
    significant_groups = tslib.filter_coincident_changepoints(all_cps, tolerance=15)
    if significant_groups:
        lines.append("[CHANGEPOINTS] cross-metric (PELT, 2+ coincident only)")
        for group in significant_groups[:8]:
            iter_num = group[0][0]
            changes = ", ".join(f"{tag}({d})" for _, tag, d in group)
            n_metrics = len(set(tag for _, tag, _ in group))
            lines.append(f"  iter {iter_num:>5d}: [{n_metrics} metrics] {changes}")
    elif all_cps:
        lines.append("[CHANGEPOINTS] no coincident changes (all single-metric)")

    # 2. Lag analysis (replaces rolling correlation)
    lag_results = tslib.multi_metric_lag_analysis(data, pairs=pairs)
    if lag_results:
        sig_results = [r for r in lag_results if r["significant"]]
        lines.append("[LAG ANALYSIS] cross-metric lead-lag (first-differenced)")
        if sig_results:
            for r in sig_results:
                a, b = r["pair"]
                lag = r["best_lag"]
                corr = r["best_corr"]
                if lag > 0:
                    direction = f"{a} leads {b}"
                elif lag < 0:
                    direction = f"{b} leads {a}"
                else:
                    direction = "synchronous"
                lines.append(f"  {a:>20s} -> {b:<20s}  lag={lag:+d}  corr={corr:+.2f}  ({direction})")
        hidden = len(lag_results) - len(sig_results)
        if hidden > 0:
            lines.append(f"  ({hidden} pairs hidden: |corr| < 0.3)")

    # 3. HMM regime detection (with duration filter)
    regime_info = tslib.detect_regimes(data, metrics=metrics)
    if regime_info:
        n = regime_info["n_states"]
        valid = regime_info.get("valid_states", list(range(n)))
        if len(valid) <= 1:
            lines.append(f"[REGIMES] single regime (HMM fitted {n} states, {n - len(valid)} filtered: dur<5)")
        else:
            lines.append(f"[REGIMES] HMM ({len(valid)} valid of {n} states, dur<5 hidden)")
            for s in valid:
                means = regime_info["state_means"].get(s, {})
                dur = regime_info["state_durations"].get(s, 0)
                key_vals = []
                for m in ["mean_reward", "roll_deg", "pitch_deg", "barrier_penalty", "z_std"]:
                    if m in means:
                        key_vals.append(f"{m}={_fmt(means[m])}")
                state_line = f"  state {s}: dur={dur:.0f}  " + "  ".join(key_vals[:4])
                lines.append(state_line)
            trans = regime_info["transitions"]
            self_probs = [f"s{i}={trans[i][i]:.2f}" for i in valid]
            lines.append(f"  self-transition: {', '.join(self_probs)}")

    return lines


def generate_deep_plots(data, run_path, metrics=None, pairs=None,
                        auto_tags=None, focus_tags=None, focus_patterns_raw=None):
    """Generate PNG plots for deep analysis. Saves to {run_path}/analysis/."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_dir = Path(run_path) / "analysis"
    out_dir.mkdir(exist_ok=True)
    saved = []

    # Common: get steps for x-axis
    reward_data = data.get("Train/mean_reward", [])
    if not reward_data:
        return saved

    # Compute significant changepoints once (shared by Plot 1 and Plot 3)
    all_cps = tslib.multi_metric_changepoints(data)
    significant_groups = tslib.filter_coincident_changepoints(all_cps, tolerance=15)
    # Flatten to iteration set for vertical lines
    sig_iters = set()
    for group in significant_groups:
        sig_iters.add(group[0][0])

    # --- Plot 1: Key metrics + significant changepoints timeline ---
    # 5 panels: reward, roll, pitch, exploration (noise+entropy), barrier
    roll_tag = _resolve(data, "Attitude/roll_deg", "Attitude_Error/roll_deg")
    pitch_tag = _resolve(data, "Attitude/pitch_deg", "Attitude_Error/pitch_deg")
    fig, axes = plt.subplots(5, 1, figsize=(14, 12), sharex=True)
    plot_metrics = [
        ("Train/mean_reward", "Reward", axes[0]),
        (roll_tag, "Roll Error (deg)", axes[1]),
        (pitch_tag, "Pitch Error (deg)", axes[2]),
    ]
    for tag, label, ax in plot_metrics:
        if tag not in data:
            continue
        tag_steps = [s for s, _ in data[tag]]
        tag_vals = [v for _, v in data[tag]]
        ax.plot(tag_steps, tag_vals, linewidth=0.8, alpha=0.8)
        ax.set_ylabel(label, fontsize=9)
        ax.grid(True, alpha=0.3)
        for si in sig_iters:
            ax.axvline(si, color="red", linewidth=0.8, alpha=0.6, linestyle="--")

    # Panel 4: Exploration health (noise_std + entropy on dual y-axis)
    ax_expl = axes[3]
    if "Policy/mean_noise_std" in data:
        ns_steps = [s for s, _ in data["Policy/mean_noise_std"]]
        ns_vals = [v for _, v in data["Policy/mean_noise_std"]]
        ax_expl.plot(ns_steps, ns_vals, linewidth=0.8, alpha=0.8, color="tab:blue", label="noise_std")
        ax_expl.set_ylabel("noise_std", fontsize=9, color="tab:blue")
        ax_expl.tick_params(axis="y", labelcolor="tab:blue")
    if "Policy/entropy" in data:
        ent_steps = [s for s, _ in data["Policy/entropy"]]
        ent_vals = [v for _, v in data["Policy/entropy"]]
        ax_ent = ax_expl.twinx()
        ax_ent.plot(ent_steps, ent_vals, linewidth=0.8, alpha=0.8, color="tab:orange", label="entropy")
        ax_ent.set_ylabel("entropy", fontsize=9, color="tab:orange")
        ax_ent.tick_params(axis="y", labelcolor="tab:orange")
    ax_expl.grid(True, alpha=0.3)
    for si in sig_iters:
        ax_expl.axvline(si, color="red", linewidth=0.8, alpha=0.6, linestyle="--")

    # Panel 5: Barrier penalty
    if "Constraint/barrier_penalty" in data:
        bp_steps = [s for s, _ in data["Constraint/barrier_penalty"]]
        bp_vals = [v for _, v in data["Constraint/barrier_penalty"]]
        axes[4].plot(bp_steps, bp_vals, linewidth=0.8, alpha=0.8)
        axes[4].set_ylabel("Barrier Penalty", fontsize=9)
        axes[4].grid(True, alpha=0.3)
        for si in sig_iters:
            axes[4].axvline(si, color="red", linewidth=0.8, alpha=0.6, linestyle="--")

    axes[-1].set_xlabel("Iteration")
    fig.suptitle("Key Metrics + Significant Changepoints (2+ metrics coincident)", fontsize=11)
    fig.tight_layout()
    p = out_dir / "01_metrics_changepoints.png"
    fig.savefig(p, dpi=120)
    plt.close(fig)
    saved.append(str(p))

    # --- Plot 2: Lag heatmap ---
    lag_pairs_to_plot = pairs if pairs else tslib.LAG_PAIRS
    heatmap_data = []
    pair_labels = []
    max_lag = 30
    for tag_a, tag_b in lag_pairs_to_plot:
        if tag_a not in data or tag_b not in data:
            continue
        va = np.array([v for _, v in data[tag_a]], dtype=np.float64)
        vb = np.array([v for _, v in data[tag_b]], dtype=np.float64)
        n = min(len(va), len(vb))
        if n < max_lag * 2 + 10:
            continue
        profile = tslib.lag_profile(va[:n], vb[:n], max_lag=max_lag)
        if profile is not None:
            heatmap_data.append(profile)
            short_a = tag_a.split("/")[-1]
            short_b = tag_b.split("/")[-1]
            pair_labels.append(f"{short_a}\n-> {short_b}")

    if heatmap_data:
        heatmap_arr = np.array(heatmap_data)
        fig, ax = plt.subplots(figsize=(14, max(4, len(heatmap_data) * 0.6 + 1)))
        im = ax.imshow(heatmap_arr, aspect="auto", cmap="RdBu_r", vmin=-1, vmax=1,
                        extent=(-max_lag - 0.5, max_lag + 0.5, len(heatmap_data) - 0.5, -0.5))
        ax.set_yticks(range(len(pair_labels)))
        ax.set_yticklabels(pair_labels, fontsize=7)
        ax.set_xlabel("Lag (positive = X leads Y)")
        ax.axvline(0, color="black", linewidth=0.5, alpha=0.5)
        plt.colorbar(im, ax=ax, label="Correlation", shrink=0.8)
        fig.suptitle("Lead-Lag Cross-Correlation Heatmap (first-differenced)", fontsize=11)
        fig.tight_layout()
        p = out_dir / "02_lag_heatmap.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(str(p))

    # --- Plot 3: Segmented summary (PELT significant segments) ---
    if sig_iters and "Train/mean_reward" in data:
        reward_steps = [s for s, _ in data["Train/mean_reward"]]
        reward_vals = np.array([v for _, v in data["Train/mean_reward"]], dtype=np.float64)

        # Build segments from significant changepoint iterations
        boundaries = sorted(sig_iters)
        # Map iterations to indices
        step_arr = np.array(reward_steps)
        seg_indices = [0]
        for b in boundaries:
            idx = int(np.searchsorted(step_arr, b))
            if idx > seg_indices[-1] and idx < len(reward_vals):
                seg_indices.append(idx)
        seg_indices.append(len(reward_vals))

        if len(seg_indices) > 2:  # at least 2 segments
            # Compute means per segment for reward and errors
            seg_labels = []
            seg_reward = []
            seg_roll = []
            seg_pitch = []
            roll_vals = np.array(_values(data, roll_tag), dtype=np.float64) \
                if roll_tag in data else None
            pitch_vals = np.array(_values(data, pitch_tag), dtype=np.float64) \
                if pitch_tag in data else None

            for i in range(len(seg_indices) - 1):
                s, e = seg_indices[i], seg_indices[i + 1]
                seg_labels.append(f"{reward_steps[s]}-{reward_steps[min(e - 1, len(reward_steps) - 1)]}")
                seg_reward.append(float(reward_vals[s:e].mean()))
                if roll_vals is not None and e <= len(roll_vals):
                    seg_roll.append(float(roll_vals[s:e].mean()))
                if pitch_vals is not None and e <= len(pitch_vals):
                    seg_pitch.append(float(pitch_vals[s:e].mean()))

            n_plots = 1 + (1 if seg_roll else 0) + (1 if seg_pitch else 0)
            fig, axes = plt.subplots(n_plots, 1, figsize=(14, 3 * n_plots))
            if n_plots == 1:
                axes = [axes]

            x = np.arange(len(seg_labels))
            axes[0].bar(x, seg_reward, color="#4CAF50", alpha=0.8)
            axes[0].set_ylabel("Mean Reward")
            axes[0].set_xticks(x)
            axes[0].set_xticklabels(seg_labels, fontsize=7, rotation=30, ha="right")
            axes[0].grid(True, alpha=0.3, axis="y")

            pidx = 1
            if seg_roll:
                axes[pidx].bar(x[:len(seg_roll)], seg_roll, color="#FF9800", alpha=0.8)
                axes[pidx].set_ylabel("Mean Roll Error (deg)")
                axes[pidx].set_xticks(x[:len(seg_roll)])
                axes[pidx].set_xticklabels(seg_labels[:len(seg_roll)], fontsize=7, rotation=30, ha="right")
                axes[pidx].grid(True, alpha=0.3, axis="y")
                pidx += 1
            if seg_pitch:
                axes[pidx].bar(x[:len(seg_pitch)], seg_pitch, color="#2196F3", alpha=0.8)
                axes[pidx].set_ylabel("Mean Pitch Error (deg)")
                axes[pidx].set_xticks(x[:len(seg_pitch)])
                axes[pidx].set_xticklabels(seg_labels[:len(seg_pitch)], fontsize=7, rotation=30, ha="right")
                axes[pidx].grid(True, alpha=0.3, axis="y")

            fig.suptitle("Segmented Summary (split at significant changepoints)", fontsize=11)
            fig.tight_layout()
            p = out_dir / "03_segmented_summary.png"
            fig.savefig(p, dpi=120)
            plt.close(fig)
            saved.append(str(p))

    # --- Plot 4: Diagnostic subsystem panels ---
    # Dynamic panels covering distinct subsystems with dual y-axis.
    # When --focus is provided, append matching metrics as extra panels.
    panels = _build_diagnostic_panels(data)

    # Add focus-matched metrics as grouped panels (one panel per focus pattern)
    if focus_tags and focus_patterns_raw:
        covered = set()
        for _, metrics_list, _ in panels:
            for tag, _, _ in metrics_list:
                covered.add(tag)
        focus_colors = ["tab:purple", "tab:brown", "tab:pink", "tab:cyan",
                        "tab:olive", "tab:gray"]
        # Group tags by which focus pattern matched them
        patterns = [p.strip().lower() for p in focus_patterns_raw.split(",") if p.strip()]
        from collections import defaultdict
        pattern_groups = defaultdict(list)
        for tag in focus_tags:
            if tag not in data or tag in covered:
                continue
            tag_lower = tag.lower()
            for pat in patterns:
                if pat in tag_lower:
                    pattern_groups[pat].append(tag)
                    covered.add(tag)
                    break
        for pat, tags in pattern_groups.items():
            group_metrics = []
            for i, tag in enumerate(tags[:6]):  # max 6 lines per panel
                short = tag.rsplit("/", 1)[-1]
                color = focus_colors[i % len(focus_colors)]
                group_metrics.append((tag, short, color))
            panels.append((f"Focus: {pat}", group_metrics, False))

    # Filter to panels that have at least one available metric
    valid_panels = []
    for title, metrics_list, dual_y in panels:
        available = [(t, l, c) for t, l, c in metrics_list if t in data]
        if available:
            valid_panels.append((title, available, dual_y))

    if valid_panels:
        n_panels = len(valid_panels)
        panel_h = 2.0 if n_panels > 8 else 2.5
        fig, axes = plt.subplots(n_panels, 1, figsize=(14, panel_h * n_panels), sharex=True)
        if n_panels == 1:
            axes = [axes]

        for idx, (title, metrics_list, dual_y) in enumerate(valid_panels):
            ax = axes[idx]
            # Plot first metric on primary y-axis
            tag0, label0, color0 = metrics_list[0]
            steps0 = [s for s, _ in data[tag0]]
            vals0 = [v for _, v in data[tag0]]
            ax.plot(steps0, vals0, linewidth=0.8, alpha=0.8, color=color0, label=label0)
            ax.set_ylabel(label0, fontsize=8, color=color0)
            ax.tick_params(axis="y", labelcolor=color0)
            ax.grid(True, alpha=0.3)

            if dual_y and len(metrics_list) == 2:
                # Second metric on twin y-axis
                tag1, label1, color1 = metrics_list[1]
                steps1 = [s for s, _ in data[tag1]]
                vals1 = [v for _, v in data[tag1]]
                ax_twin = ax.twinx()
                ax_twin.plot(steps1, vals1, linewidth=0.8, alpha=0.8, color=color1, label=label1)
                ax_twin.set_ylabel(label1, fontsize=8, color=color1)
                ax_twin.tick_params(axis="y", labelcolor=color1)
            elif len(metrics_list) > 1:
                # Multiple metrics on same y-axis (e.g. constraint margins)
                for tag_i, label_i, color_i in metrics_list[1:]:
                    steps_i = [s for s, _ in data[tag_i]]
                    vals_i = [v for _, v in data[tag_i]]
                    ax.plot(steps_i, vals_i, linewidth=0.8, alpha=0.8, color=color_i, label=label_i)
                ax.legend(fontsize=7, loc="upper right")

            ax.set_title(title, fontsize=9, loc="left", pad=2)
            for si in sig_iters:
                ax.axvline(si, color="red", linewidth=0.6, alpha=0.5, linestyle="--")

        axes[-1].set_xlabel("Iteration")
        fig.suptitle("Diagnostic Panels (subsystem analysis)", fontsize=11)
        fig.tight_layout()
        p = out_dir / "04_diagnostic_panels.png"
        fig.savefig(p, dpi=120)
        plt.close(fig)
        saved.append(str(p))

    return saved


# ==================================================================
# 7. CLI & MAIN
# ==================================================================

def main():
    parser = argparse.ArgumentParser(description="Token-efficient training log analyzer")
    parser.add_argument("run_path", nargs="?", help="Run dir path or index (0=latest). Default: latest")
    parser.add_argument("--tier", type=int, choices=[1, 2, 3], default=0,
                        help="Detail level: 1=core, 2=+constraints, 3=all. 0=auto (1+2)")
    parser.add_argument("--last", type=int, default=0, help="Analyze only last N data points")
    parser.add_argument("--stride", type=int, default=0,
                        help="Subsample every N-th data point (preserves full time range)")
    parser.add_argument("--deep", action="store_true", help="Time-series analysis (phase, plateau, changepoints)")
    parser.add_argument("--focus", type=str, default=None,
                        help="Comma-separated tag patterns to focus on (e.g. 'Encoder,joint')")
    parser.add_argument("--list", action="store_true", help="List available runs")
    args = parser.parse_args()

    if args.list:
        runs = find_runs()
        if not runs:
            print("No runs found.")
            return
        for i, r in enumerate(runs[:20]):
            print(f"  [{i:2d}] {r.parent.name}/{r.name}")
        return

    # Resolve run path
    if args.run_path:
        run_path = Path(args.run_path)
        if not run_path.exists():
            try:
                idx = int(args.run_path)
                runs = find_runs()
                if idx >= len(runs):
                    print(f"ERROR: Index {idx} out of range ({len(runs)} runs)")
                    sys.exit(1)
                run_path = runs[idx]
            except ValueError:
                runs = find_runs()
                matches = [r for r in runs if args.run_path in str(r)]
                if matches:
                    run_path = matches[0]
                else:
                    print(f"ERROR: No run matching '{args.run_path}'")
                    sys.exit(1)
    else:
        runs = find_runs()
        if not runs:
            print("ERROR: No runs found in " + LOGS_ROOT)
            sys.exit(1)
        run_path = runs[0]

    # Header
    print(f"=== {run_path.parent.name}/{run_path.name} ===")

    # Config summary
    cfg = load_config(run_path)
    cfg_lines = format_config(cfg)
    for line in cfg_lines:
        print(line)

    # Load
    data = load_events(run_path)
    if not data:
        print("ERROR: No metrics found")
        sys.exit(1)

    # Fix constraint count: YAML stores runtime defaults (num_constraints=0),
    # actual count is auto-synced by runner. Infer from TB tags instead.
    yaml_num_c = cfg.get("_yaml_num_constraints")
    tb_constraint_tags = sorted(
        t for t in data if t.startswith("Constraint/cost_return_")
    )
    tb_num_c = len(tb_constraint_tags)
    if tb_num_c > 0 and (yaml_num_c is None or yaml_num_c == 0):
        tb_names = [t.split("cost_return_")[1] for t in tb_constraint_tags]
        print(f"  constraints={tb_num_c} (from TB: {', '.join(tb_names)})")

    # Filter by --stride (subsample every N-th point, preserves full time range)
    if args.stride > 1:
        for tag in data:
            data[tag] = data[tag][::args.stride]

    # Filter by --last
    if args.last > 0:
        for tag in data:
            data[tag] = data[tag][-args.last:]

    # --- Output order: TIER1 -> TIER2 -> DIAGNOSIS -> DEEP -> TIER3 ---

    # Tier 1 (always)
    print("[TIER 1] Core Health")
    t1_lines, anomaly_tags = format_tier1(data)
    status = f"  STATUS: {len(anomaly_tags)} ANOMALIES" if anomaly_tags else "  STATUS: HEALTHY"
    print(status)
    for line in t1_lines:
        print(line)

    # Tier 2 (auto or explicit)
    tier = args.tier if args.tier > 0 else 2
    violations = []
    if tier >= 2:
        t2_lines, violations = format_tier2(data)
        for line in t2_lines:
            print(line)

    # Diagnosis (always runs, checks both anomaly_tags AND data patterns)
    diag = format_diagnosis(anomaly_tags, data)
    for line in diag:
        print(line)

    # Deep analysis
    if args.deep:
        deep_lines = format_deep(data)
        for line in deep_lines:
            print(line)

        # Resolve analysis targets: default + auto-discovered + focused
        resolved_metrics, resolved_pairs, auto_added, focus_added = \
            resolve_analysis_targets(data, focus_patterns=args.focus)

        # Report what was auto-discovered and focused
        if auto_added or focus_added:
            print("[TARGETS] resolved analysis metrics")
            if auto_added:
                auto_strs = [f"{t.split('/')[-1]}({s:.2f})" for t, s in auto_added]
                print(f"  auto: {', '.join(auto_strs)}")
            if focus_added:
                focus_strs = [t.split("/")[-1] for t in focus_added]
                print(f"  focus: {', '.join(focus_strs)}")

        # Multi-metric deep analysis
        multi_lines = format_deep_multi(data, metrics=resolved_metrics,
                                        pairs=resolved_pairs)
        for line in multi_lines:
            print(line)

        # Generate PNG plots
        auto_tag_list = [t for t, _ in auto_added]
        saved_plots = generate_deep_plots(
            data, run_path, metrics=resolved_metrics, pairs=resolved_pairs,
            auto_tags=auto_tag_list, focus_tags=focus_added,
            focus_patterns_raw=args.focus,
        )
        if saved_plots:
            print(f"[PLOTS] {len(saved_plots)} plots saved:")
            for p in saved_plots:
                print(f"  {p}")

    # Tier 3 (explicit only)
    if tier >= 3:
        t3_lines = format_tier3(data)
        for line in t3_lines:
            print(line)


if __name__ == "__main__":
    main()
