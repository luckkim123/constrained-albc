# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Sim-free serialization helpers extracted from eval.py.

Pure data-dict -> file. Imports on plain python3 so omx can re-export eval
results without booting sim.
"""

from __future__ import annotations

import os

import numpy as np


def write_eval_npz(output_dir: str, level: str, array_data: dict) -> str:
    """Write per-level eval arrays to data_<level>.npz (compressed).

    Returns the written path as a string.
    """
    path = os.path.join(output_dir, f"data_{level}.npz")
    np.savez_compressed(path, **array_data)
    return path


# ---- .mat metadata: variable descriptors (unit + meaning) ----
# Maps each raw array key written into data_{level}.mat to its physical unit and a
# one-line description, so a MATLAB session can interpret the file without reading
# this Python source. Keys must match the array names produced by run_evaluation().
_MAT_VAR_DESC: dict[str, tuple[str, str]] = {
    "time":             ("s",        "rollout time vector, shape (1, T)"),
    "actual_roll_deg":  ("deg",      "measured roll angle, shape (T, num_envs)"),
    "actual_pitch_deg": ("deg",      "measured pitch angle, shape (T, num_envs)"),
    "error_roll":       ("deg",      "roll tracking error (target - actual), (T, num_envs)"),
    "error_pitch":      ("deg",      "pitch tracking error (target - actual), (T, num_envs)"),
    "yaw_rate":         ("rad/s",    "measured yaw rate, shape (T, num_envs)"),
    "lin_vel_x":        ("m/s",      "body-frame surge velocity, shape (T, num_envs)"),
    "lin_vel_y":        ("m/s",      "body-frame sway velocity, shape (T, num_envs)"),
    "lin_vel_z":        ("m/s",      "body-frame heave velocity, shape (T, num_envs)"),
    "lin_vel_norm":     ("m/s",      "linear velocity magnitude, shape (T, num_envs)"),
    "action_magnitude": ("unitless",     "L2 norm of the 8-D action, shape (T, num_envs)"),
    "delta_action":     ("action-norm", "||a(z) - a(z_ablated)|| per env-step; z-ablation diagnostic (#1-A); (T, num_envs); zeros when ablation off"),
    "terminated":       ("bool",        "per-step termination flag, shape (T, num_envs)"),
    "time_to_failure":  ("s",        "time of first termination per env, shape (1, num_envs)"),
    "target_roll_deg":  ("deg",      "commanded roll setpoint, shape (1, T)"),
    "target_pitch_deg": ("deg",      "commanded pitch setpoint, shape (1, T)"),
    "target_yaw_rate":  ("rad/s",    "commanded yaw-rate setpoint, shape (1, T)"),
    "target_vx":        ("m/s",      "commanded surge setpoint, shape (1, T)"),
    "target_vy":        ("m/s",      "commanded sway setpoint, shape (1, T)"),
    "target_vz":        ("m/s",      "commanded heave setpoint, shape (1, T)"),
}


def _build_mat_meta(array_data: dict, level: str, dr_scale: float,
                    checkpoint: str, task: str, num_envs: int, mode: str) -> dict:
    """Build a self-describing metadata struct for a data_{level}.mat file.

    scipy.io.savemat nests a dict as a MATLAB struct, so the returned dict becomes
    `data.meta.<field>` in MATLAB. `eval_axis` is assigned per-FILE (per DR level),
    not per-variable: the same signal (e.g. error_roll) reads as a robustness signal
    at nominal DR levels and an OOD-generalization signal at an OOD level.
    """
    # eval_axis is a coarse classification of what THIS file (DR level) measures,
    # mapping to the three model-selection axes in the eval-mode-restructure spec.
    if level.startswith("ood") or level == "extreme_ood":
        eval_axis = "ood_generalization"
    else:
        # none/soft/medium/hard sweep -> broad robustness; across-env spread within a
        # level also feeds policy_consistency (computed MATLAB-side from the env axis).
        eval_axis = "robustness;policy_consistency"

    variables = {}
    for key in array_data:
        unit, desc = _MAT_VAR_DESC.get(key, ("unknown", "undocumented array"))
        variables[key] = {"unit": unit, "description": desc}

    return {
        "dr_level": level,
        "dr_scale": float(dr_scale),
        "eval_axis": eval_axis,
        "mode": mode,
        "task": task,
        "checkpoint": checkpoint if checkpoint else "",
        "num_envs": int(num_envs),
        "dims_note": "per-env signals are (T_steps, num_envs); targets/time are (1, T_steps)",
        "variables": variables,
    }
