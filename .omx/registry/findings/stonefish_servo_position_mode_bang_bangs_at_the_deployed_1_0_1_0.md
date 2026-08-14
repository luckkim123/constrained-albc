---
title: "Stonefish Servo position mode bang-bangs at the deployed 1.0/1.0 per-step gains, and the 50 Hz odom aliased the chatter away while biasing base yaw rate +41 percent (fixed at 0.1/0.1, interim)"
tags: ["stonefish", "servo", "chatter", "aliasing", "odom", "actuator", "deployment", "sim2real"]
created: 2026-08-14T05:30:16.661225
updated: 2026-08-14T06:08:22.628736
sources: ["servo-deployed-20260729", "servo-applied-20260730"]
links: ["actuator_hardware_identification_arm_xw540_t260_board_measured_p.md"]
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Stonefish Servo position mode bang-bangs at the deployed 1.0/1.0 per-step gains, and the 50 Hz odom aliased the chatter away while biasing base yaw rate +41 percent (fixed at 0.1/0.1, interim)

Two sessions on 2026-07-29 and 2026-07-30, merged here in time order. The 2026-07-30 entry CORRECTS two numbers from 2026-07-29; where they disagree the later one wins.

=== 2026-07-29 MEASURED (deployed scene) ===
[MEASURED 2026-07-29, deployed scene] A STATIONARY arm does NOT chatter, so past base-only
measurements are clean; only arm-moving windows were contaminated. And the deployed 50 Hz odometry
was ALIASING the chatter away while biasing the observed base rate 41% HIGH -- invisible to any
spectral check.

(c) STATIONARY ARM -- the contamination question, answered without new simulation. S2 already
contains a 19 s "step" segment where q1_cmd is CONSTANT. Splitting the existing runs by segment:

  gains 1.0/1.0 (deployed), odom 100 Hz     rms dq1        max dq1     peak|tau1|   HF%wz   rms|wz|
    ramp   (arm MOVING, 1 s min-jerk)            --             --        7.397     84.9%   0.7906
    step   (arm HELD 19 s at 30 deg)       0.000002       0.000071        0.150      0.7%   0.0158

The joint is DEAD STILL while holding: 2e-6 rad/s. The 80% HF%dq1 that segment reports is a RATIO
over essentially zero variance. Mechanism: with a constant setpoint the position error converges to
zero, at which point the position motor ("go here") and the velocity motor ("stop") demand the SAME
thing and stop competing. The bang-bang needs a MOVING setpoint.

Cross-check across the whole gain sweep, on segments where the arm is commanded stationary:

  gains        rms|wz| settle   rms|wz| step
  1.0/1.0        0.034326        0.017440
  0.3/0.3        0.034283        0.016757
  0.1/0.1        0.034408        0.017260
  1.0/0.0        0.034576        0.493639   <-- Kv=0 limit-cycles even while HOLDING

Three gain settings give the same base motion to within 0.2%. A stationary arm injects nothing into
the base. EXCEPTION worth carrying: Kv=0 (position motor only) limit-cycles at rest, rms|wz| 0.494
against 0.017. The velocity motor is what PREVENTS resting chatter -- do not zero it when lowering
gains.

(b) DEPLOYED-SCENE RE-RUN. albc.scn differs from the rig albc_p1.scn in exactly two lines (joint2
initial position, odom rate); the first washes out during the 20 s settle since S2 commands q2=0.
Ran {1.0/1.0, 0.1/0.1} x {odom 50 = deployed verbatim, odom 100 = instrumented}:

  run                       track_max  track_rms  peak|tau1|  rms|tau1|  HF%dq1  HF%wz  peak|wz|  rms|wz|
  Isaac (ref)                  0.0310     0.0072       0.791      0.564    0.0%   0.1%     0.567   0.1318
  deployed 1.0/1.0 odom50      0.0053     0.0003       7.399      1.069    0.1%   0.1%     1.746   0.2502
  deployed 0.1/0.1 odom50      0.0343     0.0043       0.605      0.156    1.3%   1.3%     1.212   0.1375
  deployed 1.0/1.0 odom100     0.0196     0.0020       7.397      1.038   43.3%  49.6%     1.740   0.1775
  deployed 0.1/0.1 odom100     0.0333     0.0044       0.592      0.153    0.4%   0.4%     0.981   0.1249

The odom100 "before" row reproduces the rig (7.344 / 46.5% / 48.2%), so the rig conclusion transfers
verbatim. Gain change buys: peak tau1 12.5x lower, rms tau1 6.8x lower, HF%wz 49.6% -> 0.4%, and the
base yaw response moves ONTO Isaac (rms|wz| 0.1775 -> 0.1249 vs Isaac 0.1318; peak|wz| 3.1x -> 1.7x
Isaac).

