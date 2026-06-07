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


def join_failure_dr(data: dict, axis: str = "roll", k: int = 10) -> dict:
    """Join worst-k envs against every dr_<name> channel; rank by |correlation|.

    Returns a dict with the axis, failing-env count, and a ``dr_ranking`` list of
    per-DR records (name, correlation, failing_mean, population_mean, shift) sorted by
    descending |correlation| — the top entry is the DR most associated with failure.
    """
    ss = per_env_ss_error(data, axis=axis)
    mask = failing_env_mask(ss, k=k)
    indicator = mask.astype(np.float64)

    dr_keys = sorted(key for key in data if key.startswith("dr_"))
    ranking = []
    for name in dr_keys:
        vals = np.asarray(data[name], dtype=np.float64).reshape(-1)
        if vals.shape[0] != ss.shape[0]:
            continue  # mismatched length -> not a per-env DR array; skip
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
    return {
        "axis": axis,
        "k": int(min(k, ss.shape[0])),
        "n_failing": int(mask.sum()),
        "dr_ranking": ranking,
    }


def analyze_failure_dr_levels(all_data: dict[str, dict], axis: str = "roll", k: int = 10) -> dict:
    """Run the join for every DR level PRESENT in ``all_data`` (keys, not a static list).

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


def build_failure_dr_plot_data(join_result: dict, top_n: int = 8) -> dict:
    """Shape a single-level join result into plot-ready bars (pure; no matplotlib).

    Returns the top-N DR channels by |correlation|, each with the correlation, the
    failing-env mean, the population mean, and the shift — the bar payload the plot draws.
    """
    ranking = join_result.get("dr_ranking", [])
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


def plot_failure_dr(levels_result: dict, output_path: str, top_n: int = 8) -> str | None:
    """Plot |correlation| of each DR channel with failure, one row per DR level.

    Bars are the top-N DR channels by |correlation| (failing-env vs population). A level
    whose strongest correlate is a lateral CoG/CoB offset is direct env-level evidence
    that disturbance drives the failure. Returns the written path, or None if there is
    nothing to plot.
    """
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    levels = [lvl for lvl in levels_result.get("levels", {})
              if levels_result["levels"][lvl].get("dr_ranking")]
    if not levels:
        return None

    axis = levels_result.get("axis", "?")
    fig, axes = plt.subplots(len(levels), 1, figsize=(10, max(3.0, 2.6 * len(levels))), squeeze=False)
    for i, lvl in enumerate(levels):
        ax = axes[i, 0]
        pdata = build_failure_dr_plot_data(levels_result["levels"][lvl], top_n=top_n)
        names = [b["name"].replace("dr_", "") for b in pdata["bars"]]
        corrs = [b["correlation"] for b in pdata["bars"]]
        ypos = np.arange(len(names))
        ax.barh(ypos, corrs, color=_LEVEL_COLORS.get(lvl, "gray"), edgecolor="black", linewidth=0.4)
        ax.set_yticks(ypos)
        ax.set_yticklabels(names, fontsize=8)
        ax.invert_yaxis()
        ax.axvline(0.0, color="gray", linewidth=0.8)
        ax.set_xlim(-1.0, 1.0)
        ax.set_xlabel("point-biserial corr (failing-env indicator <-> DR value)", fontsize=9)
        ax.set_title(f"{lvl}: which DR is shifted in the worst-{axis} envs", fontsize=10)
        ax.grid(True, alpha=0.3, axis="x")

    fig.suptitle(f"per-env DR <-> {axis} failure join", fontsize=12)
    plt.tight_layout()
    plt.savefig(output_path, dpi=120, bbox_inches="tight")
    plt.close(fig)
    return output_path
