---
title: "INCIDENT post-mortem: teacher_baseline_opt + e1-e4 trained on a TAM the wiki knew was wrong; measured TAM/IMU/TAM-DR dropped at P4 batch, other batch items applied"
tags: ["incident", "post-mortem", "tam", "imu", "gate-failure", "needs-action", "pre-retrain-gate", "knowledge-propagation", "teacher-baseline"]
created: 2026-07-14T08:27:07.270840
updated: 2026-07-14T08:27:07.270840
sources: ["diagnose-20260713-081707"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# INCIDENT post-mortem: teacher_baseline_opt + e1-e4 trained on a TAM the wiki knew was wrong; measured TAM/IMU/TAM-DR dropped at P4 batch, other batch items applied

POST-MORTEM of a knowledge-propagation failure: measured/decided items recorded in the wiki for the
"next big batch" were only PARTIALLY applied at the 2026-07-12 P4 consolidation, and the highest-stakes
cluster (TAM row/permutation rewrite, IMU frame, TAM/max_thrust DR) was silently dropped. The
teacher_baseline_opt baseline + e1/e2/e3/e4 all trained on a plant model the wiki already knew was wrong.
Recorded 2026-07-14 at user request.

## Verified reconciliation — retrain manifest item vs consolidated-main code (HEAD, 2026-07-14)

Source of "what was supposed to ride the batch" = next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.

APPLIED (verified in code):
- thruster first-order lag dt bug fix -> albc_env.py:695 apply_dynamics(..., self.step_dt).
- arm velocity_limit_sim 3.1 (MEASURED 2026-07-06 XW540 plateau) + soft velocity_limit_cost 2.8 ->
  albc.py:201, config.py:62. NOTE: a measured value that DID land -> the batch was not a total failure.
- clip_fraction logging -> constraint_trpo.py:436.
- M1 encoder-in-value-optimizer -> tests/test_value_optimizer_groups.py.
- B1 dr-derived priv-obs normalization bounds -> utils/priv_obs_bounds.py derive_priv_obs_bounds_from_dr.
- TAM column reorder (238932c) -> config.py:94 _ESC_CHANNEL_ORDER=(4,0,1,5,2,3). BUT the 2026-07-06
  rotation measurement REFUTES it (3 of 4 horizontal channels mis-assigned) -> applied-but-now-wrong.

NOT APPLIED (verified):
- TAM horizontal 3-row rewrite (Mz 2-2 sign split m1/m4=-0.144, m2/m5=+0.144) + corrected permutation
  (m1<-T1,m2<-T3,m4<-T2,m5<-T0). config.py Mz base row still (0.144,0.144,0.144,0.144,0,0). A column
  permutation is sign-preserving so this CANNOT be fixed by reorder alone (row values are wrong).
- IMU 45deg mounting offset + pitch negation. observations.py consumes robot.data.root_ang_vel_b raw;
  no 45deg rotation / pitch sign compensation anywhere in envs/main (grep imu_yaw_offset/pi/4 = 0).
- TAM moment-arm + max_thrust DR band (Group D). DR randomizes water_density/joint gains/payload/
  cog-cob offsets/ocean_current/obs_noise/thruster_health/sensor_noise/joint_health -- NOT
  allocation_matrix, NOT max_thrust. TAM/max_thrust have NO DR to absorb the systematic bias.

DELIBERATE / not-a-fix (correctly not applied):
- thruster nonlinear curve: uuv_cfg.py:143 enable_thrust_curve=False by decision (unmeasured plant
  model; an inaccurate curve manufactures a new gap -- keep OFF until bench-measured).
- Group C constraint over-spec sweep: an experiment, TBD, not a fix.
- learning-dynamics experiments (carry-off reset, encoder z_dim ablation, entropy-collapse isolation,
  joint1 graduated-rotation, two-phase reward retune): these RUN ON the baseline as A/B, not applied fixes.

AMBIGUOUS (needs its own check): Group A control-timing (arm 50->10 Hz). Control runs at 50 Hz
(config.py:376 decimation=4, control_decimation=1); the arm-10Hz alignment is not evidently in code.

## The pattern in what got dropped

Every dropped item is either (a) blocked on a PARTIAL measurement (TAM: vertical row + m4 HW-fault
unmeasured) and frozen all-or-nothing so even the CONFIRMED horizontal rows were held, or (b) had no
single clear owner (IMU frame, TAM DR band). Single, self-contained measured items (arm velocity limit)
landed; measured items entangled with an unfinished sibling (TAM) froze whole. This is the "no forcing
function + all-or-nothing deferral + summary omits the item" failure, on the highest-stakes item.

## Impact — honest salvage (do NOT catastrophize to "everything is worthless")

- INVALIDATED: absolute ss_error / heavy-tail numbers as a sim-to-real reference; teacher_baseline_opt's
  status as "the consolidated reference" (it is a PRE-TAM-correction baseline, mislabeled); any
  deployment/sim-to-real claim resting on the current TAM/IMU.
- LARGELY SURVIVES: the DIFFERENTIAL / mechanistic learnings of e1-e4, because all five runs share the
  SAME wrong TAM, so relative conclusions about learning dynamics + DR shaping are mostly TAM-independent:
  DORAEMON alpha=0.5 = feasibility floor (e1/e3/e4); a return-costly channel stalls the curriculum (e1);
  bias_ema obs lowers mean/CV not tail (e2); roll-tail responds to DR-dim shaping, xy-offset load-bearing
  for pitch (e4). Keepers.
- REDO SCOPE is therefore NOT "blindly re-run all 4": apply the confirmed TAM horizontal rewrite +
  corrected permutation (keep vertical-row/m4/FLU-NED explicitly open), retrain ONE corrected-TAM
  baseline, then re-validate only the winning levers (e2 bias_ema, e4-refined _y-only prune). e1/e3 are
  already settled (discard) -> no re-run.

## Root cause

The wiki succeeded as an ARCHIVE (this reconciliation was recovered in minutes with commit anchors) and
failed as a GATE. No machine-checkable actionable status; no forcing function at the launch/consolidation
boundary; all-or-nothing deferral; the baseline DESIGN omitted TAM from its delta list; keyword-scoped
queries never resurfaced it. Full failure-mode enumeration + the harness fix that addresses each are in
the handoff prompt at /workspace/.sp/plans/2026-07-14-wiki-family-backlog-mechanism-handoff.md.

## Corrective actions

- content-now (this project): a single open-actionable ledger enumerating the pre-retrain HARD-gate items
  (TAM rows+permutation, IMU frame, TAM/max_thrust DR) + the experiment backlog; tag `needs-action`.
- mechanism (deferred, distributed-harness, fresh session): wiki-family actionable-status + deterministic
  enumeration + launch/summary reconciliation gate (handoff prompt above).
- TAM correction path: apply confirmed horizontal rewrite, keep vertical/m4/FLU-NED open, retrain a real
  post-TAM baseline (USER-GATED launch).

STATUS: recorded 2026-07-14. TAM correction + baseline relabel + retrain = pending user decision.

