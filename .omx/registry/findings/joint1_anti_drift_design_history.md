---
title: "joint1 anti-drift design history"
tags: ["joint1", "design-history", "index", "hub", "drift"]
created: 2026-07-12T14:17:30.367141
updated: 2026-07-12T18:26:33.100520
sources: ["wiki-curation-2026-07-12", "diagnose-20260713-031533"]
links: ["joint1_anti_drift_constrain_the_command_cumulative_arm_b_not_the.md", "joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo.md", "arm_a_measured_angle_joint1_constraint_recovers_not_diverges_the.md", "joint1_cumulative_rotation_constraint_never_binds_policy_parks_a.md", "ee_leak_0_k_anchor_0_does_not_blow_up_joint1_settle_pade_ik_clam.md", "joint1_centering_reward_is_removed_on_main_6_term_but_alive_on_e.md", "engine_gap_flat_target_eval_records_joint1_trajectory_but_render.md", "joint1_stage_1_gate_go_drift_is_real_on_unlimited_physics_not_th.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# joint1 anti-drift design history

Sequential story of the joint1 anti-drift design (read in order; later pages correct earlier ones).

1. [[joint1_anti_drift_constrain_the_command_cumulative_arm_b_not_the]] (06-27) — A/B verdict: constrain the COMMAND (Arm B), rule established
2. [[joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo]] (06-27) — Arm B generalizes OOD, drift bounded
3. [[arm_a_measured_angle_joint1_constraint_recovers_not_diverges_the]] (06-28) — CORRECTION: Arm A recovers (early-stop artifact), loses on pitch-bias trade-off
4. [[joint1_cumulative_rotation_constraint_never_binds_policy_parks_a]] (06-30) — cumulative constraint never binds; policy parks the arm
5. [[ee_leak_0_k_anchor_0_does_not_blow_up_joint1_settle_pade_ik_clam]] (06-30) — ee_leak/k_anchor ablation holds
6. [[joint1_centering_reward_is_removed_on_main_6_term_but_alive_on_e]] (07-11) — current main state: centering reward removed

Related eval gap: [[engine_gap_flat_target_eval_records_joint1_trajectory_but_render]].

---

## Update (2026-07-12T18:26:33.100520)

7. [[joint1_stage_1_gate_go_drift_is_real_on_unlimited_physics_not_th]] (07-13) — Stage-1 GATE = GO: on unlimited physics (wall removed), the old full-DOF teacher's joint1 command drifts to ~2pi (median) and 118 rev (survivor); physical joint wraps in 45-54/64 envs. Lane-3 wall-artifact REFUTED, Lane-1 real-drift CONFIRMED. Stage 2 motivated but gated: teacher fast-fails on new physics (re-measure on a station-keeping policy), directionality regime-dependent (none 0.60 vs hard 0.51), and Stage-2's ee-action base needs its OWN baseline drift (direct-action vs ee-action signal differ). Retraining NOT authorized by this gate.
