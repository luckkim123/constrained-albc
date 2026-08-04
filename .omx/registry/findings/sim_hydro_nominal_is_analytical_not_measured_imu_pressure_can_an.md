---
title: "sim hydro nominal is analytical (not measured); IMU+pressure can anchor rotation/heave but not surge/sway/TAM"
tags: ["measurement", "system-id", "domain-randomization", "sim-to-real", "damping", "free-decay", "TAM", "sensors", "fault-tolerant-control", "thruster", "load-cell", "arm-step-response", "max_thrust", "systematic-bias", "user-decision", "batch-pass", "apply-gate", "decision"]
created: 2026-06-14T07:38:12.841674
updated: 2026-08-04T15:35:29.556995
sources: ["envs/main/config.py:139", "envs/main/mdp/events.py", "user-input-2026-07-23", "B0c-implementation-260723", "diagnose-20260723-134359", "next-20260723-203114", "static_260724_073758", "diagnose-20260727-151917", "diagnose-20260728-081953"]
links: ["curriculum_recalibration_protocol_widening_the_dr_box_requires_r.md", "tam_vertical_single_motor_dual_esc_measured_2026_07_05.md", "adding_a_dr_axis_is_half_a_change_dr_config_s_dr_tuple_fields_tr.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: resolved
blocked-on: "max_thrust half CLOSED 2026-07-27: gate D-a ADOPTED (+/-15% band, 42.5-57.5 N) after campaign B0c ran (trpo_b0cmaxthrust_s30_260724_024326) and E-int composed it into the final teacher; battery window CONFIRMED 4S LiPo ~14-16.8 V (Z6 memo). REMAINING blocker is the TAM moment-arm band only, still without a real geometric-tolerance source (CAD stack-up / bracket spec) -- which is why this page keeps needs-apply-before-retrain."
---

# sim hydro nominal is analytical (not measured); IMU+pressure can anchor rotation/heave but not surge/sway/TAM

The sim hydrodynamic nominal values are ANALYTICAL ESTIMATES, not measurements. Source comments in marinelab/marinelab/assets/albc/albc.py:36-93 say so explicitly: "Cylinder formulas (Fossen, 2021) with URDF dimensions", linear damping = "ITTC-1957 with x2.2 roughness correction", quadratic = "Cd_cross=1.17, Cd_axial=1.0". So the baseline-report heavy-tail story "low-damping envs are hard" rests on a nominal that may itself be mis-anchored -- consistent with the report CAVEAT (report.ko.md:44) where the low-damping causal sign flips between hard and ood (attribution MED, not HIGH).
HARD SENSOR CONSTRAINT (real robot): IMU + pressure ONLY. No DVL.
- IMU: angular rate p,q,r direct; attitude phi,theta direct (yaw drifts); linear accel (integrates to drifting velocity).
- Pressure: depth z direct; heave velocity w = z_dot by differentiation.
=> Rotational DOFs (roll/pitch/yaw) and heave are observable. Horizontal linear velocity (surge/sway u,v) is NOT (no DVL). Lucky alignment: the main task is attitude-only, so surge/sway velocity is not in the policy obs -- the unmeasurable axis is the irrelevant axis, and the measurable axis (rotation) is exactly where the heavy-tail blows up.
MEASURABLE from operating data (add on-robot estimation, then measure -- robot+tank available):
- Rotational damping roll/pitch/yaw (linear_damping[3:6], quadratic_damping[3:6]): IMU gyro direct, no integration drift. Method = free-decay (roll/pitch), spin-down (yaw).
- Metacentric restoring GM (center_of_gravity z = -0.05): IMU attitude; free-decay oscillation FREQUENCY gives GM, amplitude-decay ENVELOPE gives damping (exponential=linear, amplitude-proportional=quadratic).
- Heave damping (index 2): pressure differentiation.
- Net buoyancy/weight: unforced vertical drift z(t), pressure only -- simplest.
Honest boundary: free-decay does NOT fully separate added-mass from GM (both enter oscillation freq as I+I_a and GM). Damping comes out clean regardless; GM absolute needs added-mass theory value or a static tilt test.
NOT measurable from operating data -> widen DR to a physically-defensible bound instead:
- TAM (allocation_matrix, roll moment arm 0.007 m): individual thruster forces can't be separated when 6 fire together -> needs single-thruster bench. CRITICAL: TAM has NO DR AT ALL (absent from envs/main/mdp/events.py, which randomizes added_mass/lin+quad damping/yaw_damping/volume/water_density/cob-cog offset/inertia/body_mass/payload/thruster coeff+time_constant -- but NOT allocation_matrix or max_thrust). A wrong TAM is a systematic bias hitting ALL envs identically with no DR to absorb it. THE IRONY: the most dangerous param to mis-estimate (TAM) is the one operating data cannot measure. Strategy B must prioritize giving TAM/max_thrust a DR band.
- thrust_coefficient absolute scale / max_thrust: needs a load cell; operating data gives only damping-coupled relative value.
- surge/sway damping: no DVL. Has (0.4,1.7) DR; leave (not attitude-relevant) unless full-DOF.
- added mass: collinear with accel, noisy; keep its (0.5,1.5) DR, don't chase measurement.
TWO-STRATEGY PLAN (deferred, recorded at docs/plans/2026-06-14-sim-param-measurement-and-dr-anchoring.md):
A) measurable -> add free-decay logging mode to robot, run tank protocol, offline LSQ/EKF fit, anchor sim nominal (or recenter DR) to measured value.
B) un-measurable-but-important (TAM, max_thrust) -> widen DR to physically-defensible range (per-thruster gain/voltage/mounting variation; size from spec/literature, not a round number), re-train as a comparison experiment (baseline tag + exp branch per rule02), check heavy-tail/OOD don't regress.
FTC connection: this anchoring is a prerequisite for fault-tolerant-control work -- the sim domain must demonstrably COVER the real domain before fault robustness is meaningful, and faults must later be recorded per-env like DR (blocked today by eval-npz-saves-no-raw-obs).

