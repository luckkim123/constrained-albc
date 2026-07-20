---
title: "OPEN-ACTIONABLE LEDGER: read before any sim-plant code change or baseline launch (TAM/IMU HARD-gate + experiment backlog)"
tags: ["open-actionable", "ledger", "pre-retrain-gate", "launch-gate", "needs-action", "tam", "imu", "tam-dr", "single-source"]
created: 2026-07-14T08:29:04.373111
updated: 2026-07-14T09:56:27.306248
sources: []
links: ["incident_post_mortem_teacher_baseline_opt_e1_e4_trained_on_a_tam.md", "tam_columns_must_match_robot_firmware_esc_channel_order_reorder_.md", "tam_vertical_single_motor_dual_esc_measured_2026_07_05.md", "imu_45deg_offset_pitch_negation_sim_uncompensated_2026_07_05.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage_.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
---

# OPEN-ACTIONABLE LEDGER: read before any sim-plant code change or baseline launch (TAM/IMU HARD-gate + experiment backlog)

THE single page to read BEFORE any code change to the sim plant OR any baseline launch. It enumerates
every open actionable item (measured-but-not-applied, needs-experiment, blocked-on-X) in one place, so the
backlog surfaces by construction instead of by keyword luck. Exists because the TAM/IMU corrections were
recorded but stranded and a whole baseline (teacher_baseline_opt) + e1-e4 trained on a known-wrong plant
-- see [[incident_post_mortem_teacher_baseline_opt_e1_e4_trained_on_a_tam]]. Reconcile any new baseline
DESIGN / `omx queue-launch` against THIS list; a HARD-gate item still open = do NOT label a baseline
"reference/consolidated" without explicitly recording it as pre-<item>.

## HARD-GATE — pre-retrain plant-fidelity items NOT in code (block a "reference" baseline)

| Item | Status | Code delta needed | Blocked-on | Source |
|---|---|---|---|---|
| TAM horizontal 3-row rewrite (Mz 2-2 split: m1/m4=-0.144, m2/m5=+0.144; Fx/Fy from geometry) + corrected permutation (m1<-T1,m2<-T3,m4<-T2,m5<-T0) | CONFIRMED, appliable NOW | rewrite `_BASE_ALLOCATION_MATRIX` Mz row + `_ESC_CHANNEL_ORDER` in envs/main + envs/full_dof config.py | nothing (horizontal confirmed; m4 rotation inferred by diagonal symmetry) | [[tam_columns_must_match_robot_firmware_esc_channel_order_reorder__]] |
| TAM vertical row (Fz/My) redesign — one physical motor, dual-ESC, left-right (not fore/aft 2ch) | measured, NOT applied | rewrite Fz/My rows (no independent 2nd heave channel; no fore/aft pitch coupling) | m4 remeasurement (HW fault) + full B1 vertical translation | [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]] |
| IMU 45deg mounting offset + pitch negation | sim-UNCOMPENSATED | decide + (maybe) apply frame correction in observation pipeline | 3DM-GX5 datasheet (FLU/NED vs chip quirk); note firmware downstream sign already reconciled to sim | [[imu_45deg_offset_pitch_negation_sim_uncompensated_2026_07_05]] |
| TAM moment-arm + max_thrust DR band (currently NONE — the only systematic-bias axis with no DR) | NOT applied | add DR range for allocation/max_thrust to a physically-defensible band | source a defensible numeric band (no load cell to measure) | [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] |

APPLIED-BUT-REFUTED (re-open, do not treat as done): TAM column reorder `238932c` is in code but the
2026-07-06 rotation measurement shows 3 of 4 horizontal channels mis-assigned -> superseded by the
horizontal-rewrite row above.

## OTHER open items (not hard-gate)

| Item | Status | Note |
|---|---|---|
| Experiment backlog (command-box eval, DORAEMON per-axis gate, latency-as-DR-dim, state_std z-cond, etc.) | see the dedicated page | [[baseline_open_experiment_leads_backlog_beyond_heavy_tail_triage__]] |
| Thruster nonlinear curve (deadband + signed-square) | present OFF-by-default (deliberate) | keep OFF until bench-measured; an unverified curve manufactures a new gap |
| Group C constraint over-spec sweep (joint1_pos 720deg-slack) | TBD, not audited | experiment, not a fix |
| Group A control-timing (arm 50->10 Hz) | AMBIGUOUS | control runs at 50 Hz (decimation=4, control_decimation=1); arm-10Hz alignment not evidently in code — verify separately |

## Rule (until the harness gate lands)

Before any new baseline DESIGN or `omx queue-launch`: (1) read this page; (2) reconcile the DESIGN's delta
list against the HARD-GATE table; (3) either apply every open HARD-gate item, or explicitly record in the
DESIGN "this baseline is pre-<item>" for each unapplied one. Never launch a "reference/consolidated"
baseline with a silent open HARD-gate item. The structural enforcement of this rule is the deferred
harness fix: /workspace/.sp/plans/2026-07-14-wiki-family-backlog-mechanism-handoff.md.

---

## Update (2026-07-14T09:56:27.306248)

STATUS SYNC 2026-07-14 (wiki-status mechanism now live in omx v0.7.0): HARD-GATE item 1 (TAM horizontal 3-row rewrite + ESC permutation) was APPLIED in commit 3bb042b -> its page is now status:resolved; the table row above is stale on that point. Items 2-4 remain OPEN and are now machine-enumerable via status:needs-apply-before-retrain (tam_vertical / imu_45deg / sim_hydro_nominal-TAM-DR-band) -- omx queue-launch will REFUSE until each is applied or explicitly --ack-gate <slug>. The experiment backlog page is status:needs-experiment. This ledger stays the human roster; the per-item statuses are the machine gate.
