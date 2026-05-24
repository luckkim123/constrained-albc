"""Single-switch OOD eval: nominal -> extreme OOD physics at one step.

1 env, zero command (hover). Start with nominal physics so policy stabilizes;
at t=switch_time suddenly switch to extreme OOD physics. Records trajectory to
measure transient recovery + post-switch steady state.

Usage:
  ./isaaclab.sh -p scripts/analysis/eval_single_switch.py \\
    --task Isaac-FullDOF-TRPO-v0 \\
    --checkpoint <path>/model_4999.pt \\
    --switch_time 10.0 --total_time 30.0 \\
    --headless
"""

from __future__ import annotations

import argparse
import os
import sys

# cli_args lives in scripts/reinforcement_learning/rsl_rl/
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "reinforcement_learning", "rsl_rl"))

from isaaclab.app import AppLauncher

import cli_args  # isort: skip

parser = argparse.ArgumentParser(description="Single-switch OOD eval.")
parser.add_argument("--task", type=str, default="Isaac-FullDOF-TRPO-v0")
# Note: --checkpoint, --resume, --load_run, --run_name, --logger are added by cli_args.add_rsl_rl_args below.
parser.add_argument("--output_dir", type=str, default=None)
parser.add_argument("--switch_time", type=float, default=10.0, help="Time to switch physics (s).")
parser.add_argument("--total_time", type=float, default=30.0, help="Total rollout duration (s).")
parser.add_argument("--seed", type=int, default=42, help="Random seed.")
parser.add_argument("--agent", type=str, default="rsl_rl_cfg_entry_point")
parser.add_argument("--num_envs", type=int, default=1)
cli_args.add_rsl_rl_args(parser)
AppLauncher.add_app_launcher_args(parser)
args_cli, hydra_args = parser.parse_known_args()

sys.argv = [sys.argv[0]] + hydra_args
app_launcher = AppLauncher(args_cli)
simulation_app = app_launcher.app

# --- Rest of imports ---
import numpy as np
import torch
import gymnasium as gym
import rsl_rl.runners.on_policy_runner as _runner_module
from rsl_rl.runners import OnPolicyRunner

from isaaclab.utils.math import euler_xyz_from_quat
from isaaclab_rl.rsl_rl import RslRlVecEnvWrapper

import isaaclab_tasks  # noqa: F401
from isaaclab_tasks.utils import get_checkpoint_path
from isaaclab_tasks.utils.hydra import hydra_task_config
from isaaclab_tasks.direct.constrained_full_albc.encoder import ActorCriticEncoder
from isaaclab_tasks.direct.constrained_full_albc.algorithms import ConstraintTRPO
from isaaclab_tasks.direct.constrained_full_albc.runners import ConstraintEncoderRunner

_runner_module.FullDOFActorCriticEncoder = ActorCriticEncoder
_runner_module.FullDOFConstraintEncoderRunner = ConstraintEncoderRunner
_runner_module.FullDOFConstraintTRPO = ConstraintTRPO

# Extreme OOD physics preset — HARDER version (2026-04-22, v2).
# All values pushed to ~2x training bounds. Compared to training maxima:
#   payload:      6.0 kg    (training max 2.86,  +110%)
#   inertia:      4.0x      (training max 1.93,  +107%)
#   body_mass:    2.5x      (training max 1.23,  +103%)
#   linear_damp:  3.5x      (training max 1.64,  +114%)
#   quad_damp:    3.5x      (training max 1.64,  +114%)
#   volume:       2.0x      (training max 1.23,  +63%)
#   added_mass:   2.5x      (training max 1.45,  +72%)
#   water_density:1060      (training max 1024,  +3.5%; physics-capped)
#   cog/cob xy:   0.050     (training max 0.018, +178%)
#   cog/cob z:    0.080     (training max 0.036, +122%)
#   payload_cog_z:-0.120    (training min -0.048, +150%)
_EXTREME_OOD: dict[str, float] = {
    "payload_mass_range":       3.50,
    "added_mass_scale":         1.80,
    "linear_damping_scale":     2.05,
    "quadratic_damping_scale":  2.05,
    "water_density_range":      1045.0,
    "volume_scale":             1.45,
    "inertia_scale":            2.50,
    "body_mass_scale":          1.50,
    "cog_offset_x": 0.028, "cog_offset_y": 0.028, "cog_offset_z": 0.055,
    "cob_offset_x": 0.028, "cob_offset_y": 0.028, "cob_offset_z": 0.055,
    "payload_cog_offset_z": -0.075,
}
_EXTREME_OOD_FLOATS: dict[str, float] = {
    "payload_cog_offset_xy_radius": 0.10,  # user directive; 0.08 training -> 0.10
}