---

## Update (2026-07-02T08:51:07.153669)

ADDENDUM (2026-07-02) — measurement feasibility revisited under a HARDER sensor constraint (no load cell), and a correction to the free-decay optimism above.

An audit enumerated 95 sim parameters and adversarially verified which MUST be physically measured on the real UUV. Result: only 3 genuine measurement targets — (a) TAM roll/pitch moment-arm, (b) thruster command->thrust curve (deadband + nonlinearity), (c) arm joint step-response (Dynamixel XW540-T260 discrete-PID vs sim continuous-PD).

CONSTRAINT UPDATE — the real robot has IMU + pressure ONLY, and NO load cell / force-torque sensor either. This tightens the earlier "IMU+pressure only, no DVL" boundary.

CORRECTION to the 2026-06-14 body above — free-decay is MEASURABLE but NON-SEPARABLE, so DOWNGRADE the earlier "measurable -> anchor rotational damping/GM" claim. A tilt-and-release free-decay with IMU is observable, but the oscillation frequency lumps GM, inertia, and added-mass into a single equation: $\omega_n^2 = \rho g V\,GM / (I + A)$ — GM, $I$, $A$ are NOT separable from one measurement. So free-decay is USELESS for parameter ID (it identifies a lumped quantity, not any single sim nominal). The 2026-06-14 optimism that free-decay could anchor rotational damping / GM is retracted; damping-from-envelope still needs an independent GM/added-mass value to be meaningful.

SENSOR REACHABILITY of the 3 targets under IMU + pressure + Dynamixel-bus-telemetry ONLY:
- TAM moment-arm and thrust curve REQUIRE a load cell / force sensor — they measure FORCE, which IMU (an accelerometer) cannot recover: a single thruster's angular accel folds in unknown inertia $I$ + added-mass $A$ via $M = (I + A)\dot\omega$ (underdetermined). NOT measurable with the current suite.
- arm step-response IS measurable — via Dynamixel bus telemetry (PresentPosition / PresentVelocity / PresentCurrent). Uses NEITHER IMU nor pressure. This is the only one of the 3 doable now.
- net buoyancy IS measurable — thrusters off, log depth $z(t)$ with the pressure sensor; the simplest onboard measurement (cheap useful bonus, not one of the 3 gap targets but worth recording).