THE 50 Hz ALIASING RESULT, which is the part with consequences beyond the arm. At the DEPLOYED odom
rate the chatter is statistically invisible: HF%dq1 0.1%, HF%wz 0.1%, track_max 0.0053. Same physics,
100 Hz sampling: 43.3% / 49.6%. The chatter is a period-2 limit cycle at the 100 Hz physics step, so
sampling every 2nd step always catches the SAME PHASE. Two consequences at once: (1) it does not look
high-frequency, so no spectral check can find it; (2) that phase sits near the extremum, so the base
angular rate is systematically INFLATED -- rms|wz| 0.2502 at 50 Hz against 0.1775 at 100 Hz (+41%;
+43% on the ramp segment alone). The policy consumes that 50 Hz odometry as its observation. So the
deployed policy's observed yaw rate was biased high by an artifact that spectral validity checks
could not see. Any base metric quoted from a deployed run WHILE THE ARM WAS MOVING should be re-read
with that in mind. At 0.1/0.1 the two sampling rates agree (0.1375 vs 0.1249).

RETRACTION of my own 2026-07-29 rig claim: "0.1/0.1 improves tracking" rests on a weak statistic.
track_max for the CHATTERING configuration scatters across 0.0053 / 0.0196 / 0.0337 purely with
sampling phase -- it is the sampled extremum of a limit cycle, not a tracking error. The defensible
statement is "0.1/0.1 tracks on par with Isaac (0.033 vs 0.031) and, unlike 1.0/1.0, is robust to
sampling."

(a) APPLY TO THE DEPLOYED albc.scn: RECOMMENDED, NOT YET WRITTEN. Backups
(albc.scn.pre_servogain_260729, both source tree and install) and the patched file
(albc_servogain01.scn, a 2-line diff) are in place; the "0.1/0.1" rows above ARE that file running
the deployed scenario. The final overwrite was blocked by the session's permission layer and needs a
human ack. stonefish_sim sits on branch exp/albc-72d-bias-ema; not committed there.

0.1/0.1 IS AN INTERIM VALUE, AND ITS REAL TARGET IS AN ALREADY-OPEN LEAD. btMultiBodyJointMotor
kp/kd are per-step correction FRACTIONS, so 1.0 was never "a gain of one" -- it was "converge in one
step", a numerical statement. Per
[[actuator_hardware_identification_arm_xw540_t260_board_measured_p]] the real joint motor is a
Dynamixel XW540-T260 running its own ~1 kHz firmware PID at register gains P=800/I=1/D=40 plus a
trapezoidal profile-velocity. Three different controller FORMS are in play (real: discrete PID with
an I-term and a profile; Isaac: ImplicitActuator SI Kp=100/Kd=3; Stonefish: per-step fraction), so
"matching gains" across them is not even defined -- only matching the RESPONSE is. The decisive
missing measurement is that card's XW540-T260 step-response trajectory, and when it lands it should
retune BOTH sims' arm actuators against one target, not just Isaac's PD.

PROBE ARTIFACT, recorded so nobody mistakes it for a finding: the 20 s settle segment is violent in
this probe because the deployed scn starts joint2 at 1.5708 while S2 step-commands q2=0. At 1.0/1.0
that transient SATURATES the 13.0 N.m max_torque and peaks |wz| at 14.7 rad/s (0.1/0.1: 10.68 N.m,
10.5 rad/s, no cap contact). Deployment never sees it because the policy commands from the current
pose. That a joint-space STEP command hits the torque cap at 1.0/1.0 is itself worth knowing.

Full result: vault docs/servo-gain-deployed-fix-2026-07-29.md. Runner dep_case.sh, analyzers
dep_analyze.py / seg_hf.py / seg_abs.py and raw CSVs dep_S2_{before,before100,after,after100}.csv at
tools/p1_joint_swing/servo_probe/. [SOURCE: servo-deployed-20260729] [CONFIDENCE: HIGH]

=== 2026-07-30 APPLIED + CORRECTIONS ===
[APPLIED 2026-07-30] The deployed Stonefish albc.scn now runs servo gains 0.1/0.1. And two numbers
reported on 2026-07-29 are corrected by repeat runs -- neither changes a conclusion, but both were
quoted on weak statistics.

