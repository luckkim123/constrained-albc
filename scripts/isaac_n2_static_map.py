#!/usr/bin/env python3
"""N2 -- sim static attitude map, the counterpart of the 2026-09-02 tank T1 sweep.

Runs INSIDE the marinelab-isaaclab container under Isaac Sim's own python:

    cd /workspace/constrained-albc/scripts
    /workspace/isaaclab/isaaclab.sh -p isaac_n2_static_map.py --headless

Structure is lifted from isaac_p1_replay.py and the reasons there all still hold:
hydro is applied in ALBCEnv._apply_action, so a bare Articulation would measure the
arm in air; a zero action plus direct writes to _joint_pos_targets drives the joints
while the full underwater plant stays live; DR and faults are off so this is the
nominal plant; episode_length_buf is zeroed so the decorrelation jitter cannot
auto-reset mid-sweep.

What is different from P1: P1 swung joint1 with joint2 pinned at 0 (fully extended,
r = 0.466 m) and asked about the yaw reaction. T1 held joint2 at 149.85 deg
(r = 0.121 m) and stepped joint1 through 8 azimuths, asking what STATIC roll/pitch
each buoy azimuth produces. The measured answer was

    body_roll  = +120 * t_y - 1.5      (deg, t in m)
    body_pitch = -120 * t_x - 0.9

with residual RMS 0.43 / 0.20 deg over the 8 points, and an effective gain that
RISES about 15% from 9 deg to 29 deg of tilt. finding/134 sec 1, finding/135 sec 9-10.

Self-check built in: at theta2 = 0 the buoy body-frame radius must come out near
0.466 m and at theta2 = 2.6153 rad near 0.121 m. If it does not, the sim's joint2
zero convention differs from the robot's and the whole comparison is void -- the
script prints CONVENTION_OK / CONVENTION_MISMATCH before the sweep and does not
suppress the mismatch.
"""

import argparse
import csv
import math
import os
import sys

AZIMUTHS = [0.0, 45.0, 90.0, 135.0, 180.0, 225.0, 270.0, 315.0]
THETA2_T1 = 2.615395  # rad = 149.85 deg, the T1 hold


def s5(u):
    """5th-order min-jerk smoothstep, clamped. Same stencil as isaac_p1_replay.py."""
    u = min(1.0, max(0.0, u))
    return u * u * u * (10.0 + u * (-15.0 + 6.0 * u))


def selftest():
    assert s5(0.0) == 0.0 and s5(1.0) == 1.0
    assert abs(s5(0.5) - 0.5) < 1e-12
    # the T1 hold must map to the radius T1 actually ran at (L1 = L2 = 0.233)
    r = 0.233 * abs(complex(1.0, 0.0) + complex(math.cos(THETA2_T1), math.sin(THETA2_T1)))
    assert abs(r - 0.1212) < 5e-4, r
    print("selftest OK  (theta2=%.4f rad -> r=%.4f m)" % (THETA2_T1, r))


if "--selftest" in sys.argv:
    selftest()
    raise SystemExit(0)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import install_overlay_import_hook, launch_app  # noqa: E402

install_overlay_import_hook()

parser = argparse.ArgumentParser(description="N2 sim static attitude map (T1 counterpart).")
parser.add_argument("--task", default="Isaac-ConstrainedALBC-TRPO-v0")
parser.add_argument("--theta2", type=float, default=THETA2_T1, help="rad, held for the whole sweep")
parser.add_argument("--ramp", type=float, default=4.0, help="s, min-jerk move between azimuths")
parser.add_argument("--hold", type=float, default=26.0, help="s, hold at each azimuth (T1 held 35 s)")
parser.add_argument("--settle", type=float, default=25.0, help="s, unlogged settle at the first azimuth")
parser.add_argument("--az-list", default="", help="comma-separated azimuth degrees; default is the 8-point T1 set")
parser.add_argument("--tag", default="", help="suffix for the output csv name")
parser.add_argument("--outdir", default="/tmp/n2_static_map")
parser.add_argument("--video", action="store_true", help="unused; _common expects the flag")
args_cli, _, _, simulation_app = launch_app(parser)

import gymnasium as gym  # noqa: E402
import torch  # noqa: E402

import isaaclab_tasks  # noqa: F401,E402  -- bare, see isaac_p1_replay.py
from isaaclab_tasks.utils import parse_env_cfg  # noqa: E402

env_cfg = parse_env_cfg(args_cli.task, device=args_cli.device, num_envs=1)
env_cfg.randomization.enable = False   # nominal plant: this IS the quantity under test
env_cfg.fault.enable = False
n_az = len(AZIMUTHS)
need = args_cli.settle + n_az * (args_cli.ramp + args_cli.hold) + 40.0
env_cfg.episode_length_s = max(env_cfg.episode_length_s, need)

env = gym.make(args_cli.task, cfg=env_cfg)
u = env.unwrapped
dt = env_cfg.sim.dt * env_cfg.decimation
jnames = [u._robot.joint_names[i] for i in u._albc_joint_ids]
i1, i2 = jnames.index("joint1"), jnames.index("joint2")
action = torch.zeros((u.num_envs, env_cfg.action_space), device=u.device)
buoy_idx = u._buoy_body_id[0]
os.makedirs(args_cli.outdir, exist_ok=True)


