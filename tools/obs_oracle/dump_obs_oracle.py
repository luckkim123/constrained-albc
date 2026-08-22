"""Dump the sim's own 72D policy observations as the oracle for board obs assembly.

Runs INSIDE the marinelab-isaaclab container under Isaac Sim's python:

    cd /workspace/isaaclab && ./isaaclab.sh -p /workspace/dump_obs_oracle.py \
        --task Isaac-ConstrainedALBC-TRPO-v0 --num_envs 1 --headless \
        --steps 40 --out /workspace/obs_oracle_72d.npz

WHY THIS EXISTS
---------------
A deploy pack's goldens start from an already-assembled obs, and golden_e2e_*.npz
is numpy-self-referential, so neither can tell whether the board's `_assemble_obs`
actually reproduces `albc_env._get_observations`. A wrong assembler reproduces its
own error perfectly. Only the sim can arbitrate, which is what this dumps.

NO POLICY IS LOADED. The board replay injects whatever action the sim applied, so
the actions only need to be identical on both sides -- a seeded pseudo-random
sequence exercises act_hist ordering and the joint-target accumulator better than
a checkpoint would, and removes the checkpoint/runner machinery entirely.

Observation noise is nulled: the sim builds its history and integral from clean
internal state while the board can only rebuild them from the (noised) proprio it
receives, so leaving noise on would compare two things that cannot agree by
construction and say nothing about assembly logic.
"""
import argparse
import os
import sys

# This file lives in /workspace (operational scripts), not in the repo, so the SSOT
# tree stays clean; _common is a repo module and has to be put on the path by hand.
sys.path.insert(0, "/workspace/constrained-albc/scripts")

from _common import install_overlay_import_hook, launch_app  # isort: skip

cli_args = install_overlay_import_hook()

parser = argparse.ArgumentParser(description="Dump sim 72D obs as the board-assembly oracle.")
# _common.launch_app reads --video/--video_length off the namespace unconditionally,
# so they have to exist even though this probe never records.
parser.add_argument("--video", action="store_true", default=False)
parser.add_argument("--video_length", type=int, default=0)
parser.add_argument("--num_envs", type=int, default=1)
parser.add_argument("--task", type=str, default="Isaac-ConstrainedALBC-TRPO-v0")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--seed", type=int, default=30, help="env seed AND action-stream seed")
parser.add_argument("--steps", type=int, default=40)
parser.add_argument("--out", type=str, required=True)
cli_args.add_rsl_rl_args(parser)
# Progress markers go to stderr on purpose: stdout is block-buffered once the launcher
# output is piped, so a stdout print tells you nothing about where a silent exit happened.
print("[oracle] pre-launch_app", file=sys.stderr, flush=True)
args_cli, hydra_args, app_launcher, simulation_app = launch_app(parser)
print("[oracle] post-launch_app (sim app booted)", file=sys.stderr, flush=True)

"""Rest everything follows."""

import gymnasium as gym
import numpy as np
import torch

from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils.hydra import hydra_task_config


def policy_obs(out):
    """Pull the 72D policy tensor out of whatever the wrapper hands back.

    RslRlVecEnvWrapper.get_observations returns a TensorDict keyed by observation
    group (vecenv_wrapper.py:143-149), so indexing the numpy conversion positionally
    raises KeyError: 0 rather than anything that reads like a type error.
    """
    if isinstance(out, tuple):
        out = out[0]
    if hasattr(out, "keys"):
        out = out["policy"]
    return out


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg, agent_cfg):
    print("[oracle] main() entered (hydra resolved cfgs)", file=sys.stderr, flush=True)
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.seed = args_cli.seed
    if args_cli.device is not None:
        env_cfg.sim.device = args_cli.device

    # Null the sensor-noise model (see module docstring). DirectRLEnvCfg field; the
    # DR per-env obs_noise_scale multiplies this, so nulling it removes both layers.
    if getattr(env_cfg, "observation_noise_model", None) is not None:
        print("[oracle] nulling observation_noise_model for a deterministic obs stream")
        env_cfg.observation_noise_model = None

    env = gym.make(args_cli.task, cfg=env_cfg, render_mode=None)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)

    cfg_action = getattr(env.unwrapped.cfg, "action_space", None)
    action_dim = cfg_action if isinstance(cfg_action, int) else env.unwrapped.action_space.shape[-1]
    rng = np.random.RandomState(args_cli.seed)
    device = env.unwrapped.device

    # The env's own buffers, dumped verbatim. Comparing only obs forces a guess about
    # which action index the sim paired with which state, and that guess is exactly what
    # a phase investigation must not rest on -- so read the buffers instead of inferring.
    INTERNALS = ("_hist_buf", "_prev_actions", "_joint_pos_targets",
                 "_error_integral", "_bias_ema", "_hist_step_counter")

    def snapshot(core):
        out = {}
        for name in INTERNALS:
            buf = getattr(core, name, None)
            if buf is None:
                continue
            arr = buf.detach().cpu().numpy() if hasattr(buf, "detach") else np.asarray(buf)
            out[name] = arr[0].copy() if arr.ndim else arr.copy()
        return out

    core = env.unwrapped
    internal_log = []
    obs_log, act_log = [], []
    obs = policy_obs(env.get_observations())
    print("[oracle] policy obs tensor %s action_dim=%d" % (tuple(obs.shape), action_dim),
          file=sys.stderr, flush=True)

    for step in range(args_cli.steps):
        if not simulation_app.is_running():
            break
        obs_log.append(obs.detach().cpu().numpy()[0].copy())
        internal_log.append(snapshot(core))   # buffers as they stand when obs[t] is read
        # smooth-ish action stream: a random walk stays inside [-1, 1] and keeps the
        # joint-target accumulator in a plausible range instead of slamming the clamp
        a = np.clip(0.3 * rng.randn(args_cli.num_envs, action_dim), -1.0, 1.0)
        act_log.append(a[0].astype(np.float32).copy())
        with torch.inference_mode():
            stepped = env.step(torch.as_tensor(a, dtype=torch.float32, device=device))
        obs = policy_obs(stepped[0])

    out = {
        "obs": np.stack(obs_log).astype(np.float32),
        "actions": np.stack(act_log).astype(np.float32),
        "seed": np.array(args_cli.seed),
        "steps": np.array(len(obs_log)),
    }
    for name in INTERNALS:
        frames = [snap[name] for snap in internal_log if name in snap]
        if len(frames) == len(internal_log) and frames:
            out["sim" + name] = np.stack(frames).astype(np.float32)
    os.makedirs(os.path.dirname(os.path.abspath(args_cli.out)) or ".", exist_ok=True)
    np.savez(args_cli.out, **out)
    print("[oracle] wrote %s  obs=%s actions=%s" % (args_cli.out, out["obs"].shape,
                                                    out["actions"].shape))
    print("[oracle] obs tail step0 integral=%s bias_ema=%s"
          % (out["obs"][0, 66:69], out["obs"][0, 69:72]))
    print("[oracle] obs tail last integral=%s bias_ema=%s"
          % (out["obs"][-1, 66:69], out["obs"][-1, 69:72]))
    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
