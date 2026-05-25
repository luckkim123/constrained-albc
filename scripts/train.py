#!/usr/bin/env python3
# Copyright (c) 2026.
"""Overlay train entry for constrained-albc environments.

isaaclab stays a pristine upstream fork: its train.py only knows OnPolicyRunner /
DistillationRunner and only imports isaaclab_tasks. This overlay entry owns two
overlay concerns that must NOT live in isaaclab:

  1. Registration: a one-shot ``builtins.__import__`` hook imports ``constrained_albc``
     when ``isaaclab_tasks`` is imported (which is AFTER AppLauncher boots SimulationApp,
     so the USD ``pxr`` runtime exists), triggering the overlay's gym.register() calls.
  2. Runner dispatch: a ``_RUNNER_MAP`` for the two custom runners
     (ConstraintEncoderRunner, OnPolicyDoraemonRunner) that upstream train.py does not know.

Everything else (argparse, AppLauncher, rsl-rl version check, main() body) is replicated
from upstream/main ``scripts/reinforcement_learning/rsl_rl/train.py`` so this entry tracks
upstream behavior. When rebasing isaaclab onto a newer upstream, diff that file against
this main() body to catch drift.

Usage (run via isaaclab's runtime):
    cd /workspace/isaaclab && ./isaaclab.sh -p \
        /workspace/constrained-albc/scripts/train.py \
        --task Isaac-FullDOF-TRPO-v0 --num_envs 4 --headless
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import builtins
import os
import sys

from isaaclab.app import AppLauncher

# Make upstream cli_args importable (it lives next to upstream train.py and uses
# `import cli_args  # isort: skip`, relying on sys.path).
ISAACLAB_PATH = os.environ.get("ISAACLAB_PATH", "/workspace/isaaclab")
UPSTREAM_RL_DIR = os.path.join(ISAACLAB_PATH, "scripts", "reinforcement_learning", "rsl_rl")
if UPSTREAM_RL_DIR not in sys.path:
    sys.path.insert(0, UPSTREAM_RL_DIR)

import cli_args  # isort: skip

# One-shot post-import hook: import constrained_albc the moment isaaclab_tasks is
# imported below (after AppLauncher has booted, so pxr exists), to register overlay envs.
_real_import = builtins.__import__
_overlay_loaded = False


def _import_with_overlay(name, *args, **kwargs):
    module = _real_import(name, *args, **kwargs)
    global _overlay_loaded
    if not _overlay_loaded and name == "isaaclab_tasks":
        _overlay_loaded = True
        import constrained_albc  # noqa: F401  triggers gym.register()
    return module


builtins.__import__ = _import_with_overlay

# add argparse arguments
parser = argparse.ArgumentParser(description="Train an RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record videos during training.")
parser.add_argument("--video_length", type=int, default=200, help="Length of the recorded video (in steps).")
parser.add_argument("--video_interval", type=int, default=2000, help="Interval between video recordings (in steps).")
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default=None, help="Name of the task.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="Name of the RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument("--max_iterations", type=int, default=None, help="RL Policy training iterations.")
parser.add_argument(
    "--distributed", action="store_true", default=False, help="Run training with multiple GPUs or nodes."
)
parser.add_argument("--export_io_descriptors", action="store_true", default=False, help="Export IO descriptors.")
parser.add_argument(
    "--ray-proc-id", "-rid", type=int, default=None, help="Automatically configured by Ray integration, otherwise None."
)
# append RSL-RL cli arguments
cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

# always enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Check for minimum supported RSL-RL version."""

import importlib.metadata as metadata
import platform

from packaging import version

# check minimum supported rsl-rl version
RSL_RL_VERSION = "3.0.1"
installed_version = metadata.version("rsl-rl-lib")
if version.parse(installed_version) < version.parse(RSL_RL_VERSION):
    if platform.system() == "Windows":
        cmd = [r".\isaaclab.bat", "-p", "-m", "pip", "install", f"rsl-rl-lib=={RSL_RL_VERSION}"]
    else:
        cmd = ["./isaaclab.sh", "-p", "-m", "pip", "install", f"rsl-rl-lib=={RSL_RL_VERSION}"]
    print(
        f"Please install the correct version of RSL-RL.\nExisting version is: '{installed_version}'"
        f" and required version is: '{RSL_RL_VERSION}'.\nTo install the correct version, run:"
        f"\n\n\t{' '.join(cmd)}\n"
    )
    exit(1)

"""Rest everything follows."""

import logging
import time
from datetime import datetime

import gymnasium as gym
import torch
from rsl_rl.runners import DistillationRunner, OnPolicyRunner

from isaaclab.envs import (
    DirectMARLEnv,
    DirectMARLEnvCfg,
    DirectRLEnvCfg,
    ManagerBasedRLEnvCfg,
    multi_agent_to_single_agent,
)
from isaaclab.utils.dict import print_dict
from isaaclab.utils.io import dump_yaml

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# Overlay-owned runner dispatch (the one divergence from upstream train.py).
from constrained_albc.envs.constrained_full_albc.runners import (
    ConstraintEncoderRunner,
    OnPolicyDoraemonRunner,
)

