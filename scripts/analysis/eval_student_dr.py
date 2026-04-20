#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause
"""Evaluate a student policy (student encoder + teacher actor) across DR levels.

This script reuses eval_dr_fulldof.py's DR sweep machinery (build_step_trajectory,
apply_dr_config, run_evaluation, compute_metrics, generate_plots) and swaps the
policy callable for a StudentInLoopPolicy.

Usage:
    ./isaaclab.sh -p scripts/analysis/eval_student_dr.py \
        --teacher_ckpt logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/model_4999.pt \
        --student_ckpt logs/rsl_rl/student_policy/.../models/student_999.pt \
        --encoder_type tcn \
        --num_envs 64 --headless
"""

import argparse
import os
import sys

# Dependencies in sibling/parent script dirs
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))
sys.path.insert(0, os.path.dirname(__file__))

from isaaclab.app import AppLauncher
import cli_args  # noqa: E402, F401

parser = argparse.ArgumentParser(description="Evaluate student policy across DR levels.")
parser.add_argument("--teacher_ckpt", type=str, required=True)
parser.add_argument("--student_ckpt", type=str, required=True)
parser.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], required=True)
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0")
parser.add_argument("--output_dir", type=str, default=None,
                    help="Default: <student_ckpt_dir>/../eval_dr/")
