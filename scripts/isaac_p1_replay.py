#!/usr/bin/env python3
"""P1 Isaac-side replay -- joint1 swing, base yaw reaction. Counterpart to p1_runner.py.

Runs INSIDE the marinelab-isaaclab container under Isaac Sim's own python:

    cd /workspace/constrained-albc/scripts
    /workspace/isaaclab/isaaclab.sh -p isaac_p1_replay.py --headless --case S4 --reps 3

Why it goes through ALBCEnv.step() instead of a bare Articulation: hydro (buoyancy,
added mass, drag) is applied in ALBCEnv._apply_action (albc_env.py:925-978) through
HydrodynamicsModel, not by the articulation itself. A bare-articulation scene would
measure the arm swinging in air, which is not the plant P1 is about. _apply_action
runs every physics substep regardless of what the action contains, so a zero action
plus direct writes to _joint_pos_targets drives joint1 while the full underwater
plant stays live. action_space is 8 = 2D arm delta + 6D thruster (config.py:436), so
a zero action means no thrust and no arm delta -- _pre_physics_step's
`_joint_pos_targets += delta` (albc_env.py:724) becomes a no-op.

CSV columns are byte-identical to the Stonefish runner's 24, so p1_summary.py
aggregates both sides with no changes.

NOTE ON DERIVATIVE STENCIL: Isaac logs at the 50 Hz control rate, Stonefish logged
at 100 Hz. p1_summary.py's default 5-sample stencil spans 40 ms at 100 Hz but 80 ms
at 50 Hz, which would smooth Isaac's peaks harder than Stonefish's. Aggregate the
Isaac CSVs with P1_STENCIL=3 to get the matching 40 ms span.
"""

import argparse
import csv
import math
import os
import sys

# --- profiles (shared contract with the Stonefish side, report section 4) -----------

AMP_SMALL = 0.5236  # rad, 30 deg
AMP_LARGE = 1.5708  # rad, 90 deg


def s5(u):
    """5th-order min-jerk smoothstep, clamped. Guarantees v(0)=0."""
    u = min(1.0, max(0.0, u))
    return u * u * u * (10.0 + u * (-15.0 + 6.0 * u))


def minjerk(amp, T, t):
    return amp * s5(t / T)


def sine(amp, f, t):
    """First-cycle min-jerk envelope. Without it, v(0)!=0 reproduces the step's
    servo bang-bang artifact -- the exact failure the Stonefish side hit."""
    return amp * s5(t * f) * math.sin(2.0 * math.pi * f * t)


CASES = {
    "S5": (lambda t: 0.0, "null"),
    "S1ff": (lambda t: minjerk(AMP_LARGE, 1.0, t), "step"),
    "S2": (lambda t: minjerk(AMP_SMALL, 1.0, t), "step"),
    "S3": (lambda t: sine(AMP_SMALL, 0.25, t), "sine"),
    "S4": (lambda t: sine(AMP_SMALL, 0.75, t), "sine"),
}

COLS = [
    "t_wall", "t_rel", "label", "q1_cmd", "q2_cmd", "q1", "q2", "dq1", "dq2",
    "tau1", "tau2", "px", "py", "pz", "qx", "qy", "qz", "qw", "vx", "vy", "vz",
    "wx", "wy", "wz",
]


def selftest():
    """Runnable without Isaac: the profile contract the two sims must share."""
    assert s5(0.0) == 0.0 and s5(1.0) == 1.0
    assert abs(s5(0.5) - 0.5) < 1e-12
    # v(0)=0 for every profile -- the whole point of the envelope
    for fn, _ in CASES.values():
        assert abs(fn(1e-6) - fn(0.0)) / 1e-6 < 1e-3, "profile leaves t=0 with nonzero velocity"
    assert abs(minjerk(AMP_LARGE, 1.0, 1.0) - AMP_LARGE) < 1e-12
    assert abs(minjerk(AMP_SMALL, 1.0, 1.0) - AMP_SMALL) < 1e-12
    # sine reaches its envelope-limited peak near the first quarter period
    assert sine(AMP_SMALL, 0.75, 1.0 / 3.0) > 0.0
    assert abs(sine(AMP_SMALL, 0.25, 0.0)) < 1e-12
    print("selftest OK")


if "--selftest" in sys.argv:
    selftest()
    raise SystemExit(0)

# --- Isaac boot (must precede any isaaclab/gym import) -------------------------------

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import install_overlay_import_hook, launch_app  # noqa: E402

install_overlay_import_hook()

parser = argparse.ArgumentParser(description="P1 Isaac-side joint1 swing replay.")
parser.add_argument("--task", default="Isaac-ConstrainedALBC-TRPO-v0")
parser.add_argument("--case", required=True, choices=sorted(CASES))
parser.add_argument("--reps", type=int, default=3)
parser.add_argument("--dur", type=float, default=20.0, help="logged seconds per rep")
parser.add_argument("--settle", type=float, default=20.0,
                    help="unlogged seconds at q1=q2=0 before the window, matching the "
                         "Stonefish schedules' 20 s settle + 1 s pre segments")
parser.add_argument("--outdir", default="/tmp/p1_isaac")
parser.add_argument("--video", action="store_true", help="unused; _common expects the flag")
args_cli, _, _, simulation_app = launch_app(parser)

import gymnasium as gym  # noqa: E402
import torch  # noqa: E402

