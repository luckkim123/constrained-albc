# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Depth/XY exam schedule and metrics (pure numpy, Isaac-Sim-free).

depth-xy-ftc-2026-09 PLAN "Eval schedule": depth steps +-0.3 m, hover, xy force steps at
attitude 0; depth ss error, settling, attitude deviation, force tracking; mean/median/P90/max.
eval.py ``depthxy`` drives the env with SCHEDULE and hands the recorded per-step arrays to
compute_depthxy_metrics.
"""

from __future__ import annotations

import numpy as np

DEPTH_STEP_M = 0.3
SS_WINDOW_S = 3.0  # steady-state window at the end of every segment
SETTLE_BAND_M = 0.05  # settled once |e_z| stays inside this band until the segment ends

# (name, duration s, depth offset from the episode-start depth in m (+ = deeper), u_x, u_y).
# u_xy is the normalized body-frame horizontal force command, F_cmd = u_xy * depth_xy.xy_force_scale.
# Roll/pitch and yaw-rate commands are 0 in every segment.
SCHEDULE: tuple[tuple[str, float, float, float, float], ...] = (
    ("hover", 5.0, 0.0, 0.0, 0.0),
    ("depth +0.3", 10.0, DEPTH_STEP_M, 0.0, 0.0),
    ("depth return 1", 10.0, 0.0, 0.0, 0.0),
    ("depth -0.3", 10.0, -DEPTH_STEP_M, 0.0, 0.0),
    ("depth return 2", 10.0, 0.0, 0.0, 0.0),
    ("xy +x", 8.0, 0.0, 1.0, 0.0),
    ("xy +y", 8.0, 0.0, 0.0, 1.0),
    ("xy -x", 8.0, 0.0, -1.0, 0.0),
    ("xy -y", 8.0, 0.0, 0.0, -1.0),
    ("final hover", 5.0, 0.0, 0.0, 0.0),
)
SCHEDULE_DURATION_S = sum(seg[1] for seg in SCHEDULE)


def build_depthxy_schedule(step_dt: float) -> dict[str, np.ndarray]:
    """Per-step commands for SCHEDULE: depth_offset (T,), u_xy (T, 2), seg_start (S+1,) step indices."""
    steps = [int(round(seg[1] / step_dt)) for seg in SCHEDULE]
    seg_start = np.concatenate([[0], np.cumsum(steps)]).astype(np.int64)
    return {
        "time": np.arange(seg_start[-1]) * step_dt,  # time at which step k's command is applied
        "depth_offset": np.repeat([seg[2] for seg in SCHEDULE], steps).astype(np.float32),
        "u_xy": np.repeat([seg[3:5] for seg in SCHEDULE], steps, axis=0).astype(np.float32),
        "seg_start": seg_start,
        "segment_names": np.array([seg[0] for seg in SCHEDULE]),
    }


def _stats(x: np.ndarray) -> dict:
    """mean / median / P90 / max over the finite entries; None when there are none."""
    x = np.asarray(x, dtype=np.float64)
    x = x[np.isfinite(x)]
    if x.size == 0:
        return {"mean": None, "median": None, "p90": None, "max": None, "n": 0}
    return {
        "mean": float(x.mean()),
        "median": float(np.median(x)),
        "p90": float(np.percentile(x, 90)),
        "max": float(x.max()),
        "n": int(x.size),
    }


def compute_depthxy_metrics(data: dict, step_dt: float) -> dict:
    """Per-segment metrics, each a per-env scalar summarized across envs by _stats.

    data: depth, depth_target, roll_err_deg, pitch_err_deg (T, N); force_xy, force_cmd_xy (T, N, 2);
    terminated (T, N) bool for that step; seg_start (S+1,); segment_names (S,); depth_offset (T,); u_xy (T, 2).
    depth is the true depth (+ down), the quantity the depth_tracking reward uses. An env counts in a
    segment only if it has not terminated by the segment's last step, so the post-reset state of a
    terminated env never enters a statistic; failures show up in alive_frac_end instead.
    Settling time / overshoot exist only for segments whose depth offset differs from the previous one;
    an env still outside SETTLE_BAND_M at the segment end has settling time NaN (depth_settled_frac).
    """
    term_ever = np.logical_or.accumulate(np.asarray(data["terminated"], dtype=bool), axis=0)
    ez_all = np.asarray(data["depth"], dtype=np.float64) - np.asarray(data["depth_target"], dtype=np.float64)
    ferr_all = np.linalg.norm(np.asarray(data["force_xy"]) - np.asarray(data["force_cmd_xy"]), axis=-1)
    roll_all = np.abs(np.asarray(data["roll_err_deg"]))
    pitch_all = np.abs(np.asarray(data["pitch_err_deg"]))
    seg_start = np.asarray(data["seg_start"])
    offsets = np.asarray(data["depth_offset"], dtype=np.float64)
    win = max(1, int(round(SS_WINDOW_S / step_dt)))

    segments = []
    for s, name in enumerate(data["segment_names"]):
        a, b = int(seg_start[s]), int(seg_start[s + 1])
        alive = ~term_ever[b - 1]
        ez = ez_all[a:b, alive]
        ferr = ferr_all[a:b, alive]
        step_m = float(offsets[a] - (offsets[a - 1] if a > 0 else 0.0))
        seg = {
            "name": str(name),
            "t_start_s": a * step_dt,
            "duration_s": (b - a) * step_dt,
            "depth_offset_m": float(offsets[a]),
            "u_xy": [float(v) for v in np.asarray(data["u_xy"])[a]],
            "depth_step_m": step_m,
            "n_envs": int(alive.sum()),
            "alive_frac_end": float(alive.mean()),
            "depth_ss_err_m": _stats(np.abs(ez[-win:]).mean(axis=0)),
            "roll_abs_mean_deg": _stats(roll_all[a:b, alive].mean(axis=0)),
            "roll_abs_max_deg": _stats(roll_all[a:b, alive].max(axis=0)),
            "pitch_abs_mean_deg": _stats(pitch_all[a:b, alive].mean(axis=0)),
            "pitch_abs_max_deg": _stats(pitch_all[a:b, alive].max(axis=0)),
            "force_err_N": _stats(ferr.mean(axis=0)),
            "force_err_ss_N": _stats(ferr[-win:].mean(axis=0)),
        }
        if step_m != 0.0:
            out = np.abs(ez) > SETTLE_BAND_M
            last_out = out.shape[0] - 1 - np.argmax(out[::-1], axis=0)
            settle = np.where(out.any(axis=0), (last_out + 1) * step_dt, 0.0)
            settle[out[-1]] = np.nan
            seg["depth_settle_s"] = _stats(settle)
            seg["depth_settled_frac"] = float(np.isfinite(settle).mean()) if settle.size else None
            seg["depth_overshoot_m"] = _stats(np.maximum(0.0, (ez * np.sign(step_m)).max(axis=0)))
        segments.append(seg)

    return {
        "survival_frac": float(1.0 - term_ever[-1].mean()),
        "n_terminated": int(term_ever[-1].sum()),
        "segments": segments,
    }


def render_depthxy_markdown(summary: dict) -> str:
    """Short per-level table: one row per segment."""

    def f(st: dict | None, key: str, nd: int = 3) -> str:
        v = st.get(key) if st else None
        return "-" if v is None else f"{v:.{nd}f}"

    meta = summary.get("meta", {})
    lines = [
        "# depthxy exam",
        "",
        f"checkpoint `{meta.get('checkpoint')}`, task `{meta.get('task')}`, envs {meta.get('num_envs')}, "
        f"health {meta.get('fault_fixed_health')}, delay {meta.get('control_delay')}, "
        f"DR from `{meta.get('doraemon_dr_from')}`, anchor {meta.get('env_dr_anchor')}",
        "",
        f"e_z = true depth - target (m, + deeper); ss = mean |e_z| over the last {SS_WINDOW_S:g} s; settle band "
        f"{SETTLE_BAND_M:g} m; roll/pitch = mean of per-env mean |.| / max of per-env max; F err = |F_xy_real - F_cmd|.",
    ]
    for level, res in summary.items():
        if level == "meta":
            continue
        lines += [
            "",
            f"## {level} (survival {res['survival_frac']:.3f}, truncated {res.get('n_truncated')}, "
            f"override ok {res.get('override_ok')})",
            "",
            "| segment | step m | alive | e_z ss m mean/P90/max | settle s med/P90 (settled) | overshoot m mean/max "
            "| roll deg | pitch deg | F err N mean/P90 |",
            "|:--|--:|--:|--:|--:|--:|--:|--:|--:|",
        ]
        for g in res["segments"]:
            ss = g["depth_ss_err_m"]
            if "depth_settle_s" in g:
                st, frac = g["depth_settle_s"], g["depth_settled_frac"]
                settle = f"{f(st, 'median', 2)}/{f(st, 'p90', 2)} ({'-' if frac is None else f'{frac:.2f}'})"
                over = f"{f(g['depth_overshoot_m'], 'mean')}/{f(g['depth_overshoot_m'], 'max')}"
            else:
                settle = over = "-"
            lines.append(
                f"| {g['name']} | {g['depth_step_m']:+.2f} | {g['alive_frac_end']:.2f} "
                f"| {f(ss, 'mean')}/{f(ss, 'p90')}/{f(ss, 'max')} | {settle} | {over} "
                f"| {f(g['roll_abs_mean_deg'], 'mean', 2)}/{f(g['roll_abs_max_deg'], 'max', 2)} "
                f"| {f(g['pitch_abs_mean_deg'], 'mean', 2)}/{f(g['pitch_abs_max_deg'], 'max', 2)} "
                f"| {f(g['force_err_N'], 'mean', 2)}/{f(g['force_err_N'], 'p90', 2)} |"
            )
    return "\n".join(lines) + "\n"
