# Copyright (c) 2022-2026, The Isaac Lab Project Developers.
# All rights reserved.
#
# SPDX-License-Identifier: BSD-3-Clause

"""Collect rollout data from a trained policy for offline encoder training.

Runs the trained history-only policy in inference mode, collecting per-step:
- policy_obs (14D): o_t
- privileged (23D): p_t (dynamics parameters)
- V_critic (1D): critic value prediction (supervision target for encoder)

The privileged obs are NOT used by the policy (history-only has state_space=0).
They are collected by overriding state_space=23 before env construction.

Usage:
    ./isaaclab.sh -p scripts/analysis/collect_rollouts.py \
        --task Isaac-Constrained-ALBC-HardDR-HistOnly-v0 \
        --num_envs 512 --num_episodes 50 --headless \
        --output logs/offline_encoder/rollout_data.pt
"""

"""Launch Isaac Sim Simulator first."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

parser = argparse.ArgumentParser(description="Collect rollout data for offline encoder training.")
parser.add_argument("--task", type=str, required=True, help="Task name.")
parser.add_argument("--num_envs", type=int, default=512, help="Number of parallel environments.")
parser.add_argument("--num_episodes", type=int, default=50, help="Number of complete episodes to collect.")
parser.add_argument("--output", type=str, required=True, help="Output .pt file path.")
parser.add_argument("--resume_path", type=str, default=None, help="Direct path to checkpoint .pt file.")
parser.add_argument("--seed", type=int, default=42, help="Random seed.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point", help="RSL-RL config entry point.")
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()
sys.argv = [sys.argv[0]] + hydra_args

app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

"""Rest everything follows."""

import gymnasium as gym
import torch
import rsl_rl.runners.on_policy_runner as _runner_module
from rsl_rl.runners import OnPolicyRunner

from isaaclab.utils.assets import retrieve_file_path

from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config

# Register custom classes for eval() resolution
from isaaclab_tasks.direct.constrained_albc.encoder import ActorCriticEncoder
from isaaclab_tasks.direct.constrained_albc.runners import ConstraintEncoderRunner

_runner_module.ALBCActorCriticEncoder = ActorCriticEncoder
_runner_module.ALBCConstraintEncoderRunner = ConstraintEncoderRunner


def collect_rollouts(
    env: RslRlVecEnvWrapper,
    policy_nn: torch.nn.Module,
    num_episodes: int,
    device: str,
) -> dict[str, torch.Tensor]:
    """Collect rollout data from trained policy.

    Args:
        env: Wrapped environment.
        policy_nn: Trained policy network.
        num_episodes: Number of complete episodes to collect.
        device: Torch device.

    Returns:
        Dict with keys: policy_obs, privileged, V_critic, reward.
        All tensors shape (total_steps, dim) on CPU.
    """
    policy_obs_list: list[torch.Tensor] = []
    privileged_list: list[torch.Tensor] = []
    v_critic_list: list[torch.Tensor] = []
    reward_list: list[torch.Tensor] = []

    obs = env.get_observations()
    episodes_done = 0
    step_count = 0

    print(f"Collecting {num_episodes} episodes from {env.num_envs} parallel envs...")

    with torch.inference_mode():
        while episodes_done < num_episodes:
            # Collect observations
            policy_obs_list.append(obs["policy"].cpu())
            privileged_list.append(obs["privileged"].cpu())

            # Get critic value
            v = policy_nn.evaluate(obs)
            v_critic_list.append(v.cpu())

            # Step
            actions = policy_nn.act_inference(obs)
            obs, rewards, dones, extras = env.step(actions)
            reward_list.append(rewards.cpu())

            # Count completed episodes
            num_done = dones.sum().item()
            episodes_done += num_done
            step_count += env.num_envs

            if step_count % (env.num_envs * 100) == 0:
                print(f"  steps={step_count}, episodes={episodes_done}/{num_episodes}")

    print(f"Collection complete: {step_count} steps, {episodes_done} episodes.")

    return {
        "policy_obs": torch.cat(policy_obs_list, dim=0),
        "privileged": torch.cat(privileged_list, dim=0),
        "V_critic": torch.cat(v_critic_list, dim=0).squeeze(-1),
        "reward": torch.cat(reward_list, dim=0),
    }


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg, agent_cfg):
    """Main entry point."""
    # Override state_space to collect privileged obs
    env_cfg.state_space = 23

    # Override num_envs
    env_cfg.scene.num_envs = args_cli.num_envs

    # Create environment
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env)

    # Load checkpoint
    if args_cli.resume_path:
        resume_path = args_cli.resume_path
    else:
        log_root_path = os.path.join("logs", "rsl_rl", agent_cfg.experiment_name)
        resume_path = get_checkpoint_path(log_root_path, agent_cfg.load_run, agent_cfg.load_checkpoint)
    if not resume_path:
        raise FileNotFoundError("No checkpoint found. Use --checkpoint <path> to specify directly.")
    print(f"Loading checkpoint: {resume_path}")

    # Build runner to load policy
    runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=agent_cfg.device)
    runner.load(resume_path)
    policy_nn = runner.get_inference_policy(device=agent_cfg.device)

    # Get the actual policy module for evaluate() access
    policy_module = runner.alg.policy
    policy_module.eval()

    # Reset env
    obs = env.get_observations()

    # Collect data
    data = collect_rollouts(env, policy_module, args_cli.num_episodes, agent_cfg.device)

    # Save
    output_dir = os.path.dirname(args_cli.output)
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    save_dict = {
        **data,
        "metadata": {
            "checkpoint": resume_path,
            "task": args_cli.task,
            "num_envs": args_cli.num_envs,
            "num_episodes": args_cli.num_episodes,
            "total_steps": data["policy_obs"].shape[0],
            "policy_obs_dim": data["policy_obs"].shape[1],
            "privileged_dim": data["privileged"].shape[1],
        },
    }
    torch.save(save_dict, args_cli.output)
    print(f"Saved {data['policy_obs'].shape[0]} transitions to {args_cli.output}")
    print(f"  policy_obs: {data['policy_obs'].shape}")
    print(f"  privileged: {data['privileged'].shape}")
    print(f"  V_critic:   {data['V_critic'].shape}")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
