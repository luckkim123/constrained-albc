---
title: "P1 cross-sim arm swing: the 4.7-9.3x joint-torque gap is WITHDRAWN as a servo discretisation artifact (corrected to 0.67x), and the arm-reaction channel is eliminated as a yaw-failure candidate in both sims"
tags: ["stonefish", "isaac", "cross-sim", "p1", "joint-swing", "arm-reaction", "yaw", "retraction", "sim2real"]
created: 2026-08-14T05:30:24.356457
updated: 2026-08-14T06:08:33.349130
sources: ["p1-stonefish-20260728", "p1-isaac-20260729", "p1-correction-20260729"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# P1 cross-sim arm swing: the 4.7-9.3x joint-torque gap is WITHDRAWN as a servo discretisation artifact (corrected to 0.67x), and the arm-reaction channel is eliminated as a yaw-failure candidate in both sims

Three sessions 2026-07-28 to 2026-07-29, merged here in time order. THE THIRD ENTRY WITHDRAWS THE SECOND'S HEADLINE NUMBER -- read to the end before quoting anything.

=== 2026-07-28 Stonefish half ===
[MEASURED 2026-07-28] P1 (cross-sim joint1 swing) Stonefish half: S1 + S5 DONE, S2-S4 still
pending. Deployment sim = `stonefish_dev` on ksm-ubuntu, headless, no policy bridge, 100 Hz
logging (measured 99.99-100.3 Hz), 3 repetitions per case with a fresh sim each.

VERDICT vs the P2 ceiling: the arm-swing yaw disturbance does NOT exceed the policy's rejection
ceiling. P2 measured the ceiling with a CONSTANT injected Mz (no break through 5.0 N.m), so the
like-for-like comparison is the sustained equivalent, not the transient peak. Sustained
equivalent (I_eff * rms|r_dot|): S1ff feedforward 0.148 N.m, S1 as-specced step 1.979 N.m --
both below 5 N.m, and S1ff is below even the ~1.4 N.m max training-world steady disturbance.
CONSEQUENCE: the lead's standing condition ("unless Stonefish/tank demand exceeds ~5 N.m") is
NOT met -- no training-side yaw-torque DR axis is justified on the arm-reaction channel.

BLOCKING METHOD FINDING (this is why S1 as-specced is NOT the number to compare): the Stonefish
servo does NOT enforce its declared `max_velocity="3.1"`. On the spec's 0 -> +1.5708 rad step the
joint reaches 28.8 rad/s (9.3x the declared cap), torque bang-bangs between exactly +13.000 and
-13.000 N.m, and position overshoots 44% (to 2.265 rad). Isaac/PhysX DOES enforce the cap, so a
step command measures the servo implementations, not the plants. The agreed deviation-1 fallback
was used: an identical minimum-jerk feedforward profile replayed on both sides,
q1(t) = 1.5708*(10*tau^3 - 15*tau^4 + 6*tau^5), tau = t/1.0 s, peak rate 2.945 rad/s (under the
3.1 cap). That removed the artifact (overshoot 44% -> 0.00%, tracking error 0.067 rad).
**Cross-sim comparison must use S1ff, not S1.** Isaac side must replay the same profile.

NUMBERS (mean +- sd over 3 reps; window 20 s; null floor peak|r| = 0.0161 rad/s):
| metric | S5 null | S1 step | S1ff minjerk |
| peak |r| rad/s | 0.0161 | 24.698 +- 0.056 | 4.190 +- 0.047 |
| peak yaw excursion rad | 0.240 | 1.651 +- 0.013 | 1.462 +- 0.008 |
| end yaw excursion rad | -0.240 | -1.274 +- 0.083 | -1.273 +- 0.038 |
| Mz transient peak N.m (Isaac I) | 0.0013 | 17.49 +- 0.10 | 0.792 +- 0.015 |
| Mz sustained equiv N.m | 0.0003 | 1.979 +- 0.022 | 0.148 +- 0.088 |
| peak |tau1| N.m | 0.170 | 13.000 | 13.000 |
| settle to null floor s | 0 | 15.64 +- 0.01 | 13.69 +- 0.93 |

CORRECTION TO THIS PAGE'S BODY (claim 3): "Arm+buoy yaw inertia about joint1 ~ 0.93 kg * (0.3 m)^2
~ 0.09 kg.m^2 ~ 2.4x base Izz" UNDERSTATES by ~2.6x. The buoy centre is 0.466 m from the joint1
axis, not 0.3 m (scn: joint2 at x=0.233 on link1, Buoy compound_transform x=0.233 on link2), so
the rigid contribution alone is 0.93*0.466^2 = 0.202 kg.m^2. Measured effective I_arm = 0.234
kg.m^2 = 4.28x base -- back-derived from the end yaw excursion, and independently consistent with
the geometric sum (buoy 0.202 + link2 0.012 + link1 0.001 = 0.216 rigid, +0.018 added mass). The
verdict above still holds because the larger reaction is transient.

INDEPENDENT VALIDATION: end yaw excursion is -1.274 (S1) vs -1.273 (S1ff) -- identical to three
decimals across separate runs whose swing speed differs ~6x. Angular momentum conservation
dominates, which is the expected invariant and confirms the measurement is numerically sound.

SECONDARY FINDINGS:
- Compound hydrodynamic DRAG in Stonefish is PER-PART (disassembly of
  `sf::Compound::ComputeHydrodynamicForces` @0x1b5aa0 in libStonefish.so: per-part
  `ComputeHydrodynamicForcesSurface` @0x1b5d1d and `CorrectHydrodynamicForces` @0x1b5d2c with
  `rdi = parts[i].solid`, accumulated into compound members @0x1b5d53-0x1b5eda). The buoy's sweep
  drag IS integrated; the omega x r lever arm enters via each part's own transform. (No DWARF in
  the .so, so citations are symbol+offset.)
