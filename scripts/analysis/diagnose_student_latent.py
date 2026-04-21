#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# SPDX-License-Identifier: BSD-3-Clause
"""Diagnostic: record per-step (l_hat, l_true) during student eval.

Runs the same DR sweep trajectory as eval_student_dr.py but wraps the
student-in-loop policy with an instrumented version that also evaluates
teacher's privileged encoder at every step. Output: one latent_log_<level>.npz
per DR level, plus a terminal summary of MSE / variance ratios.

Purpose: disambiguate "is encoder prediction the bottleneck?" from other
candidate causes of the student-vs-teacher eval gap.

Usage:
    CUDA_VISIBLE_DEVICES=1 ./isaaclab.sh -p scripts/analysis/diagnose_student_latent.py \
        --teacher_ckpt logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A/model_4999.pt \
        --student_ckpt logs/rsl_rl/student_policy/.../models/student_999.pt \
        --encoder_type tcn \
        --output_dir logs/rsl_rl/student_policy/.../latent_diagnostic \
        --num_envs 64 --seed 42 --headless
"""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))
sys.path.insert(0, os.path.dirname(__file__))

from isaaclab.app import AppLauncher
import cli_args  # noqa: E402, F401

parser = argparse.ArgumentParser(description="Diagnostic eval: log (l_hat, l_true) per step.")
parser.add_argument("--teacher_ckpt", type=str, required=True)
parser.add_argument("--student_ckpt", type=str, required=True)
parser.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], required=True)
parser.add_argument("--num_envs", type=int, default=64)
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0")
parser.add_argument("--output_dir", type=str, required=True)
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

import eval_dr_fulldof as edf  # type: ignore[import-not-found]
from common import DR_LEVELS, DR_SCALE  # type: ignore[import-not-found]

from isaaclab_tasks.direct.constrained_full_albc.student.eval import (
    StudentInLoopPolicy,
    build_student_policy_fn,
)


class InstrumentedStudentPolicy:
    """Wraps a StudentInLoopPolicy; logs (l_hat, l_true) at every __call__.

    Replicates the forward pass of StudentInLoopPolicy.__call__ so we can
    capture intermediate tensors (l_hat before it becomes an action, and
    l_true computed from privileged obs via frozen teacher encoder). We do
    NOT call the underlying policy's __call__ to avoid double-advancing
    the ring buffer / hidden state.
    """

    def __init__(self, student: StudentInLoopPolicy) -> None:
        self._s = student
        self.l_hat_log: list[np.ndarray] = []
        self.l_true_log: list[np.ndarray] = []

    def reset_logs(self) -> None:
        self.l_hat_log = []
        self.l_true_log = []

    def reset(self, env_ids=None) -> None:
        self._s.reset(env_ids)

    @torch.no_grad()
    def __call__(self, obs_td) -> torch.Tensor:
        s = self._s
        obs = obs_td["policy"]
        priv = obs_td["privileged"]
        l_true = s.teacher.encode_privileged(priv)   # (B, 9)

        if s.cfg.encoder_type == "tcn":
            assert s.ring is not None
            s.ring = torch.roll(s.ring, shifts=-1, dims=1)
            s.ring[:, -1] = obs
            l_hat = s.student(s.ring)
        else:
            obs_for_student = s.obs_normalizer(obs)
            obs_seq = obs_for_student.unsqueeze(1)
            l_hat_seq, s.hidden = s.student(obs_seq, hidden=s.hidden)
            l_hat = l_hat_seq[:, -1]

        obs_normed = s.teacher.normalize_obs(obs)
        action = s.teacher.actor_forward(obs_normed, l_hat)

        self.l_hat_log.append(l_hat.detach().cpu().numpy())
        self.l_true_log.append(l_true.detach().cpu().numpy())
        return action


class _PolicyNNStub:
    def __init__(self, student: StudentInLoopPolicy) -> None:
        self._s = student

    def reset(self, env_ids) -> None:
        if env_ids is None:
            self._s.reset(None)
            return
        if isinstance(env_ids, torch.Tensor):
            self._s.reset(env_ids)
        else:
            self._s.reset(torch.as_tensor(env_ids, dtype=torch.long))