CORE IRONY / HONEST LIMIT — what is measurable onboard = what does NOT need measuring (arm dynamics + buoyancy, already inside DR); what NEEDS measuring (TAM / thrust) = what onboard sensors CANNOT measure. The single dangerous silent-bias risk (TAM & max_thrust have NO DR band, per the body above) is exactly the axis onboard sensors cannot reach.

PRACTICAL VERDICT (no load cell):
- arm step-response (bus telemetry) = the ONLY real measurement that reduces the gap now -> do it (see the arm step-response protocol / thruster & actuator cards).
- net buoyancy (pressure) = cheap useful bonus -> do it.
- TAM roll/pitch arm + thrust curve = measurement IMPOSSIBLE without a load cell -> handle by ADDING Domain Randomization bands (TAM & max_thrust currently have NO DR band — the silent-bias risk), NOT by chasing a measurement.
- free-decay / IMU-noise -> SKIP (non-separable per the correction above; sim noise std already >= real).

Cross-links: actuator_hardware_identification_arm_xw540_t260_board_measured_p.md (arm XW540-T260 board-measured registers / discrete-PID structural gap), thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban.md (thrust deadband + nonlinear curve, off-by-default).

---

## Update (2026-07-14T09:55:54.109606)

Flagged needs-apply-before-retrain 2026-07-14 for the ledger item "TAM moment-arm + max_thrust DR band". Verified NOT applied: envs/main/config.py has NO DR range for allocation_matrix or max_thrust (max_thrust=50.0 fixed, line 139); the DR fields present are joint_damping/payload_mass/ocean_current/thruster_health only. TAM/max_thrust is the only systematic-bias axis with no DR. Add a physically-defensible band before a reference retrain, or record pre-TAM-DR.

---

## Update (2026-07-20T07:25:41.320166)

## DECISION (2026-07-20, user): ADD a DR band to TAM / max_thrust -- direction approved

The user approved the "band, not measurement" strategy for this item. It is now a decided
direction awaiting only a defensible number, not an open question about approach.

Why this one is worth doing even though it cannot be measured: TAM (`allocation_matrix`, roll
moment-arm 0.007 m) and `max_thrust` (50.0 N fixed, `envs/main/config.py:139`) are the ONLY
physics parameters with NO DR band at all. Every other channel -- added mass, linear/quadratic
damping, yaw damping, volume, water density, CoB/CoG offsets, inertia, body mass, payload, thruster
coefficient and time constant -- is randomised in `envs/main/mdp/events.py`. A parameter WITH a
band converts an estimation error into something the policy is trained to tolerate. A parameter
WITHOUT one converts the same error into a systematic bias applied identically to every env, which
the policy then learns as if it were physics. That is the single silent sim-to-real bias axis left
in this plant.

Measurement is impossible with the current sensor suite (IMU + pressure, no load cell, no
force/torque sensor): a single thruster's angular acceleration gives `M = (I + A) * omega_dot`,
underdetermined in inertia and added mass, and with six thrusters firing the individual forces do
not separate at all. So the band must be SOURCED, not measured.

REMAINING WORK is now narrow and non-experimental: produce a physically-defensible band from
per-thruster gain/voltage variation, mounting tolerance, and T200 spec/literature -- explicitly NOT
a round-number multiplier -- then add `allocation_matrix` (roll/pitch moment-arm) and `max_thrust`
to the randomisation roster and retrain as a comparison experiment under the rule-02 baseline-tag /
exp-branch discipline, checking that heavy-tail and OOD do not regress.