- yaw SIGN measured for the first time: +q1 command -> base yaw NEGATIVE (reaction), consistent
  with momentum conservation. `albc_bridge/frames.py`'s 2026-07-15 convention check covered
  roll/pitch only and explicitly skipped yaw (pure-yaw spawn was unstable), so this closes that gap.
- The quantitative canonical robot is `albc.scn`, NOT `albc_visual.scn`. The visual variant's own
  header forbids quantitative use (compound Izz shifts 0.144 -> 0.124), and the DEPLOYED install
  copy had the buoyfix unpropagated (`phy_cyl_base.obj scale="1.0"` instead of `0.965`), giving a
  hull displacement of 0.009 m^3 = +13.9% over the 0.00790 m^3 nominal. Any measurement run on the
  deployed albc_visual.scn is contaminated.
- Stonefish servo `max_velocity` non-enforcement is a standalone defect worth its own lead: the
  policy issues joint commands in deployment too, so the same bang-bang occurs there.

ARTIFACTS: report + scripts + aggregate JSON in the vault at
`0_Project/in_progress/albc/sim_validation/docs/stonefish-p1-joint-swing-2026-07-28.md` and
`.../tools/p1_joint_swing/` (commit 506c3218). Raw CSVs (20 MB, 11 files, byte-verified) at
`ksm-ubuntu:/home/ksm/stonefish_backups/p1_260728/`. P1 scenario copies live in the container at
`stonefish_dev:/workspace/{src/stonefish_sim/stonefish_description,install/share/stonefish_description}/`
as `data/robots/albc/albc_p1.scn` and `scenarios/albc_p1.scn` (= quantitative canonical + Servo2
initial 0.0 + odom rate 100).

STATUS: stays needs-experiment. S2-S4 are blocked on the P1 spec original (section 3.2
amplitude/frequency/duration table) which never reached the Stonefish side intact; once received,
only `sched_*.json` needs rewriting -- the runner, launcher and analysis are built and verified.
[CONFIDENCE: HIGH for S1/S5 numbers and the servo finding; the S2-S4 half is unmeasured]

