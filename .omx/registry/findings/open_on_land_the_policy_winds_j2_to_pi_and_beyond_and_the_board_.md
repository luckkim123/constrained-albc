---
title: "OPEN: on land the policy winds J2 to pi and beyond, and the board feeds it IMU at 20 Hz / joints at 10 Hz against a 50 Hz control loop"
tags: ["sim2real", "agent-jetson", "policy", "latency", "arm", "open-lead", "j2", "driver", "blocked-hardware"]
created: 2026-08-14T06:46:47.837427
updated: 2026-08-21T06:44:15.675571
sources: ["albc_bags/fieldtest_2026-08-11-12-43-33.bag", "albc_bags/fieldtest_2026-08-11-12-52-36.bag", "wiki-backlog-20260814"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "UNBLOCKED 2026-08-21 on the hardware side: the J2 branch was replaced and passed 590/590 clean at rest plus two rotation runs with zero comm failures; the driver-side baseline fix shipped 2026-08-17 (agent-jetson 6b85836 + 4239445, on the board). What remains is simply that the run has not been made. Residual risk: multi-turn winding stress is still unproven-safe (the 08-21 rotation test was only +-7 deg), so keep ~joint1_abort_rad at 6pi."
---

# OPEN: on land the policy winds J2 to pi and beyond, and the board feeds it IMU at 20 Hz / joints at 10 Hz against a 50 Hz control loop

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

RECATEGORISED 2026-08-14: this page was originally hand-written with `category: sim2real`, a value omx_core's CATEGORIES rejects, so it had never passed through `omx wiki add`. Re-added through the CLI at the same slug with category=reference and the open lead moved from a TAG into the real `status` field, where queue-launch, the route hook and exp-design can finally see it. Body preserved verbatim.

---

## Update (2026-08-14T07:49:19.963903)

BLOCKED-ON CORRECTED 2026-08-14. This lead carried an EMPTY blocked-on field, so the per-turn backlog
hook and exp-design have been reading it as "unblocked" -- schedulable today. It is not: the arm it
would run on is physically broken.

THE HARDWARE STATE, from this page's own 2026-08-13 correction: the J1->J2 daisy-chain cable is
SEVERED, J1 reads -35.54 rad (-5.66 turns) with `HW Error 0x20 OVERLOAD`, and J2 (ID 12) pings 5/5
COMM_RX_CORRUPT. The correction already says "Do not schedule Phase 1 off this page." The status field
now says the same thing to the machine.

WHAT UNBLOCKS IT, IN ORDER. Both are required; the repair alone is not enough, because the mechanism
that broke the arm is still live in the code and would break it again on the next restart:
1. Physical repair of the J1-J2 cable and recovery of J1 from its overload position.
2. THE DRIVER-SIDE FIX, still unfixed as of 2026-08-14 --
   `albc_control/src/joint_angle_command.cpp:291-293` sets `absolute_angle = angle1` (cumulative)
   while `prev_commanded = fmod(angle1, 2*pi)` (wrapped). `updateJoint` unwraps at most ONE 2*pi, so
   the remaining (k-1) turns enter the driver's UNCLAMPED accumulator on the FIRST command of every
   restart, doubling per restart (observed -1 -> -2 -> -4 turns). The fix is to unify the baseline
   representation AND put a hard clamp on `absolute_angle` in the DRIVER.

WHY THE CLAMP MUST BE IN THE DRIVER, restated because it is the generalisable part:
`JOINT_TARGET_CLAMP = [6*pi, inf]` bounds only the POLICY's internal accumulator. The driver keeps a
SECOND, unbounded accumulator. A rail in the policy layer was demonstrated not to reach the hardware --
it was demonstrated by the hardware breaking. Any joint-limit guarantee has to live in the driver.

SCOPE NOTE. Neither unblocking step is an EXPERIMENT: one is a repair, the other is a code fix in
`albc_control`. This page keeps `needs-experiment` because the open QUESTION it holds (what the policy
does on the real arm, and OPEN 2's tilt test) is still unanswered and does need a run -- but the run
cannot be scheduled until both steps land. A session picking this lead up should expect to be doing
firmware-adjacent repair work, not analysis.

---

## Update (2026-08-21T06:44:15.675571)

## UPDATE 2026-08-21 -- the hardware block is gone

The blocked_on text on this page said the J1-J2 cable was severed and the arm needed physical
repair plus a driver-side baseline fix. Both are done.

TOPOLOGY CORRECTION: the bus is NOT a daisy chain. U2D2 branches to J1 and J2 from a common point
(operator, 2026-08-21). Do not reason from "the far end of the chain dies first" -- under a branch,
one healthy ID acquits the whole common trunk at once, which is exactly how the 2026-08-21
diagnosis localised the fault.

WHAT HAPPENED. After the 2026-08-17 code fix the same J2 branch degraded a third time. Measured
over 572 rounds: id11 572/572 perfect, id12 295/572 (51.6 percent), 35 state transitions, 26
ping-OK-but-read-FAIL and 4 garbage voltage reads -- signal corruption, not power loss. The
operator replaced the harness. After replacement: 590/590 clean over a 5-minute rest probe (zero
transitions, zero read failures, 12.0/12.1 V rock steady) and two rotation runs with zero comm
failures over 433 and 84 polls, returning to the start tick.

WHAT IS STILL NOT PROVEN: multi-turn winding stress. The rotation test was deliberately limited to
+-7 deg because the harness is not yet moulded. That stress is what parted the cable on 08-13 and
again by 08-21, so the driver guard ~joint1_abort_rad (6pi, checked on BOTH commanded and measured
angle) remains the only thing between the policy and a fourth failure.

Field record and full evidence: vault .omx/programs/simtoreal-thrusters-live/PLAN.md, 2026-08-21
block. Tools: bus_probe.py and rotate_probe.py in the vault code/ directory, board copies in
~/albc_diag/ (home, so they survive reboots -- the original lived only in /tmp and was lost).