PLANNING NOTE: this shares its blocker with the curriculum-recalibration protocol's Step 1
([[curriculum_recalibration_protocol_widening_the_dr_box_requires_r]]) -- both need sourced
physical spans and neither can proceed on a measurement. Sourcing the spans ONCE unblocks both, so
the batch pass should treat "source defensible physical spans for TAM / max_thrust" as a single
shared prerequisite task rather than duplicating it per lead. Note the difference in what each
does with the span: the recalibration protocol WIDENS an existing DORAEMON dimension, whereas this
item CREATES a band where none exists. The second is strictly additive and does not disturb the
curriculum's expansion budget.

Adjacent but distinct, do not conflate: the vertical-pair wiring finding
([[tam_vertical_single_motor_dual_esc_measured_2026_07_05]]) is a STRUCTURAL mismatch (two vertical
thrusters are physically one motor on a dual-ESC harness), not a magnitude uncertainty, and a DR
band does not address it.

---

## Update (2026-07-20T08:43:44.130723)

2026-07-20 pass-2 sourcing result (Z6 half-done): a defensible max_thrust DR band CAN be composed from citable evidence -- ~14% from a realistic on-vehicle voltage window (14-18 V interpolated on the BlueRobotics T200 published 12/16/20 V thrust curves) + ~5% independent-lab thrust-curve-matching uncertainty (published T200 characterizations matched the vendor curve within 5%), composing to ~ +/-15% around nominal 50 N (42.5-57.5 N), comfortably inside the 20-30% actuator-gain DR magnitudes common in legged sim-to-real work. The TAM moment-arm band has NO underwater-specific mounting-tolerance source (searched 2026-07-20) -- per this page's own no-invented-bounds standard, max_thrust DR is ready-to-roster while TAM-arm DR stays blocked-on-source (CAD tolerance stack-up or vendor bracket spec needed); do not back-fill the arm band from the thrust evidence (irrelevant to geometry).

---

## Update (2026-07-23T07:08:29.469662)

## Z6 battery-voltage memo (2026-07-23, closes the battery residual)

User input (2026-07-23): the real robot battery is a 4S LiPo — full charge 16.8 V, nominal 14.8 V, practical cutoff ~14 V. The actual working window is therefore ~14-16.8 V.

The +/-15% max_thrust DR band was sourced from the generic T200 voltage window 14-18 V (+5% lab curve-matching). The 4S working window is NARROWER than that source window, so +/-15% covers the real span with margin: the band is conservative, not under-scoped. Decision: keep the band at +/-15% as rostered for B0c; no DR-config change follows from this memo.

User directive recorded: do not spend a dedicated experiment on thruster characterization; adopt a reasonable value and move on. Z6 therefore closes as this memo, not a study.

Residual ledger after this memo: the battery-window confirmation item is RESOLVED; the max_thrust half of this lead stays SOURCED and rostered as B0c (the pending apply this status waits for); the TAM moment-arm half remains blocked on a geometric-tolerance source (CAD stack-up / bracket spec).

---

## Update (2026-07-23T11:15:48.949319)

## max_thrust half: APPLY LANDED on a branch (2026-07-23), verdict still pending

Status intentionally UNCHANGED (`needs-apply-before-retrain`): the TAM moment-arm half of this
lead is still blocked on a geometric-tolerance source, and the max_thrust apply lives on an
experiment branch that may yet be discarded. This note records that the max_thrust half moved
from "rostered" to "implemented", so the next reader does not re-derive it.

WHAT LANDED (branch `exp/max-thrust-dr`, both overlay repos, baseline pinned at tag
`baseline-260723-b0c`; NOT on main, NOT pushed):
- `marinelab` `f45d612`: per-env `_max_thrust` tensor in `ThrusterModel`, `max_thrust_scale`
  argument on `randomize_parameters`, per-env clamp in `compute_wrench`. Default
  `(1.0, 1.0)` = OFF, so pre-existing callers are unchanged.
- `constrained-albc` `147751f`: `max_thrust_scale = (0.85, 1.15)` on `DomainRandomizationCfg`,
  wired at BOTH `randomize_parameters` call sites in `albc_env.py`, plus the eval-side
  registration in `dr_config.py` without which the `none` level would not collapse the band.

