---
title: "Stonefish yaw-gap claim review: main-body hydro yaw torque structurally zero (symmetric added mass kills Munk); PhysX DOES model arm reaction; real gaps = buoy added-mass ~10x under, no arm-link hydro, no yaw-torque DR axis"
tags: ["sim-to-real", "stonefish", "yaw", "hydrodynamics", "munk-moment", "added-mass", "domain-randomization", "arm-reaction", "servo-velocity-cap", "cross-sim-measurement"]
created: 2026-07-16T12:56:49.986664
updated: 2026-07-30T02:29:55.722594
sources: ["next-20260724-033200", "static_260724_092023", "static_260724_100219", "diagnose-20260728-081953", "p1-stonefish-20260728", "p1-stonefish-20260729", "p1-isaac-20260729", "servo-chatter-probe-20260729", "servo-deployed-20260729", "servo-applied-20260730", "stonefish-reply-20260730"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia.md", "buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy.md", "yaw_command_is_rate_not_angle_inherited_design_defensible_only_i.md", "actuator_hardware_identification_arm_xw540_t260_board_measured_p.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: needs-experiment
blocked-on: "Deployed Stonefish albc.scn servo gains APPLIED 2026-07-30 (1.0/1.0 -> 0.1/0.1, Kv nonzero, recorded INTERIM in-file). Remaining: XW540-T260 step response, the shared response target that should retune BOTH sims arm actuators; and the T200 bench curve for the thruster static-gain item. Buoy measurement route is closed -- what is left there is an Isaac-side guard-structure decision, not a Stonefish probe."
---

# Stonefish yaw-gap claim review: main-body hydro yaw torque structurally zero (symmetric added mass kills Munk); PhysX DOES model arm reaction; real gaps = buoy added-mass ~10x under, no arm-link hydro, no yaw-torque DR axis

Code-verified review (2026-07-16) of the Stonefish-transfer claim: "Stonefish has a yaw disturbance Isaac never modeled (arm-swing reaction torque + paddling drag + rotational drag asymmetry), so the policy never learned to fight strong yaw disturbances." Verdict: the CONCLUSION is directionally right, but half the mechanism story is wrong.

CLAIM-BY-CLAIM VERDICT (all against envs/main + marinelab code):
1. "Isaac hydro = per-axis constant damping" -- PARTIALLY RIGHT. Damping is diagonal (hydrodynamics.py:396-398, damping_cross_coupling=None for albc), but the model also computes C_A Coriolis, added-mass force, buoyancy restoring, and applies to TWO bodies: base + buoy/link3 (albc_env.py:255-270).
2. "No geometric coupling -> no yaw disturbance from hydro" -- EXACTLY RIGHT for the main body, by computation: Munk yaw moment = -cross(M_A*v, v)_z = 8.0*u*v - 8.0*v*u = 0 because surge/sway added mass are EQUAL (albc.py:52: (8.0, 8.0, 1.0, 0.09, 0.09, 0.035)). Roll/pitch Munk survives (heave 1.0 != sway 8.0); yaw alone is killed by parameter symmetry. Buoyancy moment z-component is also structurally 0 (r_cb on z-axis). Diagonal damping only opposes yaw rate. So the main-body hydro model CANNOT produce a yaw disturbance torque.
3. "Arm-swing reaction torque (angular momentum conservation) absent in training" -- WRONG. Isaac is a PhysX articulation sim; joint1 (z-axis, agent.urdf:92) drive reaction on the base is modeled exactly. Arm+buoy yaw inertia about joint1 ~ 0.93 kg x (0.3 m)^2 ~ 0.09 kg m^2 ~ 2.4x base Izz (0.0372). The policy trained against this reaction the whole time.
4. "Arm/buoy paddling drag absent" -- PARTIALLY RIGHT. The buoy (link3) has its own hydro model fed with the BUOY LINK's velocity (albc_env.py:959-962), so buoy sweep drag IS modeled at roughly the analytical magnitude (quad 10 vs cylinder estimate ~11.7). What IS missing: (a) link1/link2 have no hydro at all (slender, small), (b) buoy added mass is effectively ~10x UNDER: theory 2.67 kg -> stability cap 0.7 (albc.py:110) -> added_mass_stability_factor 0.4 (albc.py:143) -> effective ~0.28 kg. Two individually-legitimate stability guards multiply into a large model distortion.
5. "Rotational drag asymmetry absent" -- RIGHT. Diagonal damping + axisymmetric constants mean appendage asymmetry (gripper, thrusters, cable) produces zero yaw coupling in sim.
6. "Policy held yaw with weak Mz" -- SUPPORTED quantitatively. Training-world steady yaw disturbance tops out ~1.4 N m (current drag on buoy at max offset 0.47 m: (0.8*0.5 + 10*0.25) N * 0.47 m), ~0 with arm centered. Mz authority ~29 N m (4 horizontal thrusters x 0.144 m arm x 50 N, config.py:96,139). Disturbance <5% of authority. Consistent with prior wiki evidence: yaw_rate constraint slack 8.68/10, in-distribution yaw ss_error <= 0.007, yet yaw = the extreme heavy-tail axis under hard DR.

TRAINING YAW-DISTURBANCE CHANNEL INVENTORY (what the policy DID see):
- PhysX arm reaction torque (transient, large, exact).
- Buoy sweep drag at horizontal offset (real yaw moment about system CoM).
- Ocean-current drag on offset buoy (steady, <= ~1.4 N m; current is linear-only, albc_env.py:896-897, so it cannot torque the main body directly).

ABSENT CHANNELS (verified):
- Hull yaw drag asymmetry / D-matrix off-diagonals (damping_cross_coupling=None; infra EXISTS in hydrodynamics.py:391-394 with a (1,5) sway-yaw example in the docstring -- an unused knob).
- Yaw Munk moment (killed by symmetric added mass; note: for a z-axisymmetric bare hull this is physically correct -- the REAL asymmetry comes from appendages).
- Arm-link (link1/link2) hydro; ~90% of buoy added mass.
- Any external push/torque DR event (events.py has none: hydro/current/joint/payload/mass/friction only).
- Per-thruster asymmetry: thrust_coefficient DR is per-env shared (thruster.py:77), fault injection enable=False default (config.py:331), TAM/max_thrust has no DR at all (see sim_hydro page). A "yaw torque disturbance" axis does not exist in the DR space.

CAVEAT: Stonefish is ALSO an approximation (per-link geometry-based added mass/drag coefficients, not CFD). Its per-link application naturally creates geometric coupling, but its yaw-disturbance MAGNITUDE is not ground truth -- Isaac may under-model and Stonefish may over-model. The arbiter is the real vehicle (tank test), not either simulator.

OPEN PROBES (measurement BEFORE any training-code change):
P1. Cross-sim arm-swing response: same checkpoint, joint1 step/sine in Isaac and Stonefish, log yaw rate + Mz. Directly quantifies the reaction+paddle torque gap. No training-code change.
P2. Eval-side yaw-torque injection sweep (0.5-5 N m constant external torque during eval) -> measure where yaw tracking breaks = the policy's actual rejection ceiling. Small eval-only code addition; plant untouched; no retrain.
Only if P1/P2 show ceiling < Stonefish demand does a training intervention become justified (candidates, one variable at a time: yaw-torque DR channel; enable damping_cross_coupling; revisit buoy added-mass cap). Related blocking lead: TAM/max_thrust DR band (sim_hydro page, needs-apply-before-retrain).

Cross-links: [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] (analytical nominals, TAM no-DR), [[teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia]] (yaw = extreme tail), [[buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy]] (two-body hydro split), [[yaw_command_is_rate_not_angle_inherited_design_defensible_only_i]] (yaw is rate-tracked).

---

## Update (2026-07-24T01:12:39.843455)

[FINDING] E3/P2-yaw (proposal next-20260724-033200) MEASURES the yaw rejection ceiling and closes
the P2 half: H1 CONFIRMED -- the anchor policy has a HIGH ceiling. A constant external body-frame
yaw torque Mz was swept {0,0.5,1,2,3.5,5} N.m on anchor s30 model_4999 at the none level (fixed
nominal physics isolates the torque). none-level yaw ss_error vs Mz:

| Mz (N.m) | yaw ss_error | x base | roll ss_err | pitch ss_err |
|---|---|---|---|---|
| 0   | 0.00570 | 1.0x | 0.539 | 0.219 |
| 0.5 | 0.00581 | 1.0x | 0.556 | 0.223 |
| 1.0 | 0.00896 | 1.6x | 0.566 | 0.230 |
| 2.0 | 0.01578 | 2.8x | 0.577 | 0.251 |
| 3.5 | 0.02679 | 4.7x | 0.614 | 0.316 |
| 5.0 | 0.03640 | 6.4x | 0.673 | 0.401 |

NO break through 5.0 N.m (break line = 10x base = 0.057; 5 N.m reaches only 6.4x = 0.036), no
attitude-fail. 5.0 N.m is ~3.5x the max training-world steady disturbance (~1.4 N.m). Growth is
graceful and roughly linear -- a constant torque maps to a constant thrust trim (the 3D integral
obs supports it), exactly Lane 2's "rate-loop-cheap rejection." CONSEQUENCE: the policy side is
NOT the weak link -- a future Stonefish/tank yaw failure would indict disturbance magnitude /
modeling (or the P1 cross-sim gap), NOT missing yaw-rejection training. No training-side
yaw-torque DR axis is justified.

Instrument: eval.py --inject-yaw-torque (constant body-frame Mz on the hull hydro link via the
permanent_wrench_composer ADD path, re-applied per substep; commit 1b18631, branch
exp/latency-eval-instrument; Mz=0 byte-identical; self-gated sanity Mz=0 0.0057 vs Mz=5 0.0364).
[EVIDENCE: eval/static_260724_{092023,093722,094546,095402,100219,092900} on anchor model_4999,
64 env cuda:0, code-exec 2026-07-24; break criterion + bands from proposal next-20260724-033200]
[CONFIDENCE: HIGH]

STATUS: needs-experiment (only the P1 half remains). P2 (eval yaw-torque injection ceiling) is
DONE -- H1 high ceiling; the curve is now the standing "rejection ceiling" reference for
interpreting the C4 -> Stonefish diagnostic. P1 (cross-sim joint1 swing on the Stonefish machine)
stays DEFERRED -- needs the Stonefish host; it gives the cross-sim disturbance number that the P2
ceiling is compared against.

---

## Update (2026-07-24T07:18:08.018271)

[MEASURED 2026-07-24] P2-yaw eval sweep DONE (anchor s30, constant body-frame Mz injected at none level, instrument `--inject-yaw-torque` on exp/latency-eval-instrument). Break criterion = yaw ss_error > 10x its Mz=0 base (0.0057 -> 0.057) OR attitude-fail >5% envs. Result per Mz {0.5,1.0,2.0,3.5,5.0} N.m: yaw ss_error = 0.0058 / 0.0090 / 0.0158 / 0.0268 / 0.0364 deg (1.0x/1.6x/2.8x/4.7x/6.4x base), survival 100% at every Mz. NO BREAK through 5.0 N.m (= 3.5x the max training-world steady disturbance ~1.4 N.m). VERDICT: H1 (HIGH ceiling, Lane 2) CONFIRMED -- yaw rejection ceiling >= 5 N.m; a constant Mz maps to a small thruster trim the policy holds. CONSEQUENCE: the policy side is NOT the weak link; a Stonefish yaw failure would point at disturbance magnitude/modeling, not missing rejection training -> no training-side yaw-torque DR axis justified unless Stonefish/tank demand exceeds ~5 N.m. This measured yaw ss_error vs Mz curve is the standing "rejection ceiling" reference for the C4 -> Stonefish diagnostic. P2 half of the lead CLOSED; P1 (cross-sim joint1 swing) still deferred (needs Stonefish machine). Data: experiments/.../trpo_buoyanchor_s30_260722_134743/sweeps/p2_yaw/mz_*/summary.json.

---

## Update (2026-07-27T23:24:46.982508)

UPDATE 2026-07-28: P1 (cross-sim joint1 swing) is now the GATING pre-step for any hydro-recenter v2.
The HydroRC wholesale recenter failed the Isaac paired gate (roll n_gt20 0 -> 18.67, yaw ss +18.8%),
so the next recenter must choose HOW FAR to move the rotational damping -- exactly the number P1
measures (which closed-loop rotational damping/yaw torque the deployment sim actually exerts). Still
needs the Stonefish machine; zero GPU; zero training-code change.
[EVIDENCE: HydroRC gate result page (hydrorc recenter gate result 2026-07-28); report diagnose-20260728-081953]

---

## Update (2026-07-29T02:14:57.377387)

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
`0_Project/in_progress/krit/simulator/docs/stonefish-p1-joint-swing-2026-07-28.md` and
`.../tools/p1_joint_swing/` (commit 506c3218). Raw CSVs (20 MB, 11 files, byte-verified) at
`ksm-ubuntu:/home/ksm/stonefish_backups/p1_260728/`. P1 scenario copies live in the container at
`stonefish_dev:/workspace/{src/stonefish_sim/stonefish_description,install/share/stonefish_description}/`
as `data/robots/albc/albc_p1.scn` and `scenarios/albc_p1.scn` (= quantitative canonical + Servo2
initial 0.0 + odom rate 100).

STATUS: stays needs-experiment. S2-S4 are blocked on the P1 spec original (section 3.2
amplitude/frequency/duration table) which never reached the Stonefish side intact; once received,
only `sched_*.json` needs rewriting -- the runner, launcher and analysis are built and verified.
[CONFIDENCE: HIGH for S1/S5 numbers and the servo finding; the S2-S4 half is unmeasured]

---

## Update (2026-07-29T02:50:43.604798)

[MEASURED 2026-07-29] P1 Stonefish half now COMPLETE -- S2, S3, S4 added; the previous entry's
"S2-S4 blocked on the P1 spec original" is WITHDRAWN as a false premise. An exhaustive search of
this .omx tree found no document containing an S1-S5 case table; the authoritative P1 definition
is this page's own line 44 ("joint1 step/sine in Isaac and Stonefish, log yaw rate + Mz"). The
S1-S5 labels came from a vault hand-off brief, not from any persisted spec. Parameters were
therefore fixed by the measuring session.

CASES ADDED (joint2 = 0 throughout; all commanded rates under the declared 3.1 rad/s servo cap):
- S2 = min-jerk 0 -> 0.5236 rad, T = 1.0 s (peak 0.982 rad/s) -- 1:3 amplitude pair with S1ff
- S3 = sine A = 0.5236 rad, f = 0.25 Hz (peak 0.822 rad/s)
- S4 = sine A = 0.5236 rad, f = 0.75 Hz (peak 2.467 rad/s) -- 1:3 frequency pair with S3
Sine form for Isaac replay: q1(t) = A * s(t*f) * sin(2*pi*f*t), s(u) = 10u^3 - 15u^4 + 6u^5
clamped to [0,1]. The envelope matters: a bare A*sin starts at zero position but PEAK velocity,
which resurrects the same servo bang-bang artifact that disqualifies the step case.

VERDICT UNCHANGED -- arm-swing yaw disturbance stays below the P2 ceiling. Mz sustained
equivalent (N.m): S2 0.054 / S1ff 0.148 / S3 0.361 / S4 1.025 / S1 1.979. The worst case that
both sims can actually track is S4 at 1.025 N.m, one fifth of the >=5 N.m ceiling and below the
~1.4 N.m max training-world steady disturbance. No training-side yaw-torque DR axis is justified.
S4's transient PEAK does reach 5.48 N.m, but P2 measured with constant torque so that is not the
like-for-like number -- and S4 already saturates the torque cap, so this actuator cannot produce
a larger yaw disturbance. S4 is the physical upper bound of the arm-reaction channel.

SCALING IS TORQUE-LIMITED, NOT PLANT-LIMITED -- do not read a scaling law off this data.
Commanded ratios are exactly 3.0 in both pairs; measured response ratios are 2.42-3.19 (amplitude
S1ff/S2) and 2.38-3.19 (frequency S4/S3). A sine's angular acceleration should go as f^2 (9x for
3x frequency); measured 2.38x. The reason is visible in peak|tau1|: S1ff and S4 saturate at
exactly 13.000 N.m while S2 (7.34) and S3 (6.31) do not. The upper case of each pair is measuring
the actuator limit, not the fluid plant.

