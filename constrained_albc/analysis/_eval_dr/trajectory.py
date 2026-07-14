# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Step-change target trajectory for static-mode evaluation (pure numpy).

Extracted verbatim from eval_dr.py. No Isaac Sim dependency.
"""

from __future__ import annotations

import numpy as np

ATT_AMP_DEG = 30.0  # Attitude step amplitude (degrees); full trained att envelope (config att_cmd_rp_range +-pi/6)
LIN_VEL_AMP = 0.25  # Linear velocity step amplitude (m/s)
YAW_RATE_AMP = 0.5  # Yaw rate step amplitude (rad/s); full trained yaw envelope (config yaw_rate_cmd_range +-0.5)
WARMUP_SEGMENTS = 1  # Initial warmup segments (inter-block warmups also excluded via _classify_segment)


def build_step_trajectory(
    segment_duration: float,
    step_dt: float,
    att_amp_deg: float | None = None,
    yaw_rate_amp: float | None = None,
) -> tuple[np.ndarray, dict[str, np.ndarray], list[str], int]:
    """Build 6-DOF step-change target trajectory with inter-block warmups.

    Structure: warmup + att(10) + warmup + lin_vel(10) + warmup + yaw(4)
    Warmup segments (3 total) reset the system state between blocks so each block's
    dynamics are independent of the previous block. All warmup segs excluded from
    metrics/plots; any segment classified as "warmup" is skipped.

    Att block (10 segs): 3x3 grid (-a,0,+a) x (-a,0,+a) + final (0,0) return-to-neutral.
    Lin vel block (10 segs): 2x2x2 corners (+/-v) + (0,0,0) twice.
    Yaw block (4 segs): (+w, -w, 0, 0).

    Args:
        segment_duration: seconds per segment.
        step_dt: seconds per sim step.
        att_amp_deg: override for ATT_AMP_DEG (module default when None).
        yaw_rate_amp: override for YAW_RATE_AMP (module default when None).

    Returns:
        time_s: 1D time array (seconds).
        targets: dict of 1D target arrays keyed by channel name.
        seg_names: list of segment labels.
        warmup_steps: number of warmup steps to skip in metrics/plots.
    """
    a = ATT_AMP_DEG if att_amp_deg is None else att_amp_deg
    v = LIN_VEL_AMP
    w = YAW_RATE_AMP if yaw_rate_amp is None else yaw_rate_amp

    # (roll_deg, pitch_deg, vx, vy, vz, yaw_rate, name)
    # NOTE: every block now starts with a logged zero-command segment so the
    # first plotted step shows the policy at zero command (rather than the
    # raw post-warmup state mid-transition). The attitude block also has its
    # final (0, 0) return doubled so all blocks end with at least 2 segments
    # of zero command for clean steady-state visualization.
    waypoints: list[tuple[float, float, float, float, float, float, str]] = [
        # Initial warmup (1 seg, excluded)
        (0, 0, 0, 0, 0, 0, "warmup (init)"),
        # Logged zero-command pre-attitude (1 seg)
        (0, 0, 0, 0, 0, 0, "att zero (post-warmup)"),
        # Attitude block (10 segs): 3x3 grid + final (0,0) return-to-neutral.
        # Row-major order (roll outer, pitch inner).
        (-a, -a, 0, 0, 0, 0, f"att ({-a:.0f}, {-a:.0f})"),
        (-a,  0, 0, 0, 0, 0, f"att ({-a:.0f}, 0)"),
        (-a,  a, 0, 0, 0, 0, f"att ({-a:.0f}, {a:.0f})"),
        ( 0, -a, 0, 0, 0, 0, f"att (0, {-a:.0f})"),
        ( 0,  0, 0, 0, 0, 0, "att (0, 0)"),
        ( 0,  a, 0, 0, 0, 0, f"att (0, {a:.0f})"),
        ( a, -a, 0, 0, 0, 0, f"att ({a:.0f}, {-a:.0f})"),
        ( a,  0, 0, 0, 0, 0, f"att ({a:.0f}, 0)"),
        ( a,  a, 0, 0, 0, 0, f"att ({a:.0f}, {a:.0f})"),
        ( 0,  0, 0, 0, 0, 0, "att return (0, 0) 1"),
        # Doubling att return so it ends with 2 zero-command segs (matches lin_vel/yaw)
        ( 0,  0, 0, 0, 0, 0, "att return (0, 0) 2"),
        # Inter-block warmup before lin_vel (excluded)
        (0, 0, 0, 0, 0, 0, "warmup (pre-lin_vel)"),
        # Logged zero-command pre-lin_vel (1 seg)
        (0, 0, 0, 0, 0, 0, "vxyz zero (post-warmup)"),
        # Linear velocity block (10 segs): 2x2x2 corners + (0,0,0) twice.
        (0, 0,  v,  v,  v, 0, "vxyz (+, +, +)"),
        (0, 0,  v,  v, -v, 0, "vxyz (+, +, -)"),
        (0, 0,  v, -v,  v, 0, "vxyz (+, -, +)"),
        (0, 0,  v, -v, -v, 0, "vxyz (+, -, -)"),
        (0, 0, -v,  v,  v, 0, "vxyz (-, +, +)"),
        (0, 0, -v,  v, -v, 0, "vxyz (-, +, -)"),
        (0, 0, -v, -v,  v, 0, "vxyz (-, -, +)"),
        (0, 0, -v, -v, -v, 0, "vxyz (-, -, -)"),
        (0, 0,  0,  0,  0, 0, "vxyz return (0, 0, 0) 1"),
        (0, 0,  0,  0,  0, 0, "vxyz return (0, 0, 0) 2"),
        # Inter-block warmup before yaw (excluded)
        (0, 0, 0, 0, 0, 0, "warmup (pre-yaw)"),
        # Logged zero-command pre-yaw (1 seg)
        (0, 0, 0, 0, 0, 0, "yaw zero (post-warmup)"),
        # Yaw rate block (4 segs): +/- + zero twice.
        (0, 0, 0, 0, 0,  w, f"yaw +{w}"),
        (0, 0, 0, 0, 0, -w, f"yaw {-w}"),
        (0, 0, 0, 0, 0,  0, "yaw return 0 (1)"),
        (0, 0, 0, 0, 0,  0, "yaw return 0 (2)"),
    ]

    steps_per_seg = int(segment_duration / step_dt)
    n_segs = len(waypoints)
    total_steps = steps_per_seg * n_segs
    warmup_steps = WARMUP_SEGMENTS * steps_per_seg

    time_s = np.arange(total_steps) * step_dt
    keys = ["roll_deg", "pitch_deg", "vx", "vy", "vz", "yaw_rate"]
    targets: dict[str, np.ndarray] = {k: np.zeros(total_steps) for k in keys}
    seg_names: list[str] = []

    for i, wp in enumerate(waypoints):
        s = i * steps_per_seg
        e = (i + 1) * steps_per_seg
        for j, k in enumerate(keys):
            targets[k][s:e] = wp[j]
        seg_names.append(wp[6])

    return time_s, targets, seg_names, warmup_steps
