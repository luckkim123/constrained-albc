---
title: "Plant-change batch v2: four Isaac plant corrections are now pending and each alone forces a teacher retrain, so they are batched behind one sizing gate instead of decided individually"
tags: ["plant", "batch", "retrain", "buoy", "added-mass", "damping", "thruster", "actuator", "sim-to-real", "guard-structure", "sequencing"]
created: 2026-07-29T11:46:55.315005
updated: 2026-07-29T11:46:55.315005
sources: ["stonefish-reply-20260729", "buoy-hydro-rig-20260729", "thruster-static-gain-20260729", "servo-chatter-p1-correction-20260729"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Plant-change batch v2: four Isaac plant corrections are now pending and each alone forces a teacher retrain, so they are batched behind one sizing gate instead of decided individually

[DECISION 2026-07-29, user] The pending Isaac plant corrections are NOT decided one at a time. Each of them alone would invalidate E-int (the final teacher) and break cross-run comparability for the whole campaign, so a single retrain must carry all of them. Nothing is applied until the batch is decided as a unit. [CONFIDENCE: HIGH -- user decision]

THE FOUR CANDIDATES.
1. Buoy added mass. Isaac installs (0.7, 0.7, 0.2) against a geometric target of about 2.0 kg broadside and 1.6 kg axial. Blocked not by ignorance of the number but by the guard structure: added mass is applied as an explicit external wrench, so a construction-time check raises at M_a/I_rigid >= 1.0 and DR re-clamps per env at 0.95, giving a hard ceiling of 0.8835 kg on a 0.93 kg body. Options are raise the cap, retune added_mass_stability_factor (0.4 today), or move added mass into the mass matrix as Stonefish does. See buoy_added_mass_is_wrong_in_both_sims_and_in_opposite_directions.
2. Buoy damping anisotropy, NEW and previously unrecorded on the Isaac side. quadratic_damping (10, 10, 8) makes broadside drag exceed axial, but this buoy is a squat disc (r=0.085, h=0.118, L/D=0.69) whose axial frontal area 0.02270 m2 EXCEEDS its broadside 0.02006 m2 by 1.13x, so axial drag should be the larger one. Isaac has the ordering backwards; the Stonefish rig measured 6.670 broadside against 13.917 axial, which matches geometry. Isaac values look like slender-cylinder intuition applied to a disc. Unlike item 1 this hits no guard -- it is a pure nominal correction -- but it still changes the plant.
3. Thruster static gain and shape. Isaac is linear, thrust = command * 40.0 N; real propellers go as omega squared and marinelab already ships the signed-square curve at core/thruster.py with enable_thrust_curve defaulting False. The cross-sim gap is 2.0x at full command and 4.65x in the band the policy actually uses, with zero DR coverage. See thruster_static_gain_gap_stonefish_quadratic_rated_20_03_n_vs_is.
4. Arm actuator response. Isaac runs an ImplicitActuator at SI Kp=100 / Kd=3; the real joint is a Dynamixel XW540-T260 with its own roughly 1 kHz firmware PID (P=800/I=1/D=40) plus a trapezoidal profile. Three different controller FORMS are in play across real, Isaac and Stonefish, so matching gains is undefined and only matching the RESPONSE is meaningful.

THE GATE. Two measurements block the batch, and neither is ours to schedule.
- The real T200 command-to-thrust bench curve decides WHICH SIDE item 3 aligns to. Isaac has the wrong shape, Stonefish the low scale; applying only one knob leaves the other mismatch. Without it no target number exists.
- The XW540-T260 step-response trajectory is the shared target for item 4 and should retune BOTH sims, not just the Isaac PD.
Independently of those, items 1 and 2 need a SIZING estimate before the guard structure is touched: the buoy is a 0.93 kg body on a roughly 10 kg vehicle, and nobody has measured how much its added-mass and damping errors actually move base or arm dynamics. Rewriting the added-mass integration path is a marinelab core change; it should not be justified by a ratio nobody has sized.

WHY NOT JUST ITEM 2, WHICH HITS NO GUARD. Because the cost is the retrain, not the edit. A nominal-only change still produces a different plant, a different teacher, and a campaign whose earlier runs are no longer comparable. One retrain carrying four corrections is cheaper than four retrains carrying one each. Precedent: the 2026-07-20 batch-pass decision (campaign B0b) parked several probes the same way.

DOWNSTREAM COST TO STATE PLAINLY. The student campaign student_distill_eint distills from E-int. A plant change obsoletes every student arm run against that teacher, not just the teacher itself. Either the student track finishes first, or the batch is launched knowing it invalidates that work. This is the single largest hidden cost of the batch and it should be decided explicitly, not discovered afterwards.

NOT IN THE BATCH, deliberately. HydroRC recenter-v2 is a separate question and its own page records that recentering Isaac onto the Stonefish buoy value would move the policy FURTHER from reality, so v2 cannot be designed until item 1 picks a target. IMU 45 deg offset and the TAM moment-arm band stay gated on real-robot measurements. The thruster nonlinear-curve lead is the same measurement as the item 3 gate, not a separate item.