=== 2026-07-29 Isaac half, P1 CLOSED ===
[MEASURED 2026-07-29] P1 CLOSED -- the Isaac-side replay is done, so both halves now exist. Isaac
(PhysX) ran S5/S2/S1ff/S3/S4 x3 reps each, 15 runs, all complete (1001 rows, no truncation), with
DR and faults off, hydro live via ALBCEnv._apply_action, and a 20 s settle preceding every 20 s
window to match the Stonefish schedules. Aggregated with P1_STENCIL=3 (Isaac logs at 50 Hz, so the
default 5-sample stencil would span 80 ms against Stonefish's 40 ms) and the same P1_SKIP envelope
exclusion on the sine cases.

LIKE-FOR-LIKE GATE PASSED before any number was compared. Isaac max tracking error 0.099 rad
(S1ff) with overshoot within +-1.7%, against Stonefish's 0.067 rad and 0.00%. The realized
trajectories overlap, so the PD-gain difference (Isaac 100/3 vs Stonefish normalized 1.0/1.0) does
not invalidate the comparison.

ARM-REACTION YAW GAP IS REAL BUT SMALL. Mz sustained equivalent (N.m), Isaac vs Stonefish:
  S2   0.0148 vs 0.054   (3.6x)
  S1ff 0.0363 vs 0.148   (4.1x)
  S3   0.0338 vs 0.361   (10.7x)
  S4   0.2075 vs 1.025   (4.9x)
  S5   0.0000 vs 0.0003  (null floor)
Stonefish is 3.6-10.7x larger, so the gap's DIRECTION matches this page's original claim. Its
MAGNITUDE does not: the worst physically realizable case (S4, where Stonefish saturates its 13 N.m
joint torque cap) is 1.025 N.m in Stonefish and 0.208 N.m in Isaac -- 4.9x and 24x below the P2
rejection ceiling (>=5 N.m), and 0.73x / 0.15x the ~1.4 N.m max steady training-world disturbance.

VERDICT: the arm-reaction channel is eliminated as a candidate for the yaw failure, in BOTH sims.
The "no yaw-torque DR axis" item on this page is settled -- no such axis is justified.

NEW, LARGER GAP FOUND -- AND IT IS THIS PAGE'S OWN "no arm-link hydro" ITEM, NOW QUANTIFIED.
Realizing the SAME trajectory costs Stonefish 4.7-9.3x more joint torque than Isaac:
  peak |tau1| (N.m), Isaac vs Stonefish: S2 0.79 vs 7.34 (9.3x), S1ff 2.75 vs 13.00 SATURATED
  (4.7x), S3 0.71 vs 6.31 (8.9x), S4 1.50 vs 13.00 SATURATED (8.7x).
Isaac solves S1ff at 21% of the same 13 N.m cap that Stonefish saturates. The joint-torque gap is
LARGER than the base-yaw gap, which places the discrepancy in the ARM LINK model (inertia +
hydrodynamic drag on the arm), not in base hydro -- exactly the "no arm-link hydro" gap this page
already asserted, now with a number on it. Direction agrees with the Stonefish-side measurement
that the lead's own arm inertia estimate was ~2.6x under.

MEASUREMENT NOTES for whoever repeats this:
- The replay script had TWO defects that only an actual Isaac run exposed (fixed, vault commit
  e09bc7a7): (a) the overlay import hook matches the name "isaaclab_tasks" EXACTLY, so a
  `from isaaclab_tasks.utils import ...` never triggers gym.register() and the task appears
  nonexistent; (b) logging straight from env.reset() puts the spawn transient under the
  excitation -- without settle the S5 null floor reads peak |r| 0.464 rad/s against Stonefish's
  0.0161, with the base rotating 2.31 rad on no command. Settle and episode_length_s must be
  raised together or the window auto-resets midway.
- kit swallows stdout in this container: the script's ROWS=/RUN_COMPLETE markers never reach the
  log. Judge success by output CSV row count (20 s window at 50 Hz = 1001 rows with header).
- With DR off, Isaac is deterministic: the 3-rep standard deviation is exactly 0 on every metric.
  One rep suffices on the Isaac side; sd=0 is not an anomaly.
- Isaac's residual null floor is a CONSTANT 0.077 rad/s yaw drift (peak ~= rms, angular
  acceleration ~= 0), not an undamped transient -- more settle will not remove it. It does not
  touch Mz (derived from angular acceleration) but does sit as an offset on rate metrics, which is
  why the verdict above is taken on Mz.

Full result: vault docs/isaac-p1-joint-swing-2026-07-29.md (Stonefish half:
docs/stonefish-p1-joint-swing-2026-07-28.md). Raw CSVs committed at
tools/p1_joint_swing/isaac_csv/. [CONFIDENCE: HIGH]

=== 2026-07-29 SAME-DAY CORRECTION: the 4.7-9.3x is WITHDRAWN ===
[CORRECTION 2026-07-29, same day] THE ARM-LINK HYDRO NUMBER POSTED EARLIER TODAY IS WITHDRAWN.
That update reported "realizing the same trajectory costs Stonefish 4.7-9.3x more joint torque than
Isaac" and called it the first quantification of this page's own "no arm-link hydro" item. It is not
a hydrodynamic gap. It is a servo discretisation artifact, and the corrected numbers point the other
way.

WHAT WAS MISSED. 92-94% of the Stonefish tau1 power sits above 5 Hz, and 42-48% of the base yaw-rate
power does too, against 0.1-0.5% for Isaac. The commanded motion never exceeds 0.75 Hz, so every bit
of that is chatter. P1 compared peak |tau1|, which on the Stonefish side is the amplitude of a
per-step limit cycle rather than the torque the arm dynamics demand. The raw waveform is unambiguous:
q1 advances in 0.0195 rad stair steps, dq1 alternates between full rate and EXACTLY 0.0000, and tau1
flips +7.3 / -7.0 at the 100 Hz step rate. Base wz arrives on a different ROS message (odometry, not
joint_states) and carries the same contamination, so this is physics, not logging.

