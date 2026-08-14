---
title: "OPEN: on land the policy winds J2 to pi and beyond, and the board feeds it IMU at 20 Hz / joints at 10 Hz against a 50 Hz control loop"
tags: ["sim2real", "needs-experiment", "agent-jetson", "policy", "latency", "arm"]
created: 2026-08-12T13:45:00
updated: 2026-08-12T13:45:00
sources: ["albc_bags/fieldtest_2026-08-11-12-43-33.bag", "albc_bags/fieldtest_2026-08-11-12-52-36.bag"]
links: []
category: sim2real
confidence: medium
schemaVersion: 1
---

> # CORRECTION 2026-08-14 -- three of this page's four sections have been overtaken.
>
> The measurements are still good. What is void is (a) two constants it reports as
> confirmed, (b) its all-clear on restart state, and (c) both OPEN questions, which were
> answered on 2026-08-13 -- one of them by breaking the arm.
>
> **1. The two constants in "Confirmed OK" are both dead values.**
> `imu_yaw_offset: -78.0` is now **`+102.0`** (`-78` was the 45.0 fix that left a 180 deg
> error behind; closed 2026-08-12 by three independent lineages). `order(fw<-sim) =
> [3, 5, 4, 0, 1, 2]` is now **`[3, 2, 4, 0, 5, 1]`** -- see the correction on
> `esc_deadband_and_the_six_channel_pwm_unification_that_removed_it.md`. The section's
> actual finding -- that startup log constants reach runtime -- still stands; only the
> values printed do not. Derive them from `robot/albc_rl/scripts/deployed_tam.json`,
> never from a log line or a source constant.
>
> **2. OPEN 1 (J2 winds up on land) is resolved, and it was not a land artefact.**
> The winding is the policy's joint-target INTEGRATOR running unbounded: `np_policy.py`
> accumulates `DELTA_SCALE * action[:2]` at the control rate with
> `JOINT_TARGET_CLAMP = [6*pi, inf]` -- joint1 railed, **joint2 deliberately unbounded**,
> matching sim. Nothing in the deployed stack stops it. On 2026-08-13 this ran against the
> driver-side ratchet below and wound J1 to **-5.66 turns**, which **severed the J2
> daisy-chain cable**. This page's "not evidence about water behaviour" was true and beside
> the point: the hazard was never about water.
>
> **3. "NOT stale state -- the restart does initialise" is scoped too broadly.**
> Its evidence is correct -- run 2's first joint2 COMMAND was 1.807, the physical start, not
> run 1's endpoint -- but it clears only the POLICY layer. The ratchet lives one layer down,
> in the driver: `albc_control/src/joint_angle_command.cpp:291-293` sets
> `absolute_angle = angle1` (cumulative) while `prev_commanded = fmod(angle1, 2*pi)`
> (wrapped). Baseline and first command are in different representations, so **each restart
> jumps by (k-1) turns** -- observed 1 -> 2 -> 4. A bag of commanded targets cannot see this;
> the operator's suspicion was right about the machine even though it was wrong about the
> topic. **Still unfixed as of 2026-08-14.**
>
> **4. OPEN 3 (rate mismatch) was investigated 2026-08-13: delay, not gain.**
> Lowering `~control_hz` 50 -> 10 stabilised the arm; the driver loop was found hardcoded at
> 10 Hz; a `joint_delta_scale` parameter was added to decouple per-tick gain from control
> frequency so the two can be separated. `CONTROL_DT` was also found hardcoded for 20 Hz
> against a 10 Hz `control_hz` (integral-scaling mismatch).
>
> **5. "What decides these: Tank Phase 1" has been overtaken by hardware.**
> The J2 cable is severed and J1 sits at -35.54 rad with OVERLOAD. No tank run is possible
> until it is repaired AND the driver baseline is unified with a hard clamp on
> `absolute_angle`. Do not schedule Phase 1 off this page.


# OPEN: land behaviour of the deployed policy, and two rate mismatches

Two dry runs of `albc_rl_fieldtest.launch thruster_scale:=0.0` (relay ON, arm powered,
43.5 s and 53.7 s). The plumbing passed; the behaviour raised questions that are **not yet
answered** and are deliberately left open.

