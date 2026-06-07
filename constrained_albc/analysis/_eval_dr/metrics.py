# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Metric computations for eval_dr (pure numpy / data dict; no Isaac Sim).

Extracted verbatim from eval_dr.py:
  - segment classification + step-response helpers
  - compute_metrics       (static mode)
  - _periodic_compute_metrics (periodic mode)
  - compute_seg_metrics   (segmented/switching mode)

All operate on plain data dicts and are unit-testable without a booted sim.
"""

from __future__ import annotations

import numpy as np


def _step_response_one_segment(
    actual_roll: np.ndarray,
    actual_pitch: np.ndarray,
    alive: np.ndarray,
    prev_roll: float,
    prev_pitch: float,
    cur_roll: float,
    cur_pitch: float,
    seg_time: np.ndarray,
) -> tuple[float, float, float]:
    """Compute step-response metrics for one attitude segment.

    Returns (rise_time, overshoot_pct, peak_time) averaged across roll/pitch
    axes with meaningful step changes (>1 deg).
    """
    axis_results: list[tuple[float, float, float]] = []

    for actual, prev_val, cur_val in [
        (actual_roll, prev_roll, cur_roll),
        (actual_pitch, prev_pitch, cur_pitch),
    ]:
        step_mag = abs(cur_val - prev_val)
        if step_mag < 1.0:
            continue

        mean_val = np.nanmean(np.where(alive, actual, np.nan), axis=1)
        sign = 1.0 if cur_val > prev_val else -1.0

        # Rise time: 10% -> 90% of step
        thresh_10 = prev_val + sign * 0.1 * step_mag
        thresh_90 = prev_val + sign * 0.9 * step_mag
        t_10 = None
        t_90 = None
        for i, v in enumerate(mean_val):
            if np.isnan(v):
                continue
            if t_10 is None and sign * (v - thresh_10) >= 0:
                t_10 = seg_time[i] - seg_time[0]
            if t_90 is None and sign * (v - thresh_90) >= 0:
                t_90 = seg_time[i] - seg_time[0]
        rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else float("nan")

        # Overshoot: actual exceeding target / step magnitude * 100
        overshoot_val = (np.nanmax(mean_val) - cur_val) if sign > 0 else (cur_val - np.nanmin(mean_val))
        overshoot_pct = max(0.0, overshoot_val) / step_mag * 100.0

        # Peak time
        peak_idx = np.nanargmax(mean_val) if sign > 0 else np.nanargmin(mean_val)
        peak_time = seg_time[peak_idx] - seg_time[0]

        axis_results.append((rise_time, overshoot_pct, peak_time))

    if not axis_results:
        return float("nan"), float("nan"), float("nan")

    rt = float(np.nanmean([r[0] for r in axis_results]))
    os_pct = float(np.nanmean([r[1] for r in axis_results]))
    pt = float(np.nanmean([r[2] for r in axis_results]))
    return rt, os_pct, pt


def _classify_segment(name: str) -> str:
    """Classify a segment name into a block type.

    Returns one of: "warmup", "attitude", "lin_vel", "yaw", "unknown".
    """
    low = name.lower()
    if "warmup" in low:
        return "warmup"
    if low.startswith("att") or "roll" in low or "pitch" in low:
        return "attitude"
    if low.startswith("vxyz") or "vx" in low or "vy" in low or "vz" in low:
        return "lin_vel"
    if "yaw" in low:
        return "yaw"
    return "unknown"


def _get_block_step_range(
    segment_names: list[str],
    steps_per_segment: int,
    block_type: str,
) -> tuple[int, int]:
    """Return (start_step, end_step) covering all contiguous segments of *block_type*.

    Segments are identified by ``_classify_segment``. The range spans from
    the first segment of matching type to the last (inclusive).
    """
    first = None
    last = None
    for i, name in enumerate(segment_names):
        if _classify_segment(name) == block_type:
            if first is None:
                first = i
            last = i
    if first is None or last is None:
        return 0, 0
    return first * steps_per_segment, (last + 1) * steps_per_segment


def _pick_sample_env(d: dict) -> int | None:
    """Pick a representative (median-error) env index for trajectory overlay.

    Returns None if num_envs <= 1 (sample would be identical to mean).
    """
    roll_err = d.get("error_roll")
    if roll_err is None or roll_err.ndim < 2 or roll_err.shape[1] <= 1:
        return None
    # Total attitude error per env (mean over timesteps)
    att_err = np.sqrt(d["error_roll"] ** 2 + d["error_pitch"] ** 2)
    per_env = np.nanmean(att_err, axis=0)  # (num_envs,)
    median_val = np.nanmedian(per_env)
    return int(np.argmin(np.abs(per_env - median_val)))


def _step_response_scalar_segment(
    actual: np.ndarray,
    alive: np.ndarray,
    prev_target: float,
    cur_target: float,
    seg_time: np.ndarray,
    min_step_mag: float = 0.01,
) -> tuple[float, float]:
    """Compute step-response metrics for a single scalar channel segment.

    Args:
        actual: (T, N) actual values.
        alive: (T, N) bool mask.
        prev_target: target at end of previous segment.
        cur_target: target in this segment.
        seg_time: (T,) time array.
        min_step_mag: minimum step magnitude to consider meaningful.

    Returns:
        (rise_time, overshoot_pct). NaN if step is too small or no data.
    """
    step_mag = abs(cur_target - prev_target)
    if step_mag < min_step_mag:
        return float("nan"), float("nan")

    mean_val = np.nanmean(np.where(alive, actual, np.nan), axis=1)
    sign = 1.0 if cur_target > prev_target else -1.0

    # Rise time: 10% -> 90%
    thresh_10 = prev_target + sign * 0.1 * step_mag
    thresh_90 = prev_target + sign * 0.9 * step_mag
    t_10 = None
    t_90 = None
    for i, v in enumerate(mean_val):
        if np.isnan(v):
            continue
        if t_10 is None and sign * (v - thresh_10) >= 0:
            t_10 = seg_time[i] - seg_time[0]
        if t_90 is None and sign * (v - thresh_90) >= 0:
            t_90 = seg_time[i] - seg_time[0]
    rise_time = (t_90 - t_10) if (t_10 is not None and t_90 is not None) else float("nan")

    # Overshoot
    overshoot_val = (np.nanmax(mean_val) - cur_target) if sign > 0 else (cur_target - np.nanmin(mean_val))
    overshoot_pct = max(0.0, overshoot_val) / step_mag * 100.0

    return rise_time, overshoot_pct


def compute_metrics(data: dict) -> dict:
    """Compute per-channel summary metrics from collected data.

    Skips warmup and tail segments. Computes separate metrics for:
    - Attitude (roll/pitch): SS error, settling time, rise time, overshoot
    - Linear velocity (per-axis vx, vy, vz): SS error, rise time, overshoot
    - Yaw rate: SS error, rise time, overshoot
    """
    time_s = data["time"]
    error_roll = data["error_roll"]
    error_pitch = data["error_pitch"]
    terminated = data["terminated"]
    num_envs = error_roll.shape[1]
    seg_steps = data["steps_per_segment"]
    seg_names = data["segment_names"]
    seg_duration = data["segment_duration"]

    error_norm = np.sqrt(error_roll**2 + error_pitch**2)
    alive = ~terminated
    survival_rate = float(alive[-1].sum()) / num_envs * 100.0

    target_roll = data["target_roll_deg"]
    target_pitch = data["target_pitch_deg"]

    max_target_amp = max(
        float(np.max(np.abs(target_roll))),
        float(np.max(np.abs(target_pitch))),
        1.0,
    )
    settling_threshold = max(2.0, max_target_amp * 0.33)

    # ---- Attitude metrics (only attitude segments) ----
    att_ss_errors: list[float] = []
    att_ss_jitters: list[float] = []
    att_ss_jitters_std: list[float] = []  # env-to-env spread of per-env jitter (rule03 CV)
    att_settling_times: list[float] = []
    att_rise_times: list[float] = []
    att_overshoot_pcts: list[float] = []
    att_zero_crossings: list[float] = []

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "attitude":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_error = error_norm[s:e]
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]

        # Steady-state error and jitter (last 50% of segment)
        ss_start = int(seg_steps * 0.5)
        ss_error = seg_error[ss_start:]
        ss_alive = seg_alive[ss_start:]
        if ss_alive.any():
            ss_vals = np.where(ss_alive, ss_error, np.nan)
            att_ss_errors.append(float(np.nanmean(ss_vals)))
            # SS jitter (unified to the recompute per-env-then-aggregate form so
            # ss_jitter_std exists): per-env temporal std (axis=0 is time), then
            # mean across envs = jitter, std across envs = jitter_std (rule03 CV).
            per_env_jit = np.nanstd(ss_vals, axis=0)
            att_ss_jitters.append(float(np.nanmean(per_env_jit)))
            att_ss_jitters_std.append(float(np.nanstd(per_env_jit)))
        else:
            att_ss_errors.append(float("nan"))
            att_ss_jitters.append(float("nan"))
            att_ss_jitters_std.append(float("nan"))

        # Zero crossing count: number of times the mean error signal crosses
        # the target (sign changes in error_roll/pitch relative to target).
        # Use roll axis as representative; count sign changes after rise (first 20% skipped).
        zc_start = int(seg_steps * 0.2)
        cur_roll_tgt = float(target_roll[s])
        roll_mean = np.nanmean(np.where(seg_alive, data["actual_roll_deg"][s:e], np.nan), axis=1)
        roll_deviation = roll_mean[zc_start:] - cur_roll_tgt
        valid = ~np.isnan(roll_deviation)
        if valid.sum() > 2:
            signs = np.sign(roll_deviation[valid])
            crossings = np.sum(np.abs(np.diff(signs)) > 0)
            att_zero_crossings.append(float(crossings))
        else:
            att_zero_crossings.append(float("nan"))

        # Settling time: last time error exceeds threshold, then +1 step.
        # Standard control definition: time after which error stays within band permanently.
        mean_per_step = np.nanmean(np.where(seg_alive, seg_error, np.nan), axis=1)
        above = mean_per_step >= settling_threshold
        if not above.any():
            att_settling_times.append(0.0)  # already within band at start
        else:
            last_above_idx = np.where(above)[0][-1]
            if last_above_idx < len(seg_time) - 1:
                att_settling_times.append(float(seg_time[last_above_idx + 1] - seg_time[0]))
            else:
                att_settling_times.append(float(seg_duration))  # never permanently settled

        # Step-response (rise time, overshoot) via existing dual-axis helper
        cur_roll_target = float(target_roll[s])
        cur_pitch_target = float(target_pitch[s])
        prev_roll_target = float(target_roll[s - 1]) if s > 0 else 0.0
        prev_pitch_target = float(target_pitch[s - 1]) if s > 0 else 0.0

        seg_rt, seg_os, _ = _step_response_one_segment(
            data["actual_roll_deg"][s:e],
            data["actual_pitch_deg"][s:e],
            seg_alive,
            prev_roll_target,
            prev_pitch_target,
            cur_roll_target,
            cur_pitch_target,
            seg_time,
        )
        att_rise_times.append(seg_rt)
        att_overshoot_pcts.append(seg_os)

    # Aggregate attitude error over attitude block only
    att_start, att_end = _get_block_step_range(seg_names, seg_steps, "attitude")
    att_alive = alive[att_start:att_end]
    att_err = error_norm[att_start:att_end]
    if att_alive.any():
        total_att_error = float(np.nanmean(np.where(att_alive, att_err, np.nan)))
        per_env_att = np.nanmean(np.where(att_alive, att_err, np.nan), axis=0)
        total_att_error_std = float(np.nanstd(per_env_att))
    else:
        total_att_error = float("nan")
        total_att_error_std = float("nan")

    # ---- Linear velocity metrics (per-axis, only lin_vel segments) ----
    lin_vel_keys = ["lin_vel_x", "lin_vel_y", "lin_vel_z"]
    target_vel_keys = ["target_vx", "target_vy", "target_vz"]
    axis_labels = ["vx", "vy", "vz"]

    lin_vel_ss_errors: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_ss_jitters: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_ss_jitters_std: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_rise_times: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_overshoot_pcts: dict[str, list[float]] = {a: [] for a in axis_labels}
    lin_vel_zero_crossings: dict[str, list[float]] = {a: [] for a in axis_labels}

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "lin_vel":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]

        for ax_i, (dkey, tkey, ax_name) in enumerate(zip(lin_vel_keys, target_vel_keys, axis_labels)):
            seg_actual = data[dkey][s:e]
            cur_target = float(data[tkey][s])
            prev_target = float(data[tkey][s - 1]) if s > 0 else 0.0

            # SS error and jitter: mean/std of |actual - target| in last 50%
            ss_start = int(seg_steps * 0.5)
            ss_actual = seg_actual[ss_start:]
            ss_alive = seg_alive[ss_start:]
            ss_err = np.abs(ss_actual - cur_target)
            if ss_alive.any():
                ss_vals = np.where(ss_alive, ss_err, np.nan)
                lin_vel_ss_errors[ax_name].append(float(np.nanmean(ss_vals)))
                # unified recompute per-env-then-aggregate jitter form (see att above)
                per_env_jit = np.nanstd(ss_vals, axis=0)
                lin_vel_ss_jitters[ax_name].append(float(np.nanmean(per_env_jit)))
                lin_vel_ss_jitters_std[ax_name].append(float(np.nanstd(per_env_jit)))
            else:
                lin_vel_ss_errors[ax_name].append(float("nan"))
                lin_vel_ss_jitters[ax_name].append(float("nan"))
                lin_vel_ss_jitters_std[ax_name].append(float("nan"))

            # Zero crossing count (after initial 20% of segment)
            zc_start = int(seg_steps * 0.2)
            mean_val = np.nanmean(np.where(seg_alive, seg_actual, np.nan), axis=1)
            deviation = mean_val[zc_start:] - cur_target
            valid = ~np.isnan(deviation)
            if valid.sum() > 2:
                signs = np.sign(deviation[valid])
                lin_vel_zero_crossings[ax_name].append(float(np.sum(np.abs(np.diff(signs)) > 0)))
            else:
                lin_vel_zero_crossings[ax_name].append(float("nan"))

            # Step-response only if this axis has a step change in this segment
            rt, os_pct = _step_response_scalar_segment(
                seg_actual, seg_alive, prev_target, cur_target, seg_time, min_step_mag=0.01,
            )
            lin_vel_rise_times[ax_name].append(rt)
            lin_vel_overshoot_pcts[ax_name].append(os_pct)

    # Overall lin_vel SS error (per-axis mean then averaged)
    lin_vel_block_start, lin_vel_block_end = _get_block_step_range(seg_names, seg_steps, "lin_vel")
    lin_vel_block_alive = alive[lin_vel_block_start:lin_vel_block_end]
    lin_vel_block_norm = data["lin_vel_norm"][lin_vel_block_start:lin_vel_block_end]
    if lin_vel_block_alive.any():
        total_lin_vel_error = float(np.nanmean(np.where(lin_vel_block_alive, lin_vel_block_norm, np.nan)))
    else:
        total_lin_vel_error = float("nan")

    lin_vel_survival = float(alive[lin_vel_block_end - 1].sum()) / num_envs * 100.0 if lin_vel_block_end > 0 else 0.0

    # ---- Yaw rate metrics (only yaw segments) ----
    yaw_ss_errors: list[float] = []
    yaw_ss_jitters: list[float] = []
    yaw_ss_jitters_std: list[float] = []  # env-to-env spread of per-env jitter (rule03 CV)
    yaw_rise_times: list[float] = []
    yaw_overshoot_pcts: list[float] = []
    yaw_zero_crossings: list[float] = []

    for seg_idx, name in enumerate(seg_names):
        if _classify_segment(name) != "yaw":
            continue
        s = seg_idx * seg_steps
        e = (seg_idx + 1) * seg_steps
        seg_alive = alive[s:e]
        seg_time = time_s[s:e]
        seg_actual = data["yaw_rate"][s:e]
        cur_target = float(data["target_yaw_rate"][s])
        prev_target = float(data["target_yaw_rate"][s - 1]) if s > 0 else 0.0

        # SS error and jitter
        ss_start = int(seg_steps * 0.5)
        ss_actual = seg_actual[ss_start:]
        ss_alive = seg_alive[ss_start:]
        ss_err = np.abs(ss_actual - cur_target)
        if ss_alive.any():
            ss_vals = np.where(ss_alive, ss_err, np.nan)
            yaw_ss_errors.append(float(np.nanmean(ss_vals)))
            # unified recompute per-env-then-aggregate jitter form (see att above)
            per_env_jit = np.nanstd(ss_vals, axis=0)
            yaw_ss_jitters.append(float(np.nanmean(per_env_jit)))
            yaw_ss_jitters_std.append(float(np.nanstd(per_env_jit)))
        else:
            yaw_ss_errors.append(float("nan"))
            yaw_ss_jitters.append(float("nan"))
            yaw_ss_jitters_std.append(float("nan"))

        # Zero crossing count (after initial 20%)
        zc_start = int(seg_steps * 0.2)
        mean_val = np.nanmean(np.where(seg_alive, seg_actual, np.nan), axis=1)
        deviation = mean_val[zc_start:] - cur_target
        valid = ~np.isnan(deviation)
        if valid.sum() > 2:
            signs = np.sign(deviation[valid])
            yaw_zero_crossings.append(float(np.sum(np.abs(np.diff(signs)) > 0)))
        else:
            yaw_zero_crossings.append(float("nan"))

        # Step-response
        rt, os_pct = _step_response_scalar_segment(
            seg_actual, seg_alive, prev_target, cur_target, seg_time, min_step_mag=0.01,
        )
        yaw_rise_times.append(rt)
        yaw_overshoot_pcts.append(os_pct)

    yaw_block_start, yaw_block_end = _get_block_step_range(seg_names, seg_steps, "yaw")
    yaw_block_alive = alive[yaw_block_start:yaw_block_end]
    yaw_block_actual = data["yaw_rate"][yaw_block_start:yaw_block_end]
    yaw_block_target = data["target_yaw_rate"][yaw_block_start:yaw_block_end, None]  # (T,) -> (T,1) for broadcast
    yaw_block_err = np.abs(yaw_block_actual - yaw_block_target)
    if yaw_block_alive.any():
        total_yaw_rate_error = float(np.nanmean(np.where(yaw_block_alive, yaw_block_err, np.nan)))
    else:
        total_yaw_rate_error = float("nan")

    yaw_survival = float(alive[yaw_block_end - 1].sum()) / num_envs * 100.0 if yaw_block_end > 0 else 0.0

    return {
        # Attitude
        "total_att_error": total_att_error,
        "total_att_error_std": total_att_error_std,
        "att_ss_errors": att_ss_errors,
        "att_ss_jitters": att_ss_jitters,
        "att_ss_jitters_std": att_ss_jitters_std,
        "att_settling_times": att_settling_times,
        "att_rise_times": att_rise_times,
        "att_overshoot_pcts": att_overshoot_pcts,
        "att_zero_crossings": att_zero_crossings,
        # Linear velocity (per-axis)
        "total_lin_vel_error": total_lin_vel_error,
        "lin_vel_ss_errors": lin_vel_ss_errors,  # dict[axis_name, list[float]]
        "lin_vel_ss_jitters": lin_vel_ss_jitters,
        "lin_vel_ss_jitters_std": lin_vel_ss_jitters_std,
        "lin_vel_rise_times": lin_vel_rise_times,
        "lin_vel_overshoot_pcts": lin_vel_overshoot_pcts,
        "lin_vel_zero_crossings": lin_vel_zero_crossings,
        "lin_vel_survival": lin_vel_survival,
        # Yaw
        "total_yaw_rate_error": total_yaw_rate_error,
        "yaw_ss_errors": yaw_ss_errors,
        "yaw_ss_jitters": yaw_ss_jitters,
        "yaw_ss_jitters_std": yaw_ss_jitters_std,
        "yaw_rise_times": yaw_rise_times,
        "yaw_overshoot_pcts": yaw_overshoot_pcts,
        "yaw_zero_crossings": yaw_zero_crossings,
        "yaw_survival": yaw_survival,
        # Global
        "survival_rate": survival_rate,
    }


def _settling_time(signal: np.ndarray, threshold: float, step_dt: float) -> float:
    """Time from start until signal stays within threshold permanently.

    Args:
        signal: 1D array of absolute values (e.g. attitude error norm).
        threshold: Settling band (e.g. 1.0 deg).
        step_dt: Time per step.

    Returns:
        Settling time in seconds. NaN if never settles.
    """
    within = signal <= threshold
    # Find last step where signal exceeds threshold
    exceed_indices = np.where(~within)[0]
    if len(exceed_indices) == 0:
        return 0.0  # Already within threshold from the start
    last_exceed = exceed_indices[-1]
    if last_exceed >= len(signal) - 1:
        return float("nan")  # Never settles
    return (last_exceed + 1) * step_dt


def _periodic_compute_metrics(data: dict) -> dict:
    """Compute per-DR-step and overall metrics.

    Per DR step:
        - SS error: mean error in last 50% of step (steady state)
        - Peak transient: max error in first 50% of step (overshoot)
        - Settling time: time to stay within threshold permanently
    """
    steps_per_dr = data["steps_per_dr"]
    num_dr_steps = data["num_dr_steps"]
    step_duration = data["step_duration"]
    terminated = data["terminated"]
    step_dt = data["time"][1] - data["time"][0] if len(data["time"]) > 1 else 0.02

    # Use last 50% of each DR step as steady state
    ss_start_frac = 0.5
    ss_start_offset = int(steps_per_dr * ss_start_frac)

    # Settling thresholds
    ATT_SETTLE_THRESH = 1.0   # deg
    LV_SETTLE_THRESH = 0.05   # m/s
    YR_SETTLE_THRESH = 0.02   # rad/s

    per_step_att_err = []
    per_step_lin_vel = []
    per_step_yaw_rate = []
    # env-to-env std of the per-step SS error (rule03 CV: std/mean across envs).
    # The 2D arrays carry an env axis, so per-env SS means are available to disperse.
    per_step_att_err_std = []
    per_step_lin_vel_std = []
    per_step_yaw_rate_std = []
    per_step_att_peak = []
    per_step_lv_peak = []
    per_step_yr_peak = []
    per_step_att_settle = []
    per_step_lv_settle = []
    per_step_yr_settle = []

    for dr_i in range(num_dr_steps):
        seg_s = dr_i * steps_per_dr
        seg_e = (dr_i + 1) * steps_per_dr
        ss_s = seg_s + ss_start_offset
        if ss_s >= len(data["time"]):
            break

        # Full segment signals (for peak / settling)
        roll_full = data["actual_roll_deg"][seg_s:seg_e]
        pitch_full = data["actual_pitch_deg"][seg_s:seg_e]
        att_full = np.sqrt(roll_full ** 2 + pitch_full ** 2)
        lv_full = np.sqrt(
            data["lin_vel_x"][seg_s:seg_e] ** 2
            + data["lin_vel_y"][seg_s:seg_e] ** 2
            + data["lin_vel_z"][seg_s:seg_e] ** 2
        )
        yr_full = np.abs(data["yaw_rate"][seg_s:seg_e])
        alive_full = ~terminated[seg_s:seg_e]

        # SS signals (last 50%)
        alive_ss = alive_full[ss_start_offset:]
        att_ss = att_full[ss_start_offset:]
        lv_ss = lv_full[ss_start_offset:]
        yr_ss = yr_full[ss_start_offset:]

        # -- SS error (mean in last 50%) + env-to-env std (axis=0 is time, axis=1 env) --
        att_ss_masked = np.where(alive_ss, att_ss, np.nan)
        lv_ss_masked = np.where(alive_ss, lv_ss, np.nan)
        yr_ss_masked = np.where(alive_ss, yr_ss, np.nan)
        per_step_att_err.append(np.nanmean(att_ss_masked))
        per_step_lin_vel.append(np.nanmean(lv_ss_masked))
        per_step_yaw_rate.append(np.nanmean(yr_ss_masked))
        # per-env SS mean first, then std across envs -> CV computable per rule03
        per_step_att_err_std.append(np.nanstd(np.nanmean(att_ss_masked, axis=0)))
        per_step_lin_vel_std.append(np.nanstd(np.nanmean(lv_ss_masked, axis=0)))
        per_step_yaw_rate_std.append(np.nanstd(np.nanmean(yr_ss_masked, axis=0)))

        # -- Peak transient (max in full segment, per-env mean) --
        att_peak = np.where(alive_full, att_full, np.nan)
        per_step_att_peak.append(np.nanmax(np.nanmean(att_peak, axis=1)))
        lv_peak = np.where(alive_full, lv_full, np.nan)
        per_step_lv_peak.append(np.nanmax(np.nanmean(lv_peak, axis=1)))
        yr_peak = np.where(alive_full, yr_full, np.nan)
        per_step_yr_peak.append(np.nanmax(np.nanmean(yr_peak, axis=1)))

        # -- Settling time (per-env mean signal) --
        att_mean_signal = np.nanmean(np.where(alive_full, att_full, np.nan), axis=1)
        per_step_att_settle.append(_settling_time(att_mean_signal, ATT_SETTLE_THRESH, step_dt))
        lv_mean_signal = np.nanmean(np.where(alive_full, lv_full, np.nan), axis=1)
        per_step_lv_settle.append(_settling_time(lv_mean_signal, LV_SETTLE_THRESH, step_dt))
        yr_mean_signal = np.nanmean(np.where(alive_full, yr_full, np.nan), axis=1)
        per_step_yr_settle.append(_settling_time(yr_mean_signal, YR_SETTLE_THRESH, step_dt))

    return {
        # SS error
        "per_step_att_err": np.array(per_step_att_err),
        "per_step_lin_vel": np.array(per_step_lin_vel),
        "per_step_yaw_rate": np.array(per_step_yaw_rate),
        "mean_att_err": np.nanmean(per_step_att_err),
        "mean_lin_vel": np.nanmean(per_step_lin_vel),
        "mean_yaw_rate": np.nanmean(per_step_yaw_rate),
        # SS error env-to-env dispersion (per-step + aggregate) -> CV per rule03
        "per_step_att_err_std": np.array(per_step_att_err_std),
        "per_step_lin_vel_std": np.array(per_step_lin_vel_std),
        "per_step_yaw_rate_std": np.array(per_step_yaw_rate_std),
        "mean_att_err_std": np.nanmean(per_step_att_err_std),
        "mean_lin_vel_std": np.nanmean(per_step_lin_vel_std),
        "mean_yaw_rate_std": np.nanmean(per_step_yaw_rate_std),
        # Peak transient
        "per_step_att_peak": np.array(per_step_att_peak),
        "per_step_lv_peak": np.array(per_step_lv_peak),
        "per_step_yr_peak": np.array(per_step_yr_peak),
        "mean_att_peak": np.nanmean(per_step_att_peak),
        "mean_lv_peak": np.nanmean(per_step_lv_peak),
        "mean_yr_peak": np.nanmean(per_step_yr_peak),
        # Settling time
        "per_step_att_settle": np.array(per_step_att_settle),
        "per_step_lv_settle": np.array(per_step_lv_settle),
        "per_step_yr_settle": np.array(per_step_yr_settle),
        "mean_att_settle": np.nanmean(per_step_att_settle),
        "mean_lv_settle": np.nanmean(per_step_lv_settle),
        "mean_yr_settle": np.nanmean(per_step_yr_settle),
        # Thresholds (for reference)
        "att_settle_thresh": ATT_SETTLE_THRESH,
        "lv_settle_thresh": LV_SETTLE_THRESH,
        "yr_settle_thresh": YR_SETTLE_THRESH,
        # Survival
        "survival": (~data["terminated"][-1]).mean() * 100,
        "step_duration": step_duration,
    }


def compute_seg_metrics(data: dict) -> dict:
    """Per-seg per-env transient metrics after DR switch.

    Each seg (except seg 0) represents "DR just changed, policy must adapt".
    Seg 0 is a baseline: initial DR, no switch yet.

    Primary metrics (target = xyz=0, rpy=0):
        pos_drift_norm_peak: max sqrt(x^2+y^2+z^2) within seg (transient)
        pos_drift_norm_ss:   mean of last 50% (DC offset after transient)
        yaw_drift_deg_peak / ss: |yaw| (already wrapped to [-180,180])
        peak_roll_deg / ss_roll_deg: |roll| peak/ss (attitude is a directly-logged view)
        peak_pitch_deg / ss_pitch_deg: |pitch|
    """
    steps_per_seg = data["steps_per_segment"]
    num_segs = data["num_segments"]
    seg_duration = data["segment_duration"]
    num_envs = data["actual_roll_deg"].shape[1]

    per_seg = []
    for seg in range(num_segs):
        s = seg * steps_per_seg
        e = (seg + 1) * steps_per_seg
        roll_abs = np.abs(data["actual_roll_deg"][s:e])
        pitch_abs = np.abs(data["actual_pitch_deg"][s:e])
        yaw_abs = np.abs(data["actual_yaw_deg"][s:e])
        pos_norm = np.sqrt(
            data["pos_x"][s:e] ** 2 + data["pos_y"][s:e] ** 2 + data["pos_z"][s:e] ** 2
        )
        half = steps_per_seg // 2

        per_seg.append({
            "seg_idx": seg,
            # Attitude |err| from 0
            "peak_roll_deg": roll_abs.max(axis=0).tolist(),
            "peak_pitch_deg": pitch_abs.max(axis=0).tolist(),
            "peak_yaw_deg": yaw_abs.max(axis=0).tolist(),
            "ss_roll_deg": roll_abs[half:].mean(axis=0).tolist(),
            "ss_pitch_deg": pitch_abs[half:].mean(axis=0).tolist(),
            "ss_yaw_deg": yaw_abs[half:].mean(axis=0).tolist(),
            # Position drift from xyz=0
            "pos_drift_peak": pos_norm.max(axis=0).tolist(),
            "pos_drift_ss": pos_norm[half:].mean(axis=0).tolist(),
            "pos_x_ss": data["pos_x"][s:e][half:].mean(axis=0).tolist(),
            "pos_y_ss": data["pos_y"][s:e][half:].mean(axis=0).tolist(),
            "pos_z_ss": data["pos_z"][s:e][half:].mean(axis=0).tolist(),
        })

    return {"per_seg": per_seg, "num_envs": num_envs, "num_segments": num_segs}