# Nominal physics (pre-switch): training midpoints that are easy.
_NOMINAL_PHYSICS: dict[str, float] = {
    "payload_mass_range":       0.5,
    "added_mass_scale":         1.0,
    "linear_damping_scale":     1.0,
    "quadratic_damping_scale":  1.0,
    "water_density_range":      1000.0,
    "volume_scale":             1.0,
    "inertia_scale":            1.0,
    "body_mass_scale":          1.0,
    "cog_offset_x": 0.0, "cog_offset_y": 0.0, "cog_offset_z": 0.0,
    "cob_offset_x": 0.0, "cob_offset_y": 0.0, "cob_offset_z": 0.0,
    "payload_cog_offset_z": -0.015,
}


def _apply_physics(env_cfg, physics_dict: dict[str, float], float_dict: dict[str, float] | None = None) -> None:
    """Overwrite env_cfg.randomization fields: tuples -> (v,v), floats -> v."""
    dr = env_cfg.randomization
    for field_name, value in physics_dict.items():
        if hasattr(dr, field_name):
            setattr(dr, field_name, (value, value))
    if float_dict:
        for field_name, value in float_dict.items():
            if hasattr(dr, field_name):
                setattr(dr, field_name, value)


@hydra_task_config(args_cli.task, args_cli.agent)
def main(env_cfg, agent_cfg):
    # --- Disable DORAEMON ---
    if hasattr(env_cfg, "doraemon"):
        env_cfg.doraemon.enable = False
    env_cfg.scene.num_envs = args_cli.num_envs
    env_cfg.seed = args_cli.seed

    # --- Start with nominal physics ---
    _apply_physics(env_cfg, _NOMINAL_PHYSICS, {"payload_cog_offset_xy_radius": 0.0})
    print(f"[INFO] Initial physics: NOMINAL (payload={_NOMINAL_PHYSICS['payload_mass_range']}kg, inertia={_NOMINAL_PHYSICS['inertia_scale']}x, xy_radius=0.0)")
    xy_r = _EXTREME_OOD_FLOATS.get("payload_cog_offset_xy_radius", "unchanged")
    print(f"[INFO] Will switch at t={args_cli.switch_time}s to EXTREME OOD "
          f"(payload={_EXTREME_OOD['payload_mass_range']}kg, inertia={_EXTREME_OOD['inertia_scale']}x, "
          f"payload_xy_radius={xy_r})")

    # --- Create env ---
    env = gym.make(args_cli.task, cfg=env_cfg)
    env = RslRlVecEnvWrapper(env, clip_actions=agent_cfg.clip_actions)
    raw_env = env.unwrapped
    step_dt = raw_env.step_dt
    num_envs = raw_env.num_envs
    device = raw_env.device

    total_steps = int(args_cli.total_time / step_dt)
    switch_step = int(args_cli.switch_time / step_dt)

    print(f"[INFO] step_dt={step_dt:.4f}s, total_steps={total_steps}, switch_step={switch_step}")

    # --- Load policy ---
    runner_cls_name = getattr(agent_cfg, "class_name", "OnPolicyRunner")
    runner_device = agent_cfg.device

    if runner_cls_name == "FullDOFConstraintEncoderRunner":
        from isaaclab_tasks.direct.constrained_full_albc.runners import ConstraintEncoderRunner as _Runner
        runner = _Runner(env, agent_cfg.to_dict(), log_dir=None, device=runner_device)
    elif runner_cls_name == "OnPolicyDoraemonRunner":
        from isaaclab_tasks.direct.constrained_full_albc.runners import OnPolicyDoraemonRunner as _Runner
        runner = _Runner(env, agent_cfg.to_dict(), log_dir=None, device=runner_device)
    else:
        runner = OnPolicyRunner(env, agent_cfg.to_dict(), log_dir=None, device=runner_device)

    checkpoint = get_checkpoint_path(
        os.path.dirname(os.path.dirname(args_cli.checkpoint)), None, os.path.basename(args_cli.checkpoint)
    ) if not os.path.isfile(args_cli.checkpoint) else args_cli.checkpoint
    runner.load(checkpoint)
    policy = runner.get_inference_policy(device=runner_device)
    policy_nn = runner.alg.policy

    # --- Buffers ---
    t_arr = np.arange(total_steps) * step_dt
    actual_roll = np.zeros((total_steps, num_envs))
    actual_pitch = np.zeros((total_steps, num_envs))
    lin_vel_x = np.zeros((total_steps, num_envs))
    lin_vel_y = np.zeros((total_steps, num_envs))
    lin_vel_z = np.zeros((total_steps, num_envs))
    yaw_rate_arr = np.zeros((total_steps, num_envs))
    pos_x = np.zeros((total_steps, num_envs))
    pos_y = np.zeros((total_steps, num_envs))
    pos_z = np.zeros((total_steps, num_envs))
    action_magnitude = np.zeros((total_steps, num_envs))
    physics_switch_step = -1

    # --- Force reset ---
    torch.manual_seed(args_cli.seed)
    raw_env.episode_length_buf[:] = raw_env.max_episode_length
    obs = env.get_observations()
    with torch.inference_mode():
        obs, _, _, _ = env.step(policy(obs))
        if hasattr(policy_nn, "reset"):
            policy_nn.reset(torch.ones(num_envs, 1, dtype=torch.bool, device=device))
    raw_env.episode_length_buf[:] = 0

    all_env_ids = torch.arange(num_envs, device=device)
    env_origins = raw_env.scene.env_origins  # (N, 3)

    # --- Rollout ---
    for step in range(total_steps):
        # Zero command (hover)
        raw_env._ang_cmd[:, 0] = 0.0
        raw_env._ang_cmd[:, 1] = 0.0
        raw_env._ang_cmd[:, 2] = 0.0
        raw_env._vel_cmd_lin[:, :] = 0.0

        # --- Single physics switch ---
        if step == switch_step:
            _apply_physics(raw_env.cfg, _EXTREME_OOD, _EXTREME_OOD_FLOATS)
            raw_env.randomize_physics_mid_episode(env_ids=all_env_ids)
            physics_switch_step = step
            print(f"[INFO] *** PHYSICS SWITCHED at step {step} (t={step*step_dt:.1f}s): NOMINAL -> EXTREME OOD ***")

        with torch.inference_mode():
            actions = policy(obs)
            obs, _, _, _ = env.step(actions)

        roll, pitch, _ = euler_xyz_from_quat(raw_env._robot.data.root_quat_w)
        actual_roll[step] = torch.rad2deg(((roll + np.pi) % (2 * np.pi) - np.pi)).cpu().numpy()
        actual_pitch[step] = torch.rad2deg(((pitch + np.pi) % (2 * np.pi) - np.pi)).cpu().numpy()
        lin_vel_x[step] = raw_env._robot.data.root_lin_vel_b[:, 0].cpu().numpy()
        lin_vel_y[step] = raw_env._robot.data.root_lin_vel_b[:, 1].cpu().numpy()
        lin_vel_z[step] = raw_env._robot.data.root_lin_vel_b[:, 2].cpu().numpy()
        yaw_rate_arr[step] = raw_env._robot.data.root_ang_vel_b[:, 2].cpu().numpy()
        pos_drift = (raw_env._robot.data.root_pos_w - env_origins).cpu().numpy()
        pos_x[step] = pos_drift[:, 0]
        pos_y[step] = pos_drift[:, 1]
        pos_z[step] = pos_drift[:, 2]
        action_magnitude[step] = actions.abs().mean(dim=-1).cpu().numpy()

        if step % 250 == 0:
            print(f"  step {step}/{total_steps} (t={step*step_dt:.1f}s): roll={actual_roll[step, 0]:+.2f}° pitch={actual_pitch[step, 0]:+.2f}° pos=({pos_x[step, 0]:+.2f},{pos_y[step, 0]:+.2f},{pos_z[step, 0]:+.2f})")

    # --- Save ---
    if args_cli.output_dir:
        out_dir = args_cli.output_dir
    else:
        out_dir = os.path.join(os.path.dirname(args_cli.checkpoint), "eval_single_switch")
    os.makedirs(out_dir, exist_ok=True)

    np.savez(
        os.path.join(out_dir, "trajectory.npz"),
        time=t_arr, switch_step=physics_switch_step,
        actual_roll_deg=actual_roll, actual_pitch_deg=actual_pitch,
        lin_vel_x=lin_vel_x, lin_vel_y=lin_vel_y, lin_vel_z=lin_vel_z,
        yaw_rate=yaw_rate_arr,
        pos_x=pos_x, pos_y=pos_y, pos_z=pos_z,
        action_magnitude=action_magnitude,
    )
    print(f"\n[INFO] Saved trajectory to: {out_dir}/trajectory.npz")

    env.close()


if __name__ == "__main__":
    main()
    simulation_app.close()
