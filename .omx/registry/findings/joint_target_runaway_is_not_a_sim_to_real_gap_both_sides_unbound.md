---
title: "Joint target runaway is NOT a sim-to-real gap (both sides unbounded); the real asymmetry is the accumulator reset"
tags: ["albc", "arm", "joint", "vibration", "sim-to-real", "deployment", "delta-scale", "accumulator", "reset", "retrain-decision", "joint1", "controller-form", "sim2real", "blocked-hardware"]
created: 2026-08-09T08:40:54.319258
updated: 2026-08-14T07:49:38.891620
sources: ["wiki-backlog-20260814"]
links: ["open_on_land_the_policy_winds_j2_to_pi_and_beyond_and_the_board.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "HARDWARE: the remaining gap is arm CONTROLLER FORM (firmware ~1kHz PID with integral + profile-velocity trapezoid vs Isaac ImplicitActuator Kp=100/Kd=3), blocked on the XW540-T260 step-response bench; the arm is also physically broken since 2026-08-13"
---

# Joint target runaway is NOT a sim-to-real gap (both sides unbounded); the real asymmetry is the accumulator reset

The deployed joint-target accumulator is UNBOUNDED on the real robot exactly as it is in sim, so
the target runaway is not a sim-to-real gap and clamping only the sim side would manufacture one.
The one real asymmetry sits somewhere else, in the reset.

WHAT THE CODE SAYS. Sim (`envs/main/albc_env.py:824`) integrates the arm action into a position
target with no bound: `self._joint_pos_targets += delta`, `delta_scale` 0.10 at 50 Hz. Sustained
|a|=1 therefore demands 5.0 rad/s against a 3.1 rad/s cap (`velocity_limit_sim`, lowered from 6.28
on 2026-07-12 to match the measured XW540-T260 plateau), so the target can outrun the joint by up
to 1.9 rad/s and the policy's command stops taking effect until that lead unwinds. The ceiling is
documented at `envs/main/config.py:506-508` and was deliberately left open pending
`arm_delta_sysid.py`, which was never built.

The deployed path does the same thing. `deploy/student_albc_260607/numpy_port/np_policy.py:124`:
`self._joint_target = self._joint_target + DELTA_SCALE * action[:2]`, `DELTA_SCALE` 0.10, no clamp,
and `ros_node/rl_inference_node.py` publishes that absolute angle straight to the Dynamixel driver
(whose contract is an absolute angle it unwrap-follows). Same parameterization, same cap, same
windup. A policy trained under it was trained under the real thing.

CONSEQUENCE FOR THE RETRAIN QUESTION. Adding an accumulator clamp to sim alone changes the training
environment away from deployment and creates a mismatch that does not currently exist. Adding it to
both is a plant change and therefore a retrain, and nothing measured so far justifies one. So the
runaway is not a reason to modify training.

THE REAL ASYMMETRY IS THE RESET. Sim re-seeds the accumulator from the measured joint angle
(`albc_env.py:1668`, `self._joint_pos_targets[env_ids] = self._robot.data.joint_pos[env_ids][...]`),
so training always starts at zero target error. The deployed policy re-seeds from a CONSTANT
(`np_policy.py:75,87`, `NOMINAL_JOINT_POS` = [0, pi/2]). If the arm is not parked at nominal when
the policy starts, step one begins with that offset baked in and the accumulator has no path back.
This is a deployment-side bug, fixable without retraining by initializing `_joint_target` from the
measured joint position. It is also structurally invisible to sim: training never contains a
non-zero startup offset, so no amount of DR or evaluation would surface it.

WHAT REMAINS A GENUINE SIM-TO-REAL GAP ON THE ARM. The controller FORM. The real joint runs a
~1 kHz firmware PID with an integral term (P=800/I=1/D=40) plus a profile-velocity trapezoid; Isaac
runs an ImplicitActuator at Kp=100/Kd=3 with neither. That is plant-change batch v2 item 4 and it
is blocked on the XW540-T260 step response. Small-signal damping is NOT the gap: onboard-measured
overshoot 2-3% gives zeta 0.74-0.78 against Isaac's designed 0.7, and the card that measured it says
explicitly not to retune Kp/Kd.

STILL UNVERIFIED, AND IT IS THE SAME HOLE AS 2026-07-09. Whether any of this explains the vibration
the user reported on the real robot. The reset offset acts only at startup and cannot by itself
produce a sustained oscillation. No real-robot log has ever been analysed for vibration -- the
2026-07-09 differential-diagnosis card closed with "none confirmed against real logs (none
available this session)" and that is still true. The cheapest missing evidence is a deployment run
logging commanded joint target against measured joint angle: it needs no GPU, no retrain, and it
decides whether the lead actually opens in practice.

---

## CORRECTION 2026-08-13 -- the reset fix shipped, and it is what severed the J2 cable.

Three things above are now out of date, and the third one had a physical cost.

**1. "The deployed policy re-seeds from a CONSTANT (`NOMINAL_JOINT_POS` = [0, pi/2])" -- NO LONGER
TRUE.** That deployment-side bug was fixed. `robot/albc_rl/numpy_port/np_policy.py:228-230` now
seeds `_joint_target` from the MEASURED joint angle on reset, exactly as this page recommended.
The path cited above (`deploy/student_albc_260607/numpy_port/np_policy.py:124`) is an old deploy
pack; the live file is `robot/albc_rl/numpy_port/np_policy.py:253`.