# import logger
logger = logging.getLogger(__name__)

_RUNNER_MAP = {
    "FullDOFConstraintEncoderRunner": ConstraintEncoderRunner,
    "OnPolicyDoraemonRunner": OnPolicyDoraemonRunner,
}

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True
torch.backends.cudnn.deterministic = False
torch.backends.cudnn.benchmark = False


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    """Train with RSL-RL agent."""
    # override configurations with non-hydra CLI arguments
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs
    agent_cfg.max_iterations = (
        args_cli.max_iterations if args_cli.max_iterations is not None else agent_cfg.max_iterations
    )

    # set the environment seed
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device
    if args_cli.distributed and args_cli.device is not None and "cpu" in args_cli.device:
        raise ValueError(
            "Distributed training is not supported when using CPU device. "
            "Please use GPU device (e.g., --device cuda) for distributed training."
        )

    # multi-gpu training configuration
    if args_cli.distributed:
        env_cfg.sim.device = f"cuda:{app_launcher.local_rank}"
        agent_cfg.device = f"cuda:{app_launcher.local_rank}"
        seed = agent_cfg.seed + app_launcher.local_rank
        env_cfg.seed = seed
        agent_cfg.seed = seed

    # specify directory for logging experiments
    log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
    log_root_path = os.path.abspath(log_root_path)
    print(f"[INFO] Logging experiment in directory: {log_root_path}")
    log_dir = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    print(f"Exact experiment name requested from command line: {log_dir}")
    if agent_cfg.run_name:
        log_dir += f"_{agent_cfg.run_name}"
    log_dir = os.path.join(log_root_path, log_dir)

    # Point <experiment>/latest at this run so tools reach the newest run without
    # knowing its timestamp (e.g. tensorboard --logdir logs/rsl_rl/<exp>/latest).
    from constrained_albc.envs.constrained_full_albc.utils import update_latest_symlink

    os.makedirs(log_dir, exist_ok=True)
    update_latest_symlink(log_dir)

    # set the IO descriptors export flag if requested
    if isinstance(env_cfg, ManagerBasedRLEnvCfg):
        env_cfg.export_io_descriptors = args_cli.export_io_descriptors
    else:
        logger.warning(
            "IO descriptors are only supported for manager based RL environments. No IO descriptors will be exported."
        )

    env_cfg.log_dir = log_dir

    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)

    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    if agent_cfg.resume or agent_cfg.algorithm.class_name == "Distillation":
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "train"),
            "step_trigger": lambda step: step % args_cli.video_interval == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording videos during training.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    start_time = time.time()

    # wrap around environment for rsl-rl
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    # create runner from rsl-rl (overlay-owned dispatch for custom runners)
    runner_cls = _RUNNER_MAP.get(agent_cfg.class_name)
    if runner_cls is not None:
        print(f"[INFO] Using overlay runner {runner_cls.__name__} for training.")
        runner = runner_cls(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    elif agent_cfg.class_name == "OnPolicyRunner":
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    elif agent_cfg.class_name == "DistillationRunner":
        runner = DistillationRunner(env, agent_cfg.to_dict(), log_dir=log_dir, device=agent_cfg.device)
    else:
        raise ValueError(f"Unsupported runner class: {agent_cfg.class_name}")

    # write git state to logs
    runner.add_git_repo_to_log(__file__)
    if agent_cfg.resume or agent_cfg.algorithm.class_name == "Distillation":
        print(f"[INFO]: Loading model checkpoint from: {resume_path}")
        runner.load(resume_path)

    # dump the configuration into log-directory
    dump_yaml(os.path.join(log_dir, "params", "env.yaml"), env_cfg)
    dump_yaml(os.path.join(log_dir, "params", "agent.yaml"), agent_cfg)

    # --- overlay: run_id single-tree manifest (minimal-touch; training output stays in log_dir) ---
    # Emit experiments/<run_id>/ as a tracing entry point: manifest.json + copied configs +
    # a `train` symlink back to this log_dir. This does NOT move tb/checkpoints/resume -- the
    # run_id tree only indexes the existing output so analyze/compare can resolve a run by id.
    # Best-effort: a manifest failure must never abort training (the model is already safe in
    # log_dir). See docs/explanation/run-id-tree-design.md section 4 #1.
    try:
        from constrained_albc.analysis.paths import emit_run_manifest

        run = emit_run_manifest(
            task=args_cli.task,
            log_dir=log_dir,
            tag=agent_cfg.run_name or None,
            config={
                "num_envs": env_cfg.scene.num_envs,
                "max_iterations": agent_cfg.max_iterations,
                "seed": agent_cfg.seed,
                "experiment_name": agent_cfg.experiment_name,
            },
        )
        print(f"[INFO] run_id tree: experiments/{run.run_id} (manifest + train -> {log_dir})")
    except Exception as exc:  # noqa: BLE001  manifest is auxiliary; never block training
        print(f"[WARN] run_id manifest emission failed (training continues): {exc}")

    # run training
    runner.learn(num_learning_iterations=agent_cfg.max_iterations, init_at_random_ep_len=True)

    print(f"Training time: {round(time.time() - start_time, 2)} seconds")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