MECHANISM. Servo::Update (Library/src/actuators/Servo.cpp) in POSITION mode on a Featherstone body
issues TWO competing motors every step:
    fe->MotorPositionSetpoint(jId, pSetpoint, Kp);   // target = commanded position
    fe->MotorVelocitySetpoint(jId, Scalar(0), Kv);   // target = ZERO velocity
btMultiBodyJointMotor's kp/kd are normalized per-step correction FRACTIONS, not physical gains. The
deployed 1.0/1.0 therefore means "fully close the position error this step" AND "fully brake to zero
this step". Jump, stop, jump, stop.

RIG VERIFICATION (deployed scn untouched, gains patched on a rig-only copy, S2 min-jerk 30 deg):
  gains        track_max[rad]  peak|tau1|[N.m]  HF%dq1  HF%wz
  Isaac ref        0.0310           0.791         0.0     0.1
  1.0/1.0 depl     0.0337           7.344        46.5    48.2
  0.3/0.3          0.0270           1.392         2.2     2.0
  0.1/0.1          0.0263           0.527         0.9     0.8
  1.0/0.0          0.0222           5.362        91.5    94.0
At 0.1/0.1 the chatter collapses AND tracking improves. 1.0/0.0 (velocity motor removed) is the
WORST case, which pins the cause on full-authority per-step position correction rather than on the
two motors merely disagreeing.

CORRECTED NUMBERS.
- S2 peak tau1, SF/Isaac: 9.3x -> 0.67x (0.527 vs 0.791). Stonefish demands LESS torque than Isaac
  for the same trajectory. There is NO evidence of an arm-link hydrodynamic deficit in this data.
- S2 yaw reaction Mz, SF/Isaac: 6.93x -> 3.27x, absolute 0.289 N.m.
- S1ff/S4 "saturating the 13 N.m cap": the chatter amplitude hit the cap, not a physical demand.

WHAT SURVIVES. The P1 VERDICT is unchanged and strengthened: the arm-reaction channel is not a
candidate for the yaw failure. The correction moves the gap DOWN, and the worst case now sits ~17x
below the >=5 N.m P2 rejection ceiling. The "no yaw-torque DR axis" conclusion also stands.

WHERE THE RESIDUAL 3.27x GOES. Not to the arm. Base rotational damping is already measured 45-100x
short (audit item 7), and a base that is under-damped reacts more to the same arm impulse. This
residual is a second face of a known gap, not a new one.

DEPLOYMENT IMPACT. The deployed albc.scn Servo1/Servo2 carry the same 1.0/1.0, so the deployed arm
bang-bangs every physics step and injects high-frequency impulses into the base. This is the H3b
"actuator dynamics bypassed" item that albc-vibration-rootcause left as plausible/low with "time
constant unmeasured" -- the problem is discretisation, not a time constant.

BLOCKED_ON UPDATE. The arm-link hydro item is closed (no gap found), so this page's remaining open
item is the buoy added-mass one, which needs the P-C measurement.

Full result: vault docs/servo-chatter-p1-correction-2026-07-29.md. Raw CSVs and scripts at
tools/p1_joint_swing/servo_probe/. [CONFIDENCE: HIGH]

---

## Update (2026-08-14T06:08:33.349130)

[PATH CORRECTION 2026-08-14, same day as this page was created] The three vault reports this page
cites were renamed hours after this page was written. Every finding is unchanged; only the pointers
moved. Folder is `0_Project/in_progress/albc/sim_validation/docs/`.

    old:  stonefish-p1-joint-swing-2026-07-28.md
    new:  2026-07-28-stonefish-p1-joint-swing.md

    old:  isaac-p1-joint-swing-2026-07-29.md
    new:  2026-07-29-isaac-p1-joint-swing.md

    old:  servo-chatter-p1-correction-2026-07-29.md
    new:  2026-07-29-servo-chatter-p1-correction.md

The vault standardised that folder on `YYYY-MM-DD-topic.md` so that `ls` is chronological. Raw CSVs
and scripts are unmoved: `tools/p1_joint_swing/` and `tools/p1_joint_swing/isaac_csv/`.

Worth recording as its own lesson: this page was written and the rename landed within the same
hour, from two sessions running on the same repository. A wiki page that names a vault path is a
pointer, and pointers age independently of what they point at. When citing a vault file, prefer
naming the folder and the topic over the exact filename, or re-check the path when the page is
next read.

