---
title: "Stonefish role narrowed to integration smoke bench (ratified 2026-08-03): no more absolute-performance or coefficient verdicts; real-robot anchors take priority; retrain principle = widen DR by measured uncertainty, never move coefficients to a simulator's value"
tags: []
created: 2026-08-03T06:10:28.634376
updated: 2026-08-03T06:10:28.634376
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# Stonefish role narrowed to integration smoke bench (ratified 2026-08-03): no more absolute-performance or coefficient verdicts; real-robot anchors take priority; retrain principle = widen DR by measured uncertainty, never move coefficients to a simulator's value

RATIFIED 2026-08-03 (user decision on the Stonefish side, transmitted to us the same day; their
canonical copy: stonefish_sim docs/stonefish-role-decision-2026-08-03.md). Four binding points:

1. STONEFISH IS AN INTEGRATION SMOKE BENCH from now on. It reports divergence/runaway/NaN,
   safety-gate activation, seam and integration bugs (obs assembly, normalization, frame
   conventions), and qualitative regime ONLY. It will never again report absolute performance,
   ratios against Isaac, hydro coefficient verdicts, or hardware-readiness calls. They built a
   smoke_run/smoke_check pair in stonefish_sim that PASS/FAILs on exactly those criteria, rms
   printed as unscored context.

2. RESOURCE PRIORITY MOVES TO REAL-ROBOT ANCHORS, thruster first. One bench session covers the
   T200 command-to-thrust curve, the XW540-T260 step response, and the state-estimation rate
   question. Until that session happens, EVERY coefficient dispute between the two simulators is
   UNDECIDABLE and gets zero further effort. This makes the plant-change-batch-v2 gates official
   cross-team priority, and it also means the batch has NO booked date.

3. NO THIRD SIMULATOR. Considered and rejected: with zero real-robot contrast data, a third
   engine only proves three things disagree, at full integration cost.

4. RETRAIN PRINCIPLE (binding on our side too): never move a hydro coefficient to either
   simulator's value. Widen the DR distribution by the measured uncertainty instead, with the
   curriculum budget retuned alongside (couples to the curriculum_recalibration lead). HydroRC-v2
   stays ours and stays geometry-or-literature derived.

HOUSEKEEPING FACTS from their message, consistent with our records: the queued HydroRC arm is
CONSUMED (launched 2026-07-28 as trpo_hydrorc_s30_260728_013136, Isaac paired gate FAILED, not
adopted); their deployed scene keeps servo 0.1/0.1 marked INTERIM plus the E-int/A0-TCN pack from
2026-07-30, both now committed on a stonefish_sim exp branch; their leftover bridge process is
cleaned and the 4-run attitude-hold bags are archived.

WHAT THEY STILL NEED FROM US (open dispatch, owner = next session or user):
- One checkpoint worth stressing. NOTE: they hold the A0-TCN pack, which is the NON-adopted arm;
  since 2026-08-03 the adopted deployment student is C3
  (deploy/student_distill_eint/pack_eint_c3_gru_260803_144925) - the dispatch should swap them to
  the C3 GRU pack, with the multi-step golden and the stateful-GRU reset caveat.
- The six metadata items: obs spec with normalization stats, DR box actually sampled, action
  spec, rates, paired Isaac eval reference.
- THE RATE QUESTION: what rate does the real deployment stack produce state estimates at. This is
  a hardware/user fact not recorded anywhere in our workspace; it now also sets their smoke-bench
  odom rate. NEEDS THE USER.
- Bench-protocol preferences before they book the hardware session. From our records: T200 curve
  should sweep the confirmed 4S LiPo supply window 14-16.8 V, cover the policy operating band
  (where the static-gain gap is 4.65x) and the deadband around zero, both thrust directions;
  XW540-T260 step response is the shared actuator target both sims retune to.

IMPLICATION FOR THE OBS4 PROGRAM (plan 2026-08-03-obs4-student-then-teacher76-program.md): point
2 is why Phase D does not wait for the plant batch - the batch gates on an unbooked hardware
session. Point 4 constrains any future plant work: DR widening plus curriculum recalibration, not
nominal moves.