# Bare import, and it must stay bare: _common's overlay hook fires only on an exact
# name match of "isaaclab_tasks" (_common.py:37), and that is what imports
# constrained_albc and runs its gym.register(). A `from isaaclab_tasks.utils import ...`
# passes the hook the name "isaaclab_tasks.utils", misses the match, and the task never
# registers -- gymnasium then reports the env as nonexistent. train.py:137 and play.py:88
# carry the same bare import for the same reason.
import isaaclab_tasks  # noqa: F401,E402
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402

# --- env: nominal plant, no DR, no faults, episode long enough for a 20 s window -----

env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
# DomainRandomizationCfg.enable defaults True (config.py:175). Left on, joint1 would
# start at a random angle in (-pi, pi) (config.py:503) and hydro/mass/current DR would
# perturb the very plant we are measuring (albc_env.py:1522-1524).
env_cfg.randomization.enable = False
env_cfg.fault.enable = False
# episode_length_s defaults to 30 s (config.py:434); the settle segment plus the 20 s
# window plus the reset-time decorrelation jitter would truncate mid-run. Raised to cover
# settle + window, and the jitter is zeroed below. These two must move together: adding
# settle without raising this silently auto-resets the base partway through the window.
env_cfg.episode_length_s = max(env_cfg.episode_length_s, args_cli.settle + args_cli.dur + 10.0)

env = gym.make(args_cli.task, cfg=env_cfg)
u = env.unwrapped

dt = env_cfg.sim.dt * env_cfg.decimation  # 0.005 * 4 = 0.02 s -> 50 Hz, matches Stonefish cmd rate
jnames = [u._robot.joint_names[i] for i in u._albc_joint_ids]
i1, i2 = jnames.index("joint1"), jnames.index("joint2")  # find_joints does not preserve request order
prof, label = CASES[args_cli.case]
os.makedirs(args_cli.outdir, exist_ok=True)
action = torch.zeros((u.num_envs, env_cfg.action_space), device=u.device)
nsteps = int(round(args_cli.dur / dt))

for rep in range(1, args_cli.reps + 1):
    env.reset()
    # albc_env.py:1461-1464 primes episode_length_buf with up to 750 steps of
    # decorrelation jitter, which would auto-reset this run partway through.
    u.episode_length_buf[:] = 0
    # Settle before logging. The Stonefish schedules all open with a 20 s settle + 1 s pre
    # segment and take the window only after it; logging straight from reset instead puts
    # the spawn transient underneath the excitation. Measured on the first S5 run without
    # this: null-floor peak |r| 0.464 rad/s against Stonefish's 0.0161, and the base
    # rotated 2.31 rad on no command at all -- a floor that large contaminates every case.
    for _ in range(int(round(args_cli.settle / dt))):
        u._joint_pos_targets[:, i1] = 0.0
        u._joint_pos_targets[:, i2] = 0.0
        _, _, term, tmo, _ = env.step(action)
        if bool(term[0]) or bool(tmo[0]):
            print("SETTLE_TERMINATED case=%s rep=%d -- window not started" % (args_cli.case, rep))
            break
    path = os.path.join(args_cli.outdir, "p1i_%s_r%d.csv" % (args_cli.case, rep))
    truncated_at = None
    with open(path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(COLS)
        for k in range(nsteps):
            t = k * dt
            q1c = prof(t)
            u._joint_pos_targets[:, i1] = q1c
            u._joint_pos_targets[:, i2] = 0.0
            _, _, terminated, timeout, _ = env.step(action)
            if bool(terminated[0]) or bool(timeout[0]):
                truncated_at = t
                break
            d = u._robot.data
            q = d.joint_pos[0, u._albc_joint_ids]
            dq = d.joint_vel[0, u._albc_joint_ids]
            tau = d.applied_torque[0, u._albc_joint_ids]
            quat = d.root_quat_w[0]      # (w, x, y, z)
            pos = d.root_pos_w[0]
            lin = d.root_lin_vel_b[0]    # body frame, matching Stonefish odom twist
            ang = d.root_ang_vel_b[0]
            w.writerow([
                "%.6f" % t, "%.6f" % t, label, "%.6f" % q1c, "0.000000",
                "%.6f" % q[i1], "%.6f" % q[i2], "%.6f" % dq[i1], "%.6f" % dq[i2],
                "%.6f" % tau[i1], "%.6f" % tau[i2],
                "%.6f" % pos[0], "%.6f" % pos[1], "%.6f" % pos[2],
                "%.6f" % quat[1], "%.6f" % quat[2], "%.6f" % quat[3], "%.6f" % quat[0],
                "%.6f" % lin[0], "%.6f" % lin[1], "%.6f" % lin[2],
                "%.6f" % ang[0], "%.6f" % ang[1], "%.6f" % ang[2],
            ])
    if truncated_at is None:
        print("ROWS=%d DT=%.4f OUT=%s" % (nsteps, dt, path))
    else:
        # Loud, not silent: a truncated rep is not a shorter rep, it is a different
        # experiment (the env reset the base pose mid-window).
        print("TRUNCATED case=%s rep=%d at t=%.3f OUT=%s" % (args_cli.case, rep, truncated_at, path))

env.close()
simulation_app.close()
print("RUN_COMPLETE case=%s reps=%d" % (args_cli.case, args_cli.reps))