**2. THE FIX WAS INCOMPLETE ON THE OTHER SIDE OF THE CONTRACT, and on 2026-08-13 it severed the
J1->J2 daisy-chain cable.** The policy now publishes a CUMULATIVE angle. The driver's startup
baseline was never updated to match: `albc_control/src/joint_angle_command.cpp:291-293` sets
`joint1.absolute_angle = angle1` (cumulative) but `joint1.prev_commanded = fmod(angle1, 2*pi)`
(WRAPPED). `updateJoint` unwraps by removing at most ONE 2*pi, so the remaining `(k-1)*2*pi` of a
k-turn arm enters the driver's UNCLAMPED `absolute_angle` on the FIRST command of every restart.
Below one turn the jump is exactly zero -- which is why it stayed invisible -- and from -11 rad it
doubles per restart (-1, -2, -4 turns). After 11 `launch-rl` runs J1 measured **-35.54 rad
(-5.66 turns)** with `HW Error 0x20 OVERLOAD`, and J2 (ID 12) went to 100 percent COMM_RX_CORRUPT.
The old publisher (`status_publisher.h`, `mapTo2Pi`) sent a wrapped angle, so that baseline was
correct in its day; the RL node changed the contract and the driver did not follow.

Corollary that generalises: **`JOINT_TARGET_CLAMP = [6*pi, inf]` clamps only the POLICY's internal
accumulator.** The driver keeps a second, unbounded accumulator. A rail in the policy layer was
demonstrated NOT to reach the hardware. Any joint-limit guarantee has to live in the driver.

**3. "No real-robot log has ever been analysed for vibration" -- NO LONGER TRUE.** Analysed
2026-08-13 from `~/albc_bags/`. Thrusters were at `max|cmd| = 0.000000` throughout, so the
oscillation is arm-only. Equalising per-second gain across rates (50 Hz with delta_scale 0.02 vs
10 Hz with delta_scale 0.10) left 50 Hz unstable and 10 Hz calm, which excludes gain and points at
LOOP DELAY. Confidence MEDIUM: integrator rise time and the GRU history's wall-clock window also
differ between the two conditions, so the isolation is not clean.

What still stands from the original page: the runaway is not a sim-to-real gap (both sides
unbounded, so clamping sim alone would manufacture one), and the genuine remaining arm gap is the
CONTROLLER FORM (firmware ~1 kHz PID with integral + profile-velocity trapezoid vs Isaac's
ImplicitActuator Kp=100/Kd=3), still blocked on the XW540-T260 step response.

[EVIDENCE: `joint_angle_command.cpp:291-293`; `np_policy.py:228-230,253`; Dynamixel read
J1 = -35.54 rad / HW error 0x20, J2 ping 5/5 COMM_RX_CORRUPT; bag analysis of five runs,
max per-tick command step 0.10 rad with 0 steps above pi]
[CONFIDENCE: HIGH for 1 and 2, MEDIUM for the delay verdict in 3]

---

## Update (2026-08-14T07:49:38.891620)

BLOCKED-ON CORRECTED 2026-08-14, and the remaining scope narrowed to one item.

This lead carried an EMPTY blocked-on field, so the backlog hook read it as schedulable. It is not.
Reading the page against its own 2026-08-13 correction, THREE of its four threads are already closed
and the fourth is hardware-blocked:

| thread | state |
|:--|:--|
| runaway is a sim-to-real gap | CLOSED, refuted -- both sides unbounded, so clamping sim alone would MANUFACTURE a gap |
| deployed accumulator re-seeds from a constant | CLOSED, fixed -- `robot/albc_rl/numpy_port/np_policy.py:228-230` now seeds from the measured joint angle |
| no real-robot log ever analysed for vibration | CLOSED -- analysed 2026-08-13 from `~/albc_bags/`; thrusters at `max abs(cmd)=0`, so the oscillation is arm-only, and equal-per-second-gain across rates left 50 Hz unstable / 10 Hz calm, pointing at LOOP DELAY (confidence MEDIUM) |
| **arm CONTROLLER FORM** | **STILL OPEN, hardware-blocked** |

THE ONE REMAINING ITEM. The real joint runs a ~1 kHz firmware PID with an integral term
(P=800/I=1/D=40) plus a profile-velocity trapezoid; Isaac runs an ImplicitActuator at Kp=100/Kd=3 with
neither. That is plant-change batch v2 item 4 and it is blocked on the XW540-T260 STEP RESPONSE bench,
which has not been run. Small-signal damping is explicitly NOT the gap -- onboard-measured overshoot
2-3% gives zeta 0.74-0.78 against Isaac's designed 0.7, and the card that measured it says not to
retune Kp/Kd. So this needs a bench measurement, not a simulation sweep.

SECOND-ORDER BLOCK. The arm is physically broken as of 2026-08-13 (J1-J2 cable severed, J1 at
-35.54 rad with OVERLOAD), so even the bench cannot be run until it is repaired -- see
[[open_on_land_the_policy_winds_j2_to_pi_and_beyond_and_the_board_]], which also carries the driver
fix that must land so the repair is not undone on the next restart.

WHAT THE CLOSED THREADS LEAVE BEHIND, worth keeping. The reset fix this page recommended SHIPPED and
then severed the J2 cable, because it was incomplete on the other side of the contract: the policy
began publishing a CUMULATIVE angle while the driver's startup baseline stayed WRAPPED. The
generalisable lesson is on the sibling page -- a rail in the policy layer does not reach the hardware,
and any joint-limit guarantee has to live in the driver.