def _summarize_latent(l_hat: np.ndarray, l_true: np.ndarray) -> dict:
    err = l_hat - l_true  # (T, E, D)
    return {
        "overall_mse": float((err ** 2).mean()),
        "per_dim_mse": (err ** 2).mean(axis=(0, 1)).tolist(),
        "l_true_envvar_mean": float(l_true.var(axis=1).mean()),
        "l_hat_envvar_mean": float(l_hat.var(axis=1).mean()),
        "l_true_tvar_mean": float(l_true.var(axis=0).mean()),
        "l_hat_tvar_mean": float(l_hat.var(axis=0).mean()),
        "per_env_rmse_mean": float(np.sqrt((err ** 2).mean(axis=(0, 2))).mean()),
        "per_env_rmse_std": float(np.sqrt((err ** 2).mean(axis=(0, 2))).std()),
    }


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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

    os.makedirs(args_cli.output_dir, exist_ok=True)
    print(f"[INFO] Output directory: {args_cli.output_dir}")

    edf.apply_dr_config(env_cfg, DR_SCALE["none"])
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device
    print(f"[INFO] step_dt={step_dt:.4f}s, num_envs={num_envs}, device={device}")

    student = build_student_policy_fn(
        teacher_ckpt=args_cli.teacher_ckpt,
        student_ckpt=args_cli.student_ckpt,
        encoder_type=args_cli.encoder_type,
        num_envs=num_envs,
        device=str(device),
    )
    policy = InstrumentedStudentPolicy(student)
    policy_nn = _PolicyNNStub(student)
    print(f"[INFO] Loaded student ({args_cli.encoder_type}) from {args_cli.student_ckpt}")

    time_s, targets, segment_names, warmup_steps = edf.build_step_trajectory(
        segment_duration=args_cli.segment_duration,
        step_dt=step_dt,
    )
    print(
        f"[INFO] Trajectory: {len(segment_names)} segs x {args_cli.segment_duration}s = "
        f"{len(time_s)} steps"
    )

    import json

    summary = {"encoder_type": args_cli.encoder_type, "student_ckpt": args_cli.student_ckpt, "levels": {}}

    for level in DR_LEVELS:
        dr_pct = int(DR_SCALE[level] * 100)
        print(f"\n{'=' * 60}\n  DR: {level.upper()} ({dr_pct}%)\n{'=' * 60}")
        edf.apply_dr_config(raw_env.cfg, DR_SCALE[level])
        policy.reset_logs()

        edf.run_evaluation(
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

        l_hat_arr = np.stack(policy.l_hat_log, axis=0)    # (T, E, 9)
        l_true_arr = np.stack(policy.l_true_log, axis=0)  # (T, E, 9)
        np.savez_compressed(
            os.path.join(args_cli.output_dir, f"latent_log_{level}.npz"),
            l_hat=l_hat_arr,
            l_true=l_true_arr,
        )
        s = _summarize_latent(l_hat_arr, l_true_arr)
        summary["levels"][level] = s
        print(f"  overall MSE: {s['overall_mse']:.5f}")
        print(f"  per-dim MSE: " + " ".join(f"{v:.4f}" for v in s["per_dim_mse"]))
        print(f"  l_true envvar (mean dim/t): {s['l_true_envvar_mean']:.5f}")
        print(f"  l_hat  envvar (mean dim/t): {s['l_hat_envvar_mean']:.5f}")
        print(f"  l_true tvar   (mean dim/e): {s['l_true_tvar_mean']:.5f}")
        print(f"  l_hat  tvar   (mean dim/e): {s['l_hat_tvar_mean']:.5f}")
        print(f"  per-env RMSE: mean={s['per_env_rmse_mean']:.4f} std={s['per_env_rmse_std']:.4f}")

    with open(os.path.join(args_cli.output_dir, "latent_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[INFO] Summary written: {os.path.join(args_cli.output_dir, 'latent_summary.json')}")
    env.close()


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]
    simulation_app.close()
