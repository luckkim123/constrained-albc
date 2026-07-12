---
title: "joint1 anti-drift design history"
tags: ["joint1", "design-history", "index", "hub"]
created: 2026-07-12T14:17:30.367141
updated: 2026-07-12T14:17:30.367141
sources: ["wiki-curation-2026-07-12"]
links: ["joint1_anti_drift_constrain_the_command_cumulative_arm_b_not_the.md", "joint1_cumulative_ipo_constraint_generalizes_drift_bounded_at_oo.md", "arm_a_measured_angle_joint1_constraint_recovers_not_diverges_the.md", "joint1_cumulative_rotation_constraint_never_binds_policy_parks_a.md", "ee_leak_0_k_anchor_0_does_not_blow_up_joint1_settle_pade_ik_clam.md", "joint1_centering_reward_is_removed_on_main_6_term_but_alive_on_e.md", "engine_gap_flat_target_eval_records_joint1_trajectory_but_render.md"]
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

