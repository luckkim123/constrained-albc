#!/usr/bin/env python3
# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause
"""Train a student policy (TCN or GRU) via behavior cloning from a teacher checkpoint.

Usage (run via isaaclab's runtime; this script lives in the constrained-albc repo):
    cd /workspace/isaaclab && ./isaaclab.sh -p /workspace/constrained-albc/scripts/train_student.py \
        --encoder_type tcn \
        --teacher_run_dir logs/rsl_rl/fulldof_albc/2026-04-20_20-08-38_r13_A \
        --teacher_checkpoint model_4999.pt \
        --num_envs 4096 --max_iterations 1000 --headless
"""

import argparse
import os
import sys

from isaaclab.app import AppLauncher

parser = argparse.ArgumentParser(description="Train student policy from teacher checkpoint.")
parser.add_argument("--task", type=str, default="Isaac-ConstrainedALBC-TRPO-v0")
parser.add_argument("--encoder_type", type=str, choices=["tcn", "gru"], required=True)
parser.add_argument(
    "--run_name", type=str, default=None, help="Override auto-named run (default: student_<encoder_type>)."
)
parser.add_argument("--teacher_run_dir", type=str, required=True,
                    help="Run directory of the trained teacher to distill from (contains the checkpoint).")
parser.add_argument("--teacher_checkpoint", type=str, default="model_4999.pt")
parser.add_argument("--num_envs", type=int, default=4096)
parser.add_argument("--max_iterations", type=int, default=1000)
parser.add_argument("--n_steps_per_rollout", type=int, default=24)
parser.add_argument("--n_epochs", type=int, default=5)
parser.add_argument("--minibatch_size", type=int, default=8192)
parser.add_argument("--lr", type=float, default=5e-4)
parser.add_argument("--lambda_latent", type=float, default=1.0)
parser.add_argument("--save_interval", type=int, default=100)
parser.add_argument("--gru_hidden", type=int, default=None,
                    help="GRU hidden size (default: StudentCfg.gru_hidden).")
parser.add_argument("--gru_head_hidden", type=int, default=None,
                    help="GRU head intermediate dim (0=disable, default: StudentCfg.gru_head_hidden).")
parser.add_argument("--seed", type=int, default=42)
parser.add_argument("--logger", type=str, default="wandb", choices=["wandb", "tensorboard"])
parser.add_argument("--wandb_project", type=str, default="attitude_only_student")
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

# Clear out sys.argv for Hydra: only hydra-style args remain.
sys.argv = [sys.argv[0]] + hydra_args