WHY IT WAS NOT A CONFIG FLIP (correcting the roster's implicit assumption): `max_thrust` had no
DR anywhere, and the clamp consuming it was scalar (`marinelab/core/thruster.py`), so a per-env
band could not be expressed in config alone. This is a two-repo code change and therefore falls
under the rule-02 baseline-tag / exp-branch discipline.

MECHANISM NOTE worth carrying: `thrust_coefficient_scale (0.7, 1.3)` does NOT already cover
this. The coefficient is a GAIN applied BEFORE the clamp, so scaling it moves where in the
command range saturation begins while every env still saturates at the same 50 N wrench. Only a
ceiling band changes the achievable wrench set. "Already randomised" is the wrong objection.

VERIFIED before launch: band OFF is bit-identical to the pre-B0c scalar clamp (`torch.equal`
over saturating commands), and the 0.85x/1.15x ceilings do change the output, so the axis is
live rather than a no-op.

Motivation strengthened by the anchor analysis (`diagnose-20260723-134359`): `thruster_util` is
the BINDING ConstraintTRPO constraint in 7 of 7 runs across both plants, both machines and both
scales (J_C/d_k 0.805-0.943). The parameter this lead wants banded is the ceiling of the one
channel the CMDP actually binds through, which is why the probe is mechanistically motivated
rather than a generic "add DR" move.

Registration trap this surfaced is written up separately:
[[adding_a_dr_axis_is_half_a_change_dr_config_s_dr_tuple_fields_tr]].

Proposal: `next-20260723-175314` (campaign label B0c, lint-clean). Not launched -- training
remains human-gated.

---

## Update (2026-07-23T22:48:49.363229)

[FINDING] B0c (the max_thrust ±15% DR band = this lead's max_thrust apply sub-item) RAN
2026-07-24 and returned NULL-on-nominal, single-seed TERMINAL. Applying the sourced band
costs ~nothing at the nominal plant: none/roll os_env_mean +2.03 pp (~+0.6 deg transient
overshoot, just above the ~0.33 pp eval-noise floor), roll ss_error unchanged within noise
(-0.027 deg vs a ~0.04 deg run-to-run wobble), pitch flat. Neither pre-registered floor
crossed (>=10 pp os OR >=0.10 deg ss_error). So the physically-correct band is
regression-free on nominal while adding a robustness dim the anchor lacked.

[EVIDENCE: eval trpo_b0cmaxthrust_s30_260724_024326/eval/static_260724_073758 vs anchor
trpo_buoyanchor_s30/eval/static_260723_091813, roll all four levels, code-exec 2026-07-24;
verdict rule proposal next-20260723-203114; noise floors from E1 static_260724_040413]
[CONFIDENCE: HIGH]

STATUS: still needs-apply-before-retrain. The max_thrust APPLY is NOT auto-closed by B0c
running -- it closes only if the human ADOPTS B0c as the fidelity-correct baseline (SSOT 0b
decision, left for the human; if adopted -> final teacher changes -> re-distill + re-run
C4a/E4). The TAM moment-arm band sub-item stays blocked (no geometric-tolerance source).
Battery-voltage window confirmed 4S LiPo ~14-16.8 V (Z6 memo, band conservative).

---

## Update (2026-07-27T06:28:20.510246)

D-a DECIDED 2026-07-27: the user ADOPTED the max_thrust +/-15% band into the final teacher config (PLAN.md section 12.1, commit f2296ed), together with fault-DR (D-b). The band's formal screening analysis now exists (B0c run analysis diagnose-20260727-151917: NULL-on-nominal reproduced; watch items = pitch hard DC/CV, thruster_util binding 0.805->0.853, cost-critic +25% from the priv-obs-invisible parameter). The apply happens at the E-int integration retrain (anchor + band + fault-DR); this page stays needs-apply-before-retrain until E-int actually trains with the band. TAM moment-arm half unchanged (no source).

---

## Update (2026-07-27T23:24:46.899467)

UPDATE 2026-07-28: the Stonefish-anchor arm of this lead was TESTED (HydroRC probe,
trpo_hydrorc_s30_260728_013136) and produced an Isaac-side paired-gate FAIL (roll n_gt20 0 -> 18.67
envs, yaw ss_error +18.8% at none and worse at higher levels; hard-corner collapse att_norm 1.691 vs
0.719 deg). Recentering the nominals wholesale onto the Stonefish-measured values is NOT adopted. This
page's own caveat -- real-vehicle anchoring stays the band strategy, Stonefish is NOT ground truth --
is reinforced by data: the plant family cannot absorb a 10-100x rotational-damping recenter under the
unchanged relative DR band. TAM moment-arm band remains blocked on a tolerance source (unchanged).
[EVIDENCE: report diagnose-20260728-081953 under trpo_hydrorc_s30_260728_013136/analysis]

---

## Update (2026-07-28T09:12:17.947957)

# STATUS UPDATE 2026-07-27/28: the max_thrust half of this lead is CLOSED; only the TAM moment-arm band still blocks

This page's `blocked-on` still described the max_thrust band as "the pending apply". It is no longer
pending — it has been sourced, run, judged and adopted:

- Campaign B0c (`trpo_b0cmaxthrust_s30_260724_024326`) ran the +/-15% per-env band as a one-variable
  probe and returned NULL on the nominal floors (report `analysis/diagnose-20260727-151917`).
- Gate **D-a was DECIDED ADOPT by the user on 2026-07-27**: the band enters the final config as a
  sim-fidelity correction.
- E-int (`trpo_eint_s30_rs2350_260727_195102`) composed it with fault-DR into the final teacher and
  measured the composition as sub-additive on the shared thruster budget (`thruster_util` J_C/d_k
  0.821 against 0.950 for exact additivity).

The page's actionable status stays `needs-apply-before-retrain` because the **TAM moment-arm band**
half is untouched and still blocked on a real geometric-tolerance source (CAD stack-up or bracket
spec). Only the blocker text is corrected, so the remaining half is not read as already-applied.

Note for anyone reading this page from a launch checklist: a run that deliberately reverts the
max_thrust band (e.g. to preserve one-variable pairing with a pre-band baseline) must acknowledge
this gate explicitly at `omx queue-launch --ack-gate` rather than silently dropping it.

[EVIDENCE: PLAN teacher-final-closeout section 12.1 gate D-a ("DECIDED 2026-07-27: ADOPT (user)"), section 12.2 E-int row (thruster_util 0.821 vs 0.950 exact-additivity, H2 refuted), section 12.3 (B0c formal report DONE 2026-07-27, diagnose-20260727-151917), section 12.4 row sim_hydro_nominal ("max_thrust half = gate D-a; TAM moment-arm cannot-close")]
[CONFIDENCE: HIGH]

---

## Update (2026-08-04T15:35:29.556995)

## VERDICT 2026-08-05 -- DEFERRED-HARDWARE (backlog-closeout program)

This page had two halves. The max_thrust half CLOSED on 2026-07-27: gate D-a was adopted with a
+/-15 percent band (42.5-57.5 N) after campaign B0c ran (trpo_b0cmaxthrust_s30_260724_024326),
and E-int composed that band into the final teacher. The battery window was confirmed as a 4S
LiPo at roughly 14-16.8 V.

The remaining half is the TAM moment-arm band, and it is blocked on a real geometric-tolerance
source -- a CAD stack-up or a bracket specification. That is a measurement, and the user skipped
measurement items on 2026-08-05. Nothing in simulation can produce a defensible tolerance band
for a physical bracket; inventing one would put a fabricated number into the plant.

Moved off the experiment queue. The lead reopens the moment a CAD stack-up exists.

Recorded by the backlog-closeout program (.omx/programs/backlog-closeout/PLAN.md section 3).
Status flipped to resolved; no experiment is scheduled for this lead.