CAVEAT on end-yaw-excursion: the S5 null case itself drifts -0.240 rad over its 20 s window
(yaw damping is near zero, so the spawn transient's residual rotation never dies). Amplitude
comparisons on that metric are unreliable; only the rate-family metrics (peak/rms |r|, Mz), whose
null floor is negligible (peak 0.0161 rad/s), are used above.

METHOD: 9 further runs (3 cases x 3 repetitions), fresh sim per run, 100 Hz logging (measured
99.99-100.96 Hz), same albc_p1.scn. Sine cases aggregate the steady-state portion only, dropping
one envelope period (4 s at 0.25 Hz, 1.34 s at 0.75 Hz).

ARTIFACTS: report `0_Project/in_progress/krit/simulator/docs/stonefish-p1-joint-swing-2026-07-28.md`
and `tools/p1_joint_swing/` (vault commit f56d7178, aggregate results_260728.json covers all 6
cases with per-repetition values). Raw CSVs now 20 files / 36 MB at
`ksm-ubuntu:/home/ksm/stonefish_backups/p1_260728/`. NOTE: `stonefish_dev` has NO workspace bind
mount, so the container's /tmp/p1 working copy dies with the container -- the host backup is the
only durable copy.

STATUS: stays needs-experiment. The ONLY remaining P1 work is the Isaac-side replay of the same
profiles; every Stonefish case is done. Feeding this into HydroRC recenter-v2: PLAN.md deferred
candidate (c) log-mean rotational recenter as "arbitrary without P1" -- P1 now supplies that number.
[CONFIDENCE: HIGH]

---

## Update (2026-07-29T07:37:32.726928)

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

---

## Update (2026-07-29T08:40:39.924042)

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

## Update (2026-07-29T10:13:45.363153)

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

---

## Update (2026-07-30T02:17:30.526819)

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

## Update (2026-07-30T02:29:55.722594)

SERVO FIX APPLIED 2026-07-30, AND FOUR FIGURES ON THIS PAGE ARE RETRACTED BY THE STONEFISH SIDE'S OWN
REPEAT MEASUREMENT. The handoff item 1 is closed.

APPLIED. The deployed albc.scn now carries position_gain 0.1 and velocity_gain 0.1 on Servo1 and
Servo2, in both the source tree and the install copy, with albc.scn.pre_servogain_260729 kept beside
each as the revert. Both conditions we attached were honoured: Kv is nonzero (Kv=0 limit-cycles even
while holding, so the velocity motor is what prevents resting chatter and lowering both together is
the fix), and 0.1/0.1 is recorded as INTERIM with the XW540-T260 step response named as the pending
target. Post-apply on the deployed scene: track_rms 0.0041, rms tau1 0.151, rms wz 0.1365. Not
committed on our branch; working tree only.

RETRACTED, DO NOT QUOTE. (a) The 12.5x peak joint-torque reduction becomes 7x on rms: rms tau1
1.032-1.069 -> 0.147-0.156, reproducing to 3 percent, while peak tau1 scatters 1.4x at fixed gains.
(b) track_max is unusable at every gain setting and every sample rate: a third run gave 0.0195 against
0.0343 and 0.0333, a 1.76x spread at identical gains and rate, because the free-floating settle is
chaotic so base attitude at ramp start differs per run and a max statistic amplifies it. The claim
that 0.1/0.1 tracks at least as well as 1.0/1.0 survives on track_rms only: 0.0041-0.0044 across four
runs and both rates, against Isaac 0.0072, so Stonefish tracks TIGHTER than Isaac reproducibly. At
1.0/1.0 track_rms is 0.0003 at odom 50 against 0.0020-0.0022 at odom 100, a 7x swing on sampling
alone. (c) The 40 percent aliasing bias holds at n=2 per rate (rms wz 0.25020 and 0.24680 at odom 50
against 0.17746 and 0.17759 at odom 100, within-rate spread 1.4 and 0.1 percent) but is WORSE than
stated: at 50 Hz the HF fraction itself is unstable, HF percent dq1 coming out 0.1 and 14.8 on two
identical runs against a stable 43.3 and 46.5 at 100 Hz. A clean HF fraction measured at the deployed
rate proves nothing at all.

THE STATIONARY-ARM CONCLUSION ON THIS PAGE SURVIVES (c), AND THE REASON GENERALISES. That conclusion
never used an HF fraction. It rests on rms dq1 = 2e-6 rad/s while holding, a direct kinematic quantity
measured at odom 100 Hz, and on cross-gain INVARIANCE of rms base yaw rate: 0.034326, 0.034283,
0.034408 across three gain settings whose chatter differs by roughly 50x, a 0.2 percent spread. An
invariance argument is immune to a common-mode sampling bias, so it holds at either rate; the absolute
HF and peak figures that (c) kills were not invariance arguments. Rule to carry: when a sampling
artifact is suspected, prefer a cross-condition invariance over any absolute magnitude, and prefer rms
over peak or max on anything measured off a chaotic free-floating settle.

STABILITY ARGUMENT REPLACED. The M_a/m = 10 datum is withdrawn as a physical operating point since it
existed only because of the cylinder bug. It is superseded by an analytic argument that needs no
measurement: M + M_a is positive definite for any M_a greater than zero, so the implicit
mass-matrix treatment is unconditionally stable regardless of ratio. This is the argument to use; the
architectural conclusion that Isaac's explicit external-wrench path is the one needing a stability cap
is unchanged.

UPSTREAM BUG REPORT NUMBER. Use distance-from-physics, not the missing length factor: the correct
axial added mass for a short cylinder is the disc limit (8/3)*rho*r^3, so the engine's rho*pi*r^2 sits
3*pi/(8*r) above physics, which is 13.1x for the hull at r=0.09 and 13.9x for the buoy at r=0.085. The
report should also note that getAugmentedMass averages the broken axis into the other two, so the
error propagates to all three translational axes of every cylinder solid.

[EVIDENCE: Stonefish reply 2026-07-30 quoting vault docs/servo-gain-deployed-fix-2026-07-29.md
sections 2.1, 2.2, 3 and the correction section of docs/stonefish-hydro-measurement-2026-07-27.md;
stationary-arm figures from this page's own update 2026-07-29T10:13; ratio arithmetic re-derived
2026-07-30 code-exec] [CONFIDENCE: HIGH on the applied fix and the retractions, which are the
Stonefish side's own repeat measurements; HIGH on the invariance-immunity reasoning]