# Launch Omniverse app (required before importing isaaclab_tasks)
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest follows."""
import logging
import time
from datetime import datetime

import gymnasium as gym
import torch

from isaaclab.envs import DirectRLEnvCfg

from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils.hydra import hydra_task_config

from constrained_albc.envs.main.student.config import StudentCfg
from constrained_albc.envs.main.student.runner import StudentRunner

logging.basicConfig(level=logging.INFO, format="[%(asctime)s] %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("train_student")


@hydra_task_config(args_cli.task, "rsl_rl_cfg_entry_point")
def main(env_cfg: DirectRLEnvCfg, _agent_cfg) -> None:
    """Hydra-decorated entry: receives env_cfg from the task registry."""
    # Build student cfg from CLI
    cfg = StudentCfg()
    cfg.encoder_type = args_cli.encoder_type
    cfg.teacher_run_dir = args_cli.teacher_run_dir
    cfg.teacher_checkpoint = args_cli.teacher_checkpoint
    cfg.num_envs = args_cli.num_envs
    cfg.max_iterations = args_cli.max_iterations
    cfg.n_steps_per_rollout = args_cli.n_steps_per_rollout
    cfg.n_epochs = args_cli.n_epochs
    cfg.minibatch_size = args_cli.minibatch_size
    cfg.lr = args_cli.lr
    cfg.lambda_latent = args_cli.lambda_latent
    cfg.save_interval = args_cli.save_interval
    cfg.seed = args_cli.seed
    cfg.logger = args_cli.logger
    cfg.wandb_project = args_cli.wandb_project
    cfg.task = args_cli.task
    cfg.run_name = args_cli.run_name or f"student_{args_cli.encoder_type}"
    if args_cli.gru_hidden is not None:
        cfg.gru_hidden = args_cli.gru_hidden
    if args_cli.gru_head_hidden is not None:
        cfg.gru_head_hidden = args_cli.gru_head_hidden

    # Log dir. cfg.log_dir_root is an absolute constrained-albc path (student/config.py),
    # so student output lands in the constrained-albc repo even though this script runs from
    # /workspace/isaaclab via isaaclab.sh -- it must NOT resolve against the isaaclab cwd.
    # Leaf is built via make_run_id (== the experiments run_id) so logs/ and experiments/
    # share one identical name (<task_short>_<run_name>_<ts>, tag-time), matching the teacher.
    from constrained_albc.analysis.paths import RUN_TS_FORMAT, make_run_id

    stamp = datetime.now().strftime(RUN_TS_FORMAT)
    log_dir = os.path.join(cfg.log_dir_root, make_run_id(cfg.task, tag=cfg.run_name, ts=stamp))
    os.makedirs(log_dir, exist_ok=True)
    logger.info("log_dir=%s", log_dir)

    # Apply our overrides on the hydra-supplied env_cfg
    env_cfg.scene.num_envs = cfg.num_envs
    env_cfg.seed = cfg.seed
    env_cfg.sim.device = cfg.device
    env_cfg.log_dir = log_dir

    # Build env
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
    env = RslRlVecEnvWrapper(env, clip_actions=None)

    device = torch.device(cfg.device)
    runner = StudentRunner(env=env, cfg=cfg, log_dir=log_dir, device=device)

    # --- overlay: run_id single-tree manifest for the student (minimal-touch) ---
    # Student is a child of the teacher: emit experiments/<student_run_id>/ with kind="student"
    # and link to the teacher via parent_run_id when the teacher lives in a run_id tree
    # (design section 2-C Option B). Training output stays in log_dir. Best-effort: a manifest
    # failure must never abort training.
    try:
        from constrained_albc.analysis.paths import emit_run_manifest, run_id_from_path

        parent = run_id_from_path(cfg.teacher_run_dir)
        # experiments_root is anchored to the constrained-albc repo (sibling of log_dir_root),
        # NOT the isaaclab cwd this script runs from -- otherwise the student experiments tree
        # leaks into /workspace/isaaclab/experiments. log_dir_root is
        # <repo>/logs/rsl_rl/<exp>, so the repo root is three levels up.
        repo_root = os.path.dirname(os.path.dirname(os.path.dirname(cfg.log_dir_root)))
        experiments_root = os.path.join(repo_root, "experiments")
        run = emit_run_manifest(
            task=args_cli.task,
            log_dir=log_dir,
            tag=cfg.run_name or None,
            experiment_name=cfg.experiment_name,
            experiments_root=experiments_root,
            kind="student",
            parent_run_id=parent,
            config={
                "num_envs": cfg.num_envs,
                "seed": cfg.seed,
                "experiment_name": cfg.experiment_name,
                "teacher_run_dir": cfg.teacher_run_dir,
            },
        )
        logger.info("run_id tree: experiments/%s (student, parent=%s)", run.run_id, parent)
    except Exception as exc:  # noqa: BLE001  manifest is auxiliary; never block training
        logger.warning("run_id manifest emission failed (training continues): %s", exc)

    t0 = time.time()
    try:
        runner.learn()
    finally:
        env.close()
        logger.info("Total wall time: %.1f min", (time.time() - t0) / 60.0)


if __name__ == "__main__":
    main()  # pyright: ignore[reportCallIssue]  -- hydra_task_config injects args
    simulation_app.close()