def quat_inv_apply(q, v):
    """Rotate world vector v into the body frame. q = (w, x, y, z)."""
    w, x, y, z = float(q[0]), float(q[1]), float(q[2]), float(q[3])
    r00 = 1 - 2 * (y * y + z * z); r01 = 2 * (x * y - z * w); r02 = 2 * (x * z + y * w)
    r10 = 2 * (x * y + z * w); r11 = 1 - 2 * (x * x + z * z); r12 = 2 * (y * z - x * w)
    r20 = 2 * (x * z - y * w); r21 = 2 * (y * z + x * w); r22 = 1 - 2 * (x * x + y * y)
    return (r00 * v[0] + r10 * v[1] + r20 * v[2],
            r01 * v[0] + r11 * v[1] + r21 * v[2],
            r02 * v[0] + r12 * v[1] + r22 * v[2])


def buoy_body_offset():
    d = u._robot.data
    q = d.root_quat_w[0]
    dv = (float(d.body_pos_w[0, buoy_idx, 0]) - float(d.root_pos_w[0, 0]),
          float(d.body_pos_w[0, buoy_idx, 1]) - float(d.root_pos_w[0, 1]),
          float(d.body_pos_w[0, buoy_idx, 2]) - float(d.root_pos_w[0, 2]))
    return quat_inv_apply(q, dv)


def hold(theta1, theta2, nsteps, writer, phase, az):
    for k in range(nsteps):
        u._joint_pos_targets[:, i1] = theta1
        u._joint_pos_targets[:, i2] = theta2
        _, _, term, tmo, _ = env.step(action)
        if bool(term[0]) or bool(tmo[0]):
            return False
        if writer is not None:
            d = u._robot.data
            q = d.root_quat_w[0]
            jp = d.joint_pos[0, u._albc_joint_ids]
            bx, by, bz = buoy_body_offset()
            writer.writerow([
                "%.4f" % (k * dt), phase, "%.1f" % az, "%.6f" % theta1,
                "%.6f" % float(jp[i1]), "%.6f" % float(jp[i2]),
                "%.6f" % float(q[0]), "%.6f" % float(q[1]),
                "%.6f" % float(q[2]), "%.6f" % float(q[3]),
                "%.6f" % bx, "%.6f" % by, "%.6f" % bz,
            ])
    return True


env.reset()
u.episode_length_buf[:] = 0

# --- convention self-check: does the sim's joint2 zero match the robot's? ------------
if not hold(0.0, args_cli.theta2, int(round(12.0 / dt)), None, "conv", 0.0):
    print("CONVENTION_CHECK_TERMINATED")
bx, by, bz = buoy_body_offset()
r_at_theta2 = math.hypot(bx, by)
if not hold(0.0, 0.0, int(round(12.0 / dt)), None, "conv0", 0.0):
    print("CONVENTION_CHECK_TERMINATED")
ex, ey, ez = buoy_body_offset()
r_extended = math.hypot(ex, ey)
print("CONVENTION r(theta2=%.4f)=%.4f m  r(theta2=0)=%.4f m  "
      "(robot: 0.121 and 0.466)" % (args_cli.theta2, r_at_theta2, r_extended))
ok = abs(r_at_theta2 - 0.121) < 0.030 and abs(r_extended - 0.466) < 0.060
print("CONVENTION_OK" if ok else "CONVENTION_MISMATCH -- comparison is void, do not fit")

# --- sweep ---------------------------------------------------------------------------
AZ_USE = [float(x) for x in args_cli.az_list.split(",")] if args_cli.az_list else AZIMUTHS
path = os.path.join(args_cli.outdir, "n2_static_map%s.csv" % args_cli.tag)
with open(path, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["t", "phase", "az_deg", "q1_cmd", "q1", "q2", "qw", "qx", "qy", "qz", "bx", "by", "bz"])
    prev = 0.0
    first = True
    for az in AZ_USE:
        target = math.radians(az)
        nramp = int(round(args_cli.ramp / dt))
        for k in range(nramp):
            th = prev + (target - prev) * s5(k * dt / args_cli.ramp)
            u._joint_pos_targets[:, i1] = th
            u._joint_pos_targets[:, i2] = args_cli.theta2
            _, _, term, tmo, _ = env.step(action)
            if bool(term[0]) or bool(tmo[0]):
                print("TRUNCATED during ramp to az=%.0f" % az)
                break
        prev = target
        if first:
            if not hold(target, args_cli.theta2, int(round(args_cli.settle / dt)), None, "settle", az):
                print("TRUNCATED during settle")
            first = False
        if not hold(target, args_cli.theta2, int(round(args_cli.hold / dt)), w, "hold", az):
            print("TRUNCATED during hold az=%.0f" % az)
            break
        print("AZ_DONE %.0f" % az)

print("OUT=%s DT=%.4f" % (path, dt))
env.close()
simulation_app.close()
print("RUN_COMPLETE")
