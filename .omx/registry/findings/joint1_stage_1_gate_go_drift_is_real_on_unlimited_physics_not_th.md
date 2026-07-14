---
title: "joint1 Stage-1 gate GO: drift is real on unlimited physics, not the +-360deg wall artifact"
tags: ["joint1", "drift", "cumulative-rotation", "unlimited-physics", "stage-1-gate", "ee-action", "ttf-correction"]
created: 2026-07-12T18:26:08.556497
updated: 2026-07-14T12:07:34.730666
sources: ["diagnose-20260713-031533"]
links: ["joint1_anti_drift_design_history.md", "engine_gap_flat_target_eval_records_joint1_trajectory_but_render.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
status: needs-experiment
---

# joint1 Stage-1 gate GO: drift is real on unlimited physics, not the +-360deg wall artifact

STAGE-1 GATE (proposal next-20260629-173610) = GO. On marinelab unlimited physics (ed148c7, +-360deg USD wall removed), the OLD full-DOF teacher trpo_main_teacher_260525_232805 run flat-target isolates joint1 free-DOF drift; the drift is REAL, refuting Lane 3 (wall-artifact) and confirming Lane 1.

EVIDENCE (eval static_flat_260713_025309; theta_cum = joint1_target integrated-command - t0, per-env pre-termination window; analysis diagnose-20260713-031533 report.md Findings table):
- peak |theta_cum| p50 = 6.15-7.31 rad ~= 2pi (one revolution) at ALL 4 DR levels; p95 10.3-11.6 rad.
- peak excursion > 2pi in 31-48/64 envs; physical joint1_pos wraps (+-2pi seam) in 45-54/64 envs.
- the ONE env surviving 155s ramps joint1_target monotonically to -743 rad = -118 rev (data_none.npz env19).
- Lane-3 'bounded << 2pi' prediction decisively refuted.

METHOD NOTE (reusable): use PEAK excursion (max|theta_cum| over pre-term window), NOT endpoint |theta_cum| — endpoint p50 is only 2.4-3.1 rad because many command trajectories ramp past 2pi then REVERSE, so endpoint under-counts the physical excursion (which the +-2pi seam wraps corroborate). Measured joint1_pos folds into (-2pi,2pi] with ~4pi seam jumps, so a single-step |diff|>pi (impossible at vel-limit 3.1 rad/s) = a physical full-turn crossing; use it as a WRAP COUNT, not an unwrap magnitude.

DIM-COMPAT (reusable): the 260525 teacher is full-DOF (87D obs / 24D priv / 8D action / latent 9) — dimension-EXACT for Isaac-ConstrainedALBC-Full-TRPO-v0, INCOMPATIBLE with the attitude-only main Isaac-ConstrainedALBC-TRPO-v0 (69D/28D). The manifest's old task id pointed to the pre-refactor full-DOF env. Run the checkpoint on the Full task; zero code change needed (eval.py already logs joint1_cmd/target/pos, --flat-target zeros commands).

CAVEATS gating Stage 2 (do NOT auto-proceed):
- The old teacher FAST-FAILS on the new physics under flat target (attitude collapse, median time-to-failure 7-16s; survival none 1/64 .. hard 28/64), truncating most observation windows. Re-measure drift on a policy that actually station-keeps on unlimited physics.
- Directionality is regime-dependent: command-increment sign-bias none 0.60 (directional) vs hard 0.51 (~random walk); only nominal is a clean monotonic ramp, hard is large-amplitude wandering that still crosses +-2pi.
- SCOPE BOUNDARY: this teacher uses DIRECT joint-delta action (free _joint_pos_targets integrator). Stage 2's ee-action base OVERWRITES _joint_pos_targets with IK output wrapping to (-pi,pi] (albc_env.py:579, kinematics.py:213-214), so its command signal differs — Stage 2 needs its OWN baseline drift measurement before any delta tune. This gate confirms the PREMISE, not the ee-action magnitude.

Related: [[joint1_anti_drift_design_history]] (entry 7), engine-gap [[engine_gap_flat_target_eval_records_joint1_trajectory_but_render]] (the render side is now addressed: joint1_theta_cum.png produced).

---

## Update (2026-07-12T18:38:25.025563)

CORRECTION (post-review, report-reviewer catch): the fast-fail metric is 'failing-env median time-to-failure' = 7.2/9.7/9.1/6.8 s at none/soft/medium/hard — FLAT-to-decreasing, ~7-10s at every DR level. Do NOT use the median-over-all-64-with-survivors-filled-at-155s (which reads 7.2/10.5/15.8/55.0) — that statistic is dominated by the survival fraction, not failure speed, and misleadingly implies '55s survival at hard'. Survival fraction RISES with DR (1/64 -> 28/64), a SEPARATE fact from fail-ttf (which falls). Attitude-error magnitude (sqrt(err_roll^2+err_pitch^2) pre-term window mean, from data_<level>.npz) = 60.8/55.7/53.8/53.5 deg (supersedes the earlier eval-log '48-55deg' which used a different definition/window).

---

## Update (2026-07-14T12:07:34.730666)

Backlog tag (Phase 0): open lead — Stage 2 (re-measure drift on station-keeping / ee-action baseline) not yet run; do NOT auto-proceed. Soft, not run-invalidating.
