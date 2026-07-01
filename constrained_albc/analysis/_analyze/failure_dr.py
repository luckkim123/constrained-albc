# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Per-env DR <-> failure join (pure numpy, Isaac-Sim-free).

Given an eval data dict (what data_<level>.npz holds: error_roll[T,N], dr_<name>[N],
warmup_steps), identify the worst-k envs by steady-state tracking error and test whether
their domain-randomization distribution is shifted vs the whole population.

This turns the encoder's correlational evidence (z-sweep: policy is sensitive to lateral
CoG/CoB + body mass) into env-level causal evidence (rule03 differential diagnosis at the
env level): if the worst-roll envs systematically received larger dr_cog_y, that is direct
evidence the CoG disturbance — not training length or a generic DR knob — drives the roll
failure.

The transform is axis-generic: roll is the teacher's single weakness and the default, but
the same join runs on pitch / lin_vel / yaw by changing ``axis``.
"""
from __future__ import annotations

import numpy as np

# axis -> the error key(s) in the data dict whose post-warmup |.| is the SS error.
_AXIS_KEYS: dict[str, tuple[str, ...]] = {
    "roll": ("error_roll",),
    "pitch": ("error_pitch",),
    "att_norm": ("error_roll", "error_pitch"),
}


def _ss_window_start(t: int, data: dict) -> int:
    """First time index of the steady-state window (after warmup; fallback last 50%).

    ``t`` is the time length of the axis being analyzed, so the window is consistent with
    that axis's own array rather than a sibling that may differ in length.
    """
    if t <= 0:
        return 0
    warmup = int(data.get("warmup_steps", 0) or 0)
    # Guard against a warmup that swallows the whole rollout.
    return warmup if 0 <= warmup < t else t // 2


def per_env_ss_error(data: dict, axis: str = "roll") -> np.ndarray:
    """Per-env steady-state error [N]: mean |error| over the post-warmup window.

    For ``att_norm`` the roll/pitch errors are combined as sqrt(roll^2 + pitch^2) per
    step before averaging. Dead (terminated) steps are excluded when a termination mask
    is present, so a crashed env's frozen error does not dilute the mean.
    """
    keys = _AXIS_KEYS.get(axis)
    if keys is None:
        raise ValueError(f"unknown axis {axis!r}; known: {sorted(_AXIS_KEYS)}")
    present = [np.abs(np.asarray(data[k], dtype=np.float64)) for k in keys if k in data]
    if not present:
        raise KeyError(f"axis {axis!r} needs {keys}, none present in data")

    start = _ss_window_start(present[0].shape[0], data)
    comps = [c[start:] for c in present]
    err = np.sqrt(sum(c**2 for c in comps)) if len(comps) > 1 else comps[0]  # (Tw, N)

    term = data.get("terminated")
    if term is not None:
        alive = ~np.asarray(term, dtype=bool)[start : start + err.shape[0]]
        if alive.shape == err.shape:
            err = np.where(alive, err, np.nan)

    with np.errstate(invalid="ignore"):
        ss = np.nanmean(err, axis=0)
    # An env dead for the entire window -> all-nan -> treat as worst (inf), not dropped.
    return np.where(np.isfinite(ss), ss, np.inf)


def failing_env_mask(ss_per_env: np.ndarray, k: int = 10) -> np.ndarray:
    """Boolean mask [N] selecting the k envs with the largest steady-state error."""
    n = ss_per_env.shape[0]
    k = min(k, n)
    mask = np.zeros(n, dtype=bool)
    if k > 0:
        worst = np.argsort(ss_per_env)[-k:]
        mask[worst] = True
    return mask


def _point_biserial(indicator: np.ndarray, values: np.ndarray) -> float:
    """Correlation between a 0/1 failing indicator and a continuous DR value.

    Equivalent to Pearson correlation with a binary variable; 0 when the DR has no
    spread (a constant channel like a none-level nominal).
    """
    v = np.asarray(values, dtype=np.float64)
    if np.nanstd(v) < 1e-12:
        return 0.0
    ind = indicator.astype(np.float64)
    if np.std(ind) < 1e-12:
        return 0.0
    c = np.corrcoef(ind, v)[0, 1]
    return float(c) if np.isfinite(c) else 0.0


# Per-env channel prefixes joined against failure. ``dr_`` = domain randomization (the
# intended distribution), ``fault_`` = injected actuator/sensor faults (the FTC signal).
# They are kept in SEPARATE rankings so a fault is never out-ranked and hidden by a dr
# channel — fault-tolerant control needs the fault correlation surfaced on its own.
_VALUE_PREFIXES: tuple[str, ...] = ("dr_", "fault_")


def _rank_by_prefix(data: dict, prefix: str, mask: np.ndarray, ss: np.ndarray) -> list[dict]:
    """Rank every ``<prefix><name>[N]`` channel by |corr| with the failing-env indicator.

    Prefix-agnostic: the join math is identical for dr_ and fault_; only the key prefix
    differs. Channels whose length does not match the env count are skipped (not a per-env
    array). Returns the per-channel records sorted by descending |correlation|.
    """
    indicator = mask.astype(np.float64)
    keys = sorted(key for key in data if key.startswith(prefix))
    ranking = []
    for name in keys:
        vals = np.asarray(data[name], dtype=np.float64).reshape(-1)
        if vals.shape[0] != ss.shape[0]:
            continue  # mismatched length -> not a per-env array; skip
        corr = _point_biserial(indicator, vals)
        fail_mean = float(np.nanmean(vals[mask])) if mask.any() else float("nan")
        pop_mean = float(np.nanmean(vals))
        ranking.append({
            "name": name,
            "correlation": corr,
            "failing_mean": fail_mean,
            "population_mean": pop_mean,
            "shift": fail_mean - pop_mean,
        })
    ranking.sort(key=lambda r: abs(r["correlation"]), reverse=True)
    return ranking


def join_failure_dr(
    data: dict, axis: str = "roll", k: int = 10, prefixes: tuple[str, ...] = _VALUE_PREFIXES
) -> dict:
    """Join worst-k envs against every per-env channel; rank each prefix separately.

    For each prefix in ``prefixes`` (default ``dr_`` and ``fault_``) the worst-k failing
    envs are correlated against that prefix's channels, producing a ``<p>_ranking`` list
    keyed by the prefix sans trailing underscore (``dr_`` -> ``dr_ranking``,
    ``fault_`` -> ``fault_ranking``). Each record is (name, correlation, failing_mean,
    population_mean, shift) sorted by descending |correlation|; the top entry is the
    channel most associated with failure. A prefix with no matching channels yields an
    empty list, so a dr-only or fault-only npz is handled without fabricating keys.
    """
    ss = per_env_ss_error(data, axis=axis)
    mask = failing_env_mask(ss, k=k)

    out: dict = {
        "axis": axis,
        "k": int(min(k, ss.shape[0])),
        "n_failing": int(mask.sum()),
    }
    for prefix in prefixes:
        out[f"{prefix.rstrip('_')}_ranking"] = _rank_by_prefix(data, prefix, mask, ss)
    return out


def analyze_failure_dr_levels(all_data: dict[str, dict], axis: str = "roll", k: int = 10) -> dict:
    """Run the join for every DR level PRESENT in ``all_data`` (keys, not a static list).

    Each level's result carries both a ``dr_ranking`` and a ``fault_ranking`` (see
    ``join_failure_dr``), so dr and injected faults are surfaced side by side per level.
    Deriving levels from the data keys is deliberate: the audit found eval_plots filters
    against a static DR_LEVELS that omits ``ood`` (P2 bug). Here a 3-level run, or an
    ood-included run, is handled by whatever levels actually carry error data. A level
    without the axis's error arrays is skipped, not fabricated.
    """
    out: dict = {"axis": axis, "k": k, "levels": {}}
    for level, data in all_data.items():
        if not any(key in data for key in _AXIS_KEYS.get(axis, ())):
            continue  # this level has no error data for the axis -> skip
        out["levels"][level] = join_failure_dr(data, axis=axis, k=k)
    return out


def _strip_value_prefix(name: str) -> str:
    """Strip the leading dr_/fault_ namespace from a channel name for a plot label."""
    for prefix in _VALUE_PREFIXES:
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def build_failure_dr_plot_data(join_result: dict, top_n: int = 8, ranking_key: str = "dr_ranking") -> dict:
    """Shape a single-level join result into plot-ready bars (pure; no matplotlib).

    Returns the top-N channels of ``ranking_key`` (``dr_ranking`` or ``fault_ranking``)
    by |correlation|, each with the correlation, the failing-env mean, the population
    mean, and the shift — the bar payload the plot draws.
    """
    ranking = join_result.get(ranking_key, [])
    bars = [
        {
            "name": r["name"],
            "correlation": r["correlation"],
            "failing_mean": r["failing_mean"],
            "population_mean": r["population_mean"],
            "shift": r["shift"],
        }
        for r in ranking[:top_n]
    ]
    return {"axis": join_result.get("axis"), "bars": bars}


# Per-level bar colors, consistent with the eval drdist convention (ood = magenta).
_LEVEL_COLORS = {
    "none": "#1f77b4", "soft": "#2ca02c", "medium": "#ff7f0e",
    "hard": "#d62728", "ood": "#e377c2",
}


# Which rankings to draw as columns, with the column header shown above each.
_PLOT_COLUMNS: tuple[tuple[str, str], ...] = (
    ("dr_ranking", "DR"),
    ("fault_ranking", "FAULT"),
)


def plot_failure_dr(levels_result: dict, output_path: str, top_n: int = 8) -> str | None:
    """Plot |correlation| of each channel with failure: rows = DR levels, cols = dr/fault.

    Each row is one DR level; the left column ranks dr_ channels and the right column
    ranks fault_ channels (the FTC signal). Bars are the top-N channels by |correlation|
    (failing-env vs population). A level whose strongest dr correlate is a lateral CoG/CoB
    offset, or whose strongest fault correlate is a dead thruster, is direct env-level
    evidence that disturbance/fault drives the failure. A column with no channels in any
    level is dropped, so a dr-only run renders exactly as before. Returns the written
    path, or None if there is nothing to plot.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    levels = list(levels_result.get("levels", {}))
    # Keep only columns (dr/fault) that have at least one ranked channel in some level.
    cols = [
        (key, header) for key, header in _PLOT_COLUMNS
        if any(levels_result["levels"][lvl].get(key) for lvl in levels)
    ]
    # Rows that carry data in at least one of the surviving columns.
    rows = [lvl for lvl in levels
            if any(levels_result["levels"][lvl].get(key) for key, _ in cols)]
    if not rows or not cols:
        return None

    axis = levels_result.get("axis", "?")
    fig, axes = plt.subplots(
        len(rows), len(cols),
        figsize=(6.5 * len(cols), max(3.0, 2.6 * len(rows))), squeeze=False,
    )
    for i, lvl in enumerate(rows):
        for j, (key, header) in enumerate(cols):
            ax = axes[i, j]
            pdata = build_failure_dr_plot_data(levels_result["levels"][lvl], top_n=top_n, ranking_key=key)
            names = [_strip_value_prefix(b["name"]) for b in pdata["bars"]]
            corrs = [b["correlation"] for b in pdata["bars"]]
            ypos = np.arange(len(names))
            ax.barh(ypos, corrs, color=_LEVEL_COLORS.get(lvl, "gray"), edgecolor="black", linewidth=0.4)
            ax.set_yticks(ypos)
            ax.set_yticklabels(names, fontsize=8)
            ax.invert_yaxis()
            ax.axvline(0.0, color="gray", linewidth=0.8)
            ax.set_xlim(-1.0, 1.0)
            ax.set_xlabel(f"point-biserial corr (failing-env <-> {header} value)", fontsize=9)
            ax.set_title(f"{lvl}: which {header} is shifted in the worst-{axis} envs", fontsize=10)
            ax.grid(True, alpha=0.3, axis="x")

    fig.suptitle(f"per-env DR/FAULT <-> {axis} failure join", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return output_path