parser.add_argument("--segment_duration", type=float, default=5.0)
parser.add_argument("--seed", type=int, default=42)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest follows."""
import gymnasium as gym
import numpy as np
import torch

from isaaclab.envs import DirectRLEnvCfg
from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils.hydra import hydra_task_config

# Reuse eval_dr_fulldof sweep machinery
import eval_dr_fulldof as edf  # type: ignore[import-not-found]
from common import DR_LEVELS, DR_SCALE  # type: ignore[import-not-found]

from isaaclab_tasks.direct.constrained_full_albc.student.eval import build_student_policy_fn


def _wrap_policy_for_eval(student_policy):
    """Adapt StudentInLoopPolicy to the policy callable signature used by run_evaluation.

    eval_dr_fulldof invokes `policy(obs)` where obs is already a tensordict.
    Our StudentInLoopPolicy matches that signature directly.
    """
    return student_policy


class _StudentPolicyNN:
    """Stub object exposing the `.reset(env_ids)` interface that run_evaluation
    expects on `policy_nn`. Delegates to StudentInLoopPolicy.reset.
    """

    def __init__(self, student_policy):
        self._student = student_policy

    def reset(self, env_ids):
        if env_ids is None:
            self._student.reset(None)
            return
        if isinstance(env_ids, torch.Tensor):
            self._student.reset(env_ids)
        else:
            self._student.reset(torch.as_tensor(env_ids, dtype=torch.long))


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    # ---- Env config overrides (mirror eval_dr_fulldof main) ----
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.play_mode = True
    env_cfg.vel_cmd_resample_steps = 0
    if hasattr(env_cfg, "observation_noise_model"):
        env_cfg.observation_noise_model = None
    env_cfg.max_attitude_angle = 2.5
    env_cfg.debug_vis = False
    env_cfg.seed = args_cli.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    if hasattr(env_cfg, "doraemon"):
        env_cfg.doraemon.enable = False
    env_cfg.episode_length_s = edf.TRAJECTORY_N_SEGMENTS * args_cli.segment_duration + 10.0

    # ---- Output directory ----
    if args_cli.output_dir:
        output_dir = args_cli.output_dir
    else:
        output_dir = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(args_cli.student_ckpt))),
            "eval_dr",
        )
    os.makedirs(output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {output_dir}")

    # ---- DORAEMON DR (disabled — student does not come with DORAEMON state) ----
    print("[INFO] DORAEMON-DR disabled. Hard DR = HardDomainRandomizationCfg (static).\n")

    # ---- Create env (initial DR = none) ----
    edf.apply_dr_config(env_cfg, DR_SCALE["none"])
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device

    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")

    # ---- Build student-in-loop policy ----
    student_policy = build_student_policy_fn(
        teacher_ckpt=args_cli.teacher_ckpt,
        student_ckpt=args_cli.student_ckpt,
        encoder_type=args_cli.encoder_type,
        num_envs=num_envs,
        device=str(device),
    )
    policy = _wrap_policy_for_eval(student_policy)
    policy_nn = _StudentPolicyNN(student_policy)
    print(f"[INFO] Loaded student ({args_cli.encoder_type}) from {args_cli.student_ckpt}")
    print(f"[INFO] Teacher actor (frozen) from {args_cli.teacher_ckpt}")

    # ---- Build trajectory (same for all DR levels) ----
    time_s, targets, segment_names, warmup_steps = edf.build_step_trajectory(
        segment_duration=args_cli.segment_duration,
        step_dt=step_dt,
    )
    print(
        f"[INFO] Trajectory: {len(segment_names)} segs x {args_cli.segment_duration}s = "
        f"{len(time_s)} steps ({time_s[-1]:.0f}s), warmup={edf.WARMUP_SEGMENTS} segs ({warmup_steps} steps)"
    )

    # ---- Run evaluation for each DR level ----
    all_data = {}
    all_metrics = {}

    for level in DR_LEVELS:
        dr_pct = int(DR_SCALE[level] * 100)
        print(f"\n{'=' * 60}")
        print(f"  DR Level: {level.upper()} | DR Scale: {dr_pct}%")
        print(f"{'=' * 60}")

        edf.apply_dr_config(raw_env.cfg, DR_SCALE[level])

        data = edf.run_evaluation(
            env=env,
            policy=policy,
            policy_nn=policy_nn,
            raw_env=raw_env,
            time_s=time_s,
            targets=targets,
            segment_names=segment_names,
            segment_duration=args_cli.segment_duration,
            step_dt=step_dt,
            num_envs=num_envs,
            device=device,
        )
        all_data[level] = data

        np.savez_compressed(
            os.path.join(output_dir, f"eval_{level}.npz"),
            **{k: v for k, v in data.items() if isinstance(v, np.ndarray)},
        )

        metrics = edf.compute_metrics(data)
        all_metrics[level] = metrics

        print(f"\n  Results ({level}, DR {dr_pct}%):")
        print(
            f"    att_error={metrics['total_att_error']:.1f}+/-{metrics['total_att_error_std']:.1f} deg "
            f"ss_err={np.nanmean(metrics['att_ss_errors']):.2f} deg "
            f"os={np.nanmean(metrics['att_overshoot_pcts']):.1f}%"
        )
        print(
            f"    lv_error={metrics['total_lin_vel_error']:.3f} m/s "
            f"yaw_ss={np.nanmean(metrics['yaw_ss_errors']):.4f} "
            f"yaw_os={np.nanmean(metrics['yaw_overshoot_pcts']):.1f}% "
            f"survival={metrics['survival_rate']:.0f}%"
        )

    # ---- Generate plots ----
    print("\n[INFO] Generating plots...")
    edf.generate_plots(all_data, all_metrics, output_dir)

    # ---- Save summary (delegate to edf's enhanced_summary mechanism via the all_metrics structure) ----
    # eval_dr_fulldof writes enhanced_summary.json inside generate_plots or a sibling call.
    # If not, write a minimal summary here as a safety net.
    import json
    summary_path = os.path.join(output_dir, "enhanced_summary.json")
    if not os.path.exists(summary_path):
        # Minimal summary: per-level per-metric aggregates keyed by axis name.
        summary = {}
        for lvl in DR_LEVELS:
            m = all_metrics[lvl]
            summary[lvl] = {}
            # attitude
            for i, ax in enumerate(["roll", "pitch"]):
                summary[lvl][ax] = {
                    "ss_error": float(np.nanmean(m["att_ss_errors"][:, i]) if m["att_ss_errors"].ndim > 1 else np.nanmean(m["att_ss_errors"])),
                    "ss_jitter": float(np.nanmean(m["att_ss_jitters"][:, i]) if m["att_ss_jitters"].ndim > 1 else np.nanmean(m["att_ss_jitters"])),
                    "os_env_mean": float(np.nanmean(m["att_overshoot_pcts"])),
                }
            # lin vel
            for ax in ["vx", "vy", "vz"]:
                summary[lvl][ax] = {
                    "ss_error": float(np.nanmean(m["lin_vel_ss_errors"][ax])),
                    "ss_jitter": float(np.nanmean(m["lin_vel_ss_jitters"][ax])),
                    "os_env_mean": float(np.nanmean(m["lin_vel_overshoot_pcts"][ax])),
                }
            # yaw
            summary[lvl]["yaw"] = {
                "ss_error": float(np.nanmean(m["yaw_ss_errors"])),
                "ss_jitter": float(np.nanmean(m["yaw_ss_jitters"])),
                "os_env_mean": float(np.nanmean(m["yaw_overshoot_pcts"])),
            }
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[INFO] Wrote minimal summary: {summary_path}")

    print(f"\n[INFO] Done. Output: {output_dir}")
    env.close()


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]  -- hydra_task_config injects args
    simulation_app.close()
