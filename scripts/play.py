#!/usr/bin/env python3
# Copyright (c) 2026.
"""Overlay play entry for constrained-albc environments.

Loads a trained checkpoint and rolls the policy out for visual inspection
(GUI / livestream / video). Counterpart to ``scripts/train.py``; quantitative
DR evaluation lives in ``analysis/eval_dr.py`` (see CLAUDE.md).

isaaclab stays a pristine upstream fork: its ``rsl_rl/play.py`` only knows
``OnPolicyRunner`` / ``DistillationRunner``. This overlay entry owns the two
overlay concerns that must NOT live in isaaclab (same as train.py):

  1. Registration: a one-shot ``builtins.__import__`` hook imports
     ``constrained_albc`` when ``isaaclab_tasks`` is imported (AFTER AppLauncher
     boots SimulationApp so the USD ``pxr`` runtime exists).
  2. Runner dispatch: a ``_RUNNER_MAP`` for the custom runner
     (ConstraintEncoderRunner) that upstream play.py does not know.

The policy-load path (runner_map + ``_runner_module`` monkeypatch +
``runner.load(..., load_optimizer=False)``) mirrors the VERIFIED loader in
``analysis/eval_dr.py:2353-2360`` so play and eval agree on how a ALBC policy
is reconstructed. jit/onnx export is intentionally omitted (the encoder +
asymmetric-critic structure is not export-validated; eval_dr does not export
either).

Usage (run via isaaclab's runtime):
    cd /workspace/isaaclab && ./isaaclab.sh -p \
        /workspace/constrained-albc/scripts/play.py \
        --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 16 \
        --checkpoint /path/to/model_4999.pt
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import builtins
import os
import sys

from isaaclab.app import AppLauncher

# Make upstream cli_args importable (it lives next to upstream play.py and uses
# `import cli_args`, relying on sys.path).
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
parser = argparse.ArgumentParser(description="Play a trained RL agent with RSL-RL.")
parser.add_argument("--video", action="store_true", default=False, help="Record a video during playback.")
parser.add_argument("--video_length", type=int, default=600, help="Length of the recorded video (in steps).")
parser.add_argument("--num_envs", type=int, default=None, help="Number of environments to simulate.")
parser.add_argument("--task", type=str, default="Isaac-ConstrainedALBC-TRPO-v0", help="Name of the task.")
parser.add_argument(
    "--agent", type=str, default="rsl_rl_cfg_entry_point", help="Name of the RL agent configuration entry point."
)
parser.add_argument("--seed", type=int, default=None, help="Seed used for the environment")
parser.add_argument("--real-time", action="store_true", default=False, help="Run in real-time, if possible.")
# append RSL-RL cli arguments (provides --checkpoint, --load_run, --load_checkpoint, --device, ...)
cli_args.add_rsl_rl_args(parser)
# append AppLauncher cli args
AppLauncher.add_app_launcher_args(parser)
# parse the arguments
args_cli, hydra_args = parser.parse_known_args()
# enable cameras to record video
if args_cli.video:
    args_cli.enable_cameras = True

# clear out sys.argv for Hydra
sys.argv = [sys.argv[0]] + hydra_args

# launch omniverse app
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import time

import gymnasium as gym
import torch
import rsl_rl.runners.on_policy_runner as _runner_module
from rsl_rl.runners import OnPolicyRunner

from isaaclab.envs import DirectMARLEnv, DirectMARLEnvCfg, DirectRLEnvCfg, ManagerBasedRLEnvCfg, multi_agent_to_single_agent
from isaaclab.utils.assets import retrieve_file_path
from isaaclab.utils.dict import print_dict

from isaaclab_rl.rsl_rl import RslRlBaseRunnerCfg, RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# Overlay-owned runner dispatch (same divergence from upstream as train.py).
from constrained_albc.envs.main.runners import ConstraintEncoderRunner

# rsl-rl resolves the runner by class name from agent_cfg; register the overlay
# runner on the module it looks in (mirrors eval_dr.py:249).
_runner_module.ALBCConstraintEncoderRunner = ConstraintEncoderRunner

_RUNNER_MAP = {"ALBCConstraintEncoderRunner": ConstraintEncoderRunner}

torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg: ManagerBasedRLEnvCfg | DirectRLEnvCfg | DirectMARLEnvCfg, agent_cfg: RslRlBaseRunnerCfg):
    """Play with the trained RSL-RL agent."""
    # override configurations with non-hydra CLI arguments
    agent_cfg = cli_args.update_rsl_rl_cfg(agent_cfg, args_cli)
    env_cfg.scene.num_envs = args_cli.num_envs if args_cli.num_envs is not None else env_cfg.scene.num_envs

    # set the environment seed (some randomizations occur at init)
    env_cfg.seed = agent_cfg.seed
    env_cfg.sim.device = args_cli.device if args_cli.device is not None else env_cfg.sim.device

    # resolve checkpoint (mirrors eval_dr.py:2202-2205)
    log_root_path = os.path.abspath(os.path.join("logs", "rsl_rl", agent_cfg.experiment_name))
    print(f"[INFO] Loading experiment from directory: {log_root_path}")
    if args_cli.checkpoint and args_cli.checkpoint != "none":
        resume_path = retrieve_file_path(args_cli.checkpoint)
    else:
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
    log_dir = os.path.dirname(resume_path)
    env_cfg.log_dir = log_dir

    # create isaac environment
    env = gym.make(args_cli.task, cfg=env_cfg, render_mode="rgb_array" if args_cli.video else None)
    if isinstance(env.unwrapped, DirectMARLEnv):
        env = multi_agent_to_single_agent(env)

    # wrap for video recording
    if args_cli.video:
        video_kwargs = {
            "video_folder": os.path.join(log_dir, "videos", "play"),
            "step_trigger": lambda step: step == 0,
            "video_length": args_cli.video_length,
            "disable_logger": True,
        }
        print("[INFO] Recording a video during playback.")
        print_dict(video_kwargs, nesting=4)
        env = gym.wrappers.RecordVideo(env, **video_kwargs)

    # wrap for rsl-rl
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    print(f"[INFO]: Loading model checkpoint from: {resume_path}")
    device = env.unwrapped.device
    agent_dict = agent_cfg.to_dict()
    runner_cls = _RUNNER_MAP.get(agent_cfg.class_name)
    if runner_cls is not None:
        runner = runner_cls(env, agent_dict, log_dir=None, device=agent_cfg.device)
    else:
        runner = OnPolicyRunner(env, agent_dict, log_dir=None, device=agent_cfg.device)
    runner.load(resume_path, load_optimizer=False)

    # deterministic inference policy
    policy = runner.get_inference_policy(device=device)
    policy_nn = runner.alg.policy if hasattr(runner.alg, "policy") else runner.alg.actor_critic

    dt = env.unwrapped.step_dt

    # reset and roll out
    obs = env.get_observations()
    timestep = 0
    while simulation_app.is_running():
        start_time = time.time()
        with torch.inference_mode():
            actions = policy(obs)
            obs, _, dones, _ = env.step(actions)
            if hasattr(policy_nn, "reset"):
                policy_nn.reset(dones)
        if args_cli.video:
            timestep += 1
            if timestep == args_cli.video_length:
                break
        # real-time pacing
        sleep_time = dt - (time.time() - start_time)
        if args_cli.real_time and sleep_time > 0:
            time.sleep(sleep_time)

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