APPLIED. Servo1/Servo2 position_gain and velocity_gain 1.0 -> 0.1 in both the source tree
(/workspace/src/stonefish_sim/...) and the install copy, with albc.scn.pre_servogain_260729 left
beside each as the revert. The functional diff is two <controller> lines; the other +45 lines are
comment recording why. Kv is deliberately NONZERO -- 1.0/0.0 limit-cycles even while HOLDING
(rms base wz 0.494 against 0.017 rad/s), so the velocity motor is what prevents resting chatter and
lowering both together is the fix, not removing one. 0.1/0.1 is recorded IN THE FILE as INTERIM,
pending the XW540-T260 step response, with the reason: the real motor runs a ~1 kHz firmware PID at
non-SI register gains plus a trapezoidal profile, Isaac runs an ImplicitActuator at SI Kp=100/Kd=3,
and Stonefish runs per-step correction fractions -- three different controller FORMS, so "matching
gains" is undefined and only matching the RESPONSE is. Post-apply verification on the deployed
scenario: track_rms 0.0041, rms|tau1| 0.151, rms|wz| 0.1365, all inside the staged band.
Not committed on exp/albc-72d-bias-ema; working tree only.

CORRECTION 1 -- the 50 Hz aliasing bias is CONFIRMED at n=2 per rate, and it is worse than first
reported. First pass was n=1 per rate, which could not separate the effect from run-to-run scatter.
Repeated at 1.0/1.0:

  rate            rms|wz| r1   r2        within-rate spread
  odom 50 (dep)     0.25020   0.24680          1.4%
  odom 100          0.17746   0.17759          0.1%

Between-rate +40.0% against a within-rate spread of 0.1-1.4%: a sampling effect, not scatter. The
worse part: at 50 Hz the HF fraction ITSELF is unstable. Two identical runs gave HF%dq1 = 0.1% and
14.8%, against a stable 43.3% / 46.5% at 100 Hz. So a clean HF fraction measured at the deployed
rate understates the chatter by a RUN-DEPENDENT amount and proves nothing whatsoever. At 0.1/0.1
the effect is gone: rms|wz| 0.1375 / 0.1232 at odom 50 and 0.1249 at odom 100, no systematic
between-rate difference, all inside ~11% run-to-run scatter.

CORRECTION 2 -- track_max is unusable at EITHER gain setting; use track_rms. I reported "0.1/0.1
tracks on par with Isaac and, unlike 1.0/1.0, is robust to sampling". The robustness half rested on
two runs that happened to agree. A third gives track_max 0.0195 against 0.0343 and 0.0333 -- a 1.76x
spread at the SAME gains and the SAME sample rate. The cause is not sampling: the free-floating
settle is chaotic, so base attitude at ramp start differs per run, and a max statistic amplifies it.
The claim survives on a different statistic and comes out stronger: track_rms is 0.0041-0.0044
across four runs and both sample rates at 0.1/0.1, against Isaac 0.0072 -- Stonefish tracks TIGHTER
than Isaac, reproducibly. At 1.0/1.0 track_rms is 0.0003 (odom 50) against 0.0020-0.0022 (odom 100),
7x on sampling alone, unusable.

Same lesson on torque. rms|tau1| reproduces to 3% (1.032-1.069 -> 0.147-0.156, a 7x reduction)
while peak|tau1| scatters 1.4x at 0.1/0.1 (0.428-0.605). The 12.5x peak-torque figure reported on
2026-07-29 should be replaced by 7x on rms. GENERAL RULE for this scene: quote rms, never peak or
max -- the free-floating settle makes every extremum statistic a lottery, independently of the
sampling problem above.

Full result: vault docs/servo-gain-deployed-fix-2026-07-29.md (sections 2.1, 2.2, 3). Raw CSVs
dep_S2_{before,before_r2,before100,before100_r2,after,after100,verify,final}.csv at
tools/p1_joint_swing/servo_probe/. [SOURCE: servo-applied-20260730] [CONFIDENCE: HIGH]

---

## Update (2026-08-14T06:08:22.628736)

[PATH CORRECTION 2026-08-14, same day as this page was created] The vault report this page cites
was renamed hours after this page was written. The finding is unchanged; only the pointer moved.

    old:  0_Project/in_progress/albc/sim_validation/docs/servo-gain-deployed-fix-2026-07-29.md
    new:  0_Project/in_progress/albc/sim_validation/docs/2026-07-29-servo-gain-deployed-fix.md

The vault standardised that folder on `YYYY-MM-DD-topic.md` so that `ls` is chronological. Raw CSVs
and scripts are unmoved: `tools/p1_joint_swing/servo_probe/`.

Worth recording as its own lesson: this page was written and the rename landed within the same
hour, from two sessions running on the same repository. A wiki page that names a vault path is a
pointer, and pointers age independently of what they point at. When citing a vault file, prefer
naming the folder and the topic over the exact filename, or re-check the path when the page is
next read.

