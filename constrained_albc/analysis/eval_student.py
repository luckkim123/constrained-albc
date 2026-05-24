#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Student-policy evaluation for constrained_full_albc (Isaac Sim required).

Subcommands:
    dr      evaluate student (student encoder + teacher actor) across DR levels
    latent  record per-step (l_hat, l_true) during student eval

Usage:
    ./isaaclab.sh -p scripts/analysis/eval_student.py dr --task Isaac-FullDOF-TRPO-v0 --num_envs 64 --headless
    ./isaaclab.sh -p scripts/analysis/eval_student.py latent --task Isaac-FullDOF-TRPO-v0 --headless
"""

import argparse
import os
import sys

# cli_args is vendored locally (was scripts/reinforcement_learning/rsl_rl/ in isaaclab, not migrated)
sys.path.insert(0, os.path.dirname(__file__))

import cli_args  # noqa: E402, F401

from isaaclab.app import AppLauncher


def _add_common(sp: argparse.ArgumentParser) -> None:
    """Add args shared by both subcommands."""
    # Register app-launcher flags on the subparser so they parse when placed after
    # the subcommand token (subparsers own args that follow the subcommand). This must
    # run before the required args below: add_app_launcher_args() does an internal
    # parse_known_args() for collision checks, which would abort on missing required
    # args or the subcommand token, so we neutralize sys.argv around the call.
    _saved_argv = sys.argv
    sys.argv = [sys.argv[0]]
    try:
        AppLauncher.add_app_launcher_args(sp)
    finally:
        sys.argv = _saved_argv
    sp.add_argument("--teacher_ckpt", type=str, required=True)
    sp.add_argument("--student_ckpt", type=str, required=True)
    sp.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], required=True)
    sp.add_argument("--num_envs", type=int, default=64)
    sp.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0")
    sp.add_argument("--segment_duration", type=float, default=5.0)
    sp.add_argument("--seed", type=int, default=42)
    cli_args.add_rsl_rl_args(sp)


parser = argparse.ArgumentParser(description="Student-policy evaluation for constrained_full_albc.")
subparsers = parser.add_subparsers(dest="mode", required=True)

# dr: evaluate student across DR levels
sp_dr = subparsers.add_parser("dr", description="Evaluate student policy across DR levels.")
_add_common(sp_dr)
sp_dr.add_argument("--output_dir", type=str, default=None,
                   help="Default: <student_ckpt_dir>/../eval_dr/")

# latent: record per-step (l_hat, l_true)
sp_latent = subparsers.add_parser("latent", description="Diagnostic eval: log (l_hat, l_true) per step.")
_add_common(sp_latent)
sp_latent.add_argument("--output_dir", type=str, required=True)

args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest follows."""
# Reuse eval_dr sweep machinery (static-mode helpers live at module top)
import eval_dr as edf  # type: ignore[import-not-found]
import gymnasium as gym
import numpy as np
import torch
from common import DR_LEVELS, DR_SCALE  # type: ignore[import-not-found]

from isaaclab.envs import DirectRLEnvCfg

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from constrained_albc.envs.constrained_full_albc.student.eval import (
    StudentInLoopPolicy,
    build_student_policy_fn,
)
from isaaclab_tasks.utils.hydra import hydra_task_config


# =====================================================================================
# dr subcommand
# =====================================================================================
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


def run_dr(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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
            att_ss = np.asarray(m["att_ss_errors"])
            att_jit = np.asarray(m["att_ss_jitters"])
            att_os = np.asarray(m["att_overshoot_pcts"])
            for i, ax in enumerate(["roll", "pitch"]):
                summary[lvl][ax] = {
                    "ss_error": float(np.nanmean(att_ss[:, i]) if att_ss.ndim > 1 else np.nanmean(att_ss)),
                    "ss_jitter": float(np.nanmean(att_jit[:, i]) if att_jit.ndim > 1 else np.nanmean(att_jit)),
                    "os_env_mean": float(np.nanmean(att_os)),
                }
            for ax in ["vx", "vy", "vz"]:
                summary[lvl][ax] = {
                    "ss_error": float(np.nanmean(np.asarray(m["lin_vel_ss_errors"][ax]))),
                    "ss_jitter": float(np.nanmean(np.asarray(m["lin_vel_ss_jitters"][ax]))),
                    "os_env_mean": float(np.nanmean(np.asarray(m["lin_vel_overshoot_pcts"][ax]))),
                }
            summary[lvl]["yaw"] = {
                "ss_error": float(np.nanmean(np.asarray(m["yaw_ss_errors"]))),
                "ss_jitter": float(np.nanmean(np.asarray(m["yaw_ss_jitters"]))),
                "os_env_mean": float(np.nanmean(np.asarray(m["yaw_overshoot_pcts"]))),
            }
        with open(summary_path, "w") as f:
            json.dump(summary, f, indent=2)
        print(f"[INFO] Wrote minimal summary: {summary_path}")

    print(f"\n[INFO] Done. Output: {output_dir}")
    env.close()


# =====================================================================================
# latent subcommand
# =====================================================================================
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


def run_latent(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
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
        print("  per-dim MSE: " + " ".join(f"{v:.4f}" for v in s["per_dim_mse"]))
        print(f"  l_true envvar (mean dim/t): {s['l_true_envvar_mean']:.5f}")
        print(f"  l_hat  envvar (mean dim/t): {s['l_hat_envvar_mean']:.5f}")
        print(f"  l_true tvar   (mean dim/e): {s['l_true_tvar_mean']:.5f}")
        print(f"  l_hat  tvar   (mean dim/e): {s['l_hat_tvar_mean']:.5f}")
        print(f"  per-env RMSE: mean={s['per_env_rmse_mean']:.4f} std={s['per_env_rmse_std']:.4f}")

    with open(os.path.join(args_cli.output_dir, "latent_summary.json"), "w") as f:
        json.dump(summary, f, indent=2)
    print(f"\n[INFO] Summary written: {os.path.join(args_cli.output_dir, 'latent_summary.json')}")
    env.close()


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(env_cfg: DirectRLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    if args_cli.mode == "dr":
        run_dr(env_cfg, agent_cfg)
    elif args_cli.mode == "latent":
        run_latent(env_cfg, agent_cfg)


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]  -- hydra_task_config injects args
    simulation_app.close()