## Confirmed OK (plumbing)

Startup log carried the new constants all the way to runtime:
`imu_yaw_offset: -78.0 deg`, `order(fw<-sim)=[3, 5, 4, 0, 1, 2]`,
`deadband compensation: 0.150`, `THRUSTER SAFE MODE: scale=0.0`.
`/albc/thruster_cmd` stayed at zero throughout.

## OPEN 1 -- J2 winds up on land

With the robot essentially level (`r+0.3 p-0.4 deg`), J2 target went
`1.57 -> 2.82 -> 3.31 -> 3.42` and settled near **3.09 (pi)**, later drifting to 4.6-5.1; the
second run reached **6.37 rad (~2pi)**. J1 mostly stayed within +-0.15 rad. `pi` is the
manipulability singularity (`w = sqrt|sin theta2|` = 0), where the arm cannot shift buoyancy.

A frame error CANNOT explain this: at near-zero tilt the attitude vector is near zero, and a
near-zero vector rotates to a near-zero vector. Something else in the observation drives it --
GRU state, previous-action feedback, or `bias_ema` winding against a plant that never responds.
On land there is no buoyancy, no hydrodynamic damping, and no restoring moment, so the
observation is outside the training distribution and this behaviour is **not evidence about
water behaviour**. It is also not evidence of correctness.

## OPEN 2 -- the operator saw the buoy move "the wrong way" when tilting

Not resolved. The quantitative check was inconclusive: only 80 samples exceeded 4 deg of tilt,
the tilt itself was 4-7 deg, and J1 barely moved, so the -119 deg circular-mean residual between
the commanded J1 and the lowered-side azimuth mostly reflects **both quantities being nearly
constant**, not a systematic reversal. Concentration 0.98 looks decisive and is not.

The proper test (not yet run): with the policy live, tilt the robot **15-20 deg** in one known
direction, hold 3 s, then the same the other way. The buoy is strongly positively buoyant
(URDF: buoy 26.2 N buoyancy vs ~9 N weight), so it must move toward the **lowered** side to
right the vehicle.

Note the frame chain itself was closed independently the same day: `+x = 3 o'clock` from
`joint1=0 => link1 along +x` with link1 observed at 3 o'clock, and J1 rotation confirmed
CCW-positive over two points 90 deg apart.

## NOT stale state -- the restart does initialise

The operator saw run 2 head straight to run 1's endpoint and suspected leftover state. The bags
refute it: run 2's **first** joint2 command was 1.807 (the actual physical start), not run 1's
endpoint (~4.9), and it took ~2 s to travel there **monotonically**. The two trajectories also
differ in detail (run 2 went much further, to 6.37). Both runs simply drift into a similar
region. `rosparam` persistence is a real hazard in this codebase -- `b1_channel_probe.py`
documents it -- but it is not what happened here.

## OPEN 3 -- sensor rates are far below the control rate

Measured from the bag over 43.5 s:

| topic | rate | control loop |
|---|---|---|
| `/hero_agent/sensors` (IMU) | **20.3 Hz** | 50 Hz |
| `/albc/joint_states` | **10.0 Hz** | 50 Hz |
| joint commands, `thruster_cmd` | 48.4 Hz | 50 Hz |

So 4 of every 5 ticks reuse a stale joint reading (observed `age jnt` up to **94 ms**), and
more than half reuse a stale attitude. In sim the policy sees fresh state every step. Also
logged: `tick overrun: 45.8 ms > 20.0 ms budget` (typical 13-14.7 ms).

`config.py` has a `control_delay_steps` DR field (added 2026-07-09) and a privileged latency
dim, but it is **off by default** and whether the deployed teacher enabled it is **unverified**
-- the training run directory was not found on the container. This predates today's changes.

## What decides these

Tank Phase 1 (attitude hold at `thruster_scale=0`). If the policy holds near level, OPEN 1 and
OPEN 3 are land artefacts and no retrain is justified. If it does not, these two are the
candidates to narrow, in that order.
