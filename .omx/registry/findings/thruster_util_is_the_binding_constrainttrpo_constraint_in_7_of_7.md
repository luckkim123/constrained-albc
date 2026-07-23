---
title: "thruster_util is the binding ConstraintTRPO constraint in 7 of 7 runs -- A5 loosened non-binding ones"
tags: ["constraint", "ipo", "thruster_util", "slack", "auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:56.975932
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260723-134359", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# thruster_util is the binding ConstraintTRPO constraint in 7 of 7 runs -- A5 loosened non-binding ones

FINDING: across 7 training runs spanning BOTH plants (pre/post buoyancy recentre), BOTH machines (workstation/DGX) and BOTH scales (4096/8192 envs), the binding ConstraintTRPO constraint is always thruster_util. EVIDENCE (engine .omx/profile/analyze_training.py --tier 3 --deep, JC/dk = fraction of budget consumed, final window): thruster_util 0.805 (buoyanchor s30) / 0.943 (s31) / 0.920 (s32) / 0.887 (ArmN 8192) / 0.853 (dgxseed30) / 0.852 (dgxseed31) / 0.865 (dgxseed32) -- 7/7 agreement. Runner-up on s30: rp_vel_settling 0.550, then rp_rate 0.395, arm_torque 0.237, manipulability 0.118, arm_joint_vel 0.042, yaw_rate 0.030; attitude/cumul_yaw/joint1_pos sit at -0.000 (fully dormant). CONSEQUENCE: A5 (trpo_budgetslack_260721_181133) raised budgets x100 on rp_vel_settling (0.550) and manipulability (0.118) -- neither is the binding term. This is a MECHANISM for A5's null result that does NOT depend on the seed floor, and it means any future constraint-slack probe should target thruster_util. Re-visit: analysis diagnose-20260723-134359 section 'constraint'.

---

## Merged from zero_constraint_violations_in_either_run_but_the_binding_constra.md (2026-07-23T07:32:14.143051)

# Zero constraint violations in either run, but the binding constraint tightened s

Zero constraint violations in either run, but the binding constraint tightened sharply: `thruster_util` margin fell from 6.14 to 2.77 (-55%) while its J_C/d_k rose to 0.931. A4's policy is spending far more of its actuator budget to achieve worse tracking.

[EVIDENCE: `analyze_training.py` TIER 2 both runs; all `viol` entries negative]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md


---

## Merged from zero_constraint_violations_in_either_run_and_the_binding_constra.md (2026-07-23T07:32:14.143051)

# Zero constraint violations in either run and the binding constraint is unchanged

Zero constraint violations in either run and the binding constraint is unchanged — `thruster_util` remains the single active constraint (J_C/d_k 0.812 vs 0.846) with every other constraint deeply slack.

[EVIDENCE: `analyze_training.py` TIER 2 block for both runs; all `viol` entries negative (margin not breached)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md


---

## Merged from thruster_util_is_the_binding_constraint_in_7_of_7_runs_across_bo.md (2026-07-23T07:32:14.143051)

# `thruster_util` is the binding constraint in 7 of 7 runs, across both plants, bo

`thruster_util` is the binding constraint in 7 of 7 runs, across both plants, both machines and both scales. | constraint | margin | viol | JC/dk (s30) | |:--|--:|--:|--:| | thruster_util | 7.80 | -7.80 | **0.805** | | rp_vel_settling | 9.00 | -9.00 | 0.550 | | rp_rate | 6.05 | -6.05 | 0.395 | | arm_torque | 6.10 | -6.10 | 0.237 | | manipulability | 4.41 | -4.41 | 0.118 | | arm_joint_vel | 1.92 | -1.92 | 0.042 | | yaw_rate | 9.70 | -9.70 | 0.030 | | attitude | 1.00 | -1.00 | -0.000 | | cumul_yaw | 1.00 | -1.00 | -0.000 | | joint1_pos | 1.00 | -1.00 | -0.000 | Binding constraint per run (max JC/dk): s30 `thruster_util` 0.805, s31 0.943, s32 0.920, Arm N 0.887, dgxseed30 0.853, dgxseed31 0.852, dgxseed32 0.865.

[EVIDENCE: engine per-constraint table, JC/dk (fraction of budget consumed), anchor s30 shown in full; binding constraint listed for all 7]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

`thruster_util` is the binding constraint in 7 of 7 runs, across both plants, both machines and both scales. | constraint | margin | viol | JC/dk (s30) | |:--|--:|--:|--:| | thruster_util | 7.80 | -7.80 | **0.805** | | rp_vel_settling | 9.00 | -9.00 | 0.550 | | rp_rate | 6.05 | -6.05 | 0.395 | | arm_torque | 6.10 | -6.10 | 0.237 | | manipulability | 4.41 | -4.41 | 0.118 | | arm_joint_vel | 1.92 | -1.92 | 0.042 | | yaw_rate | 9.70 | -9.70 | 0.030 | | attitude | 1.00 | -1.00 | -0.000 | | cumul_yaw | 1.00 | -1.00 | -0.000 | | joint1_pos | 1.00 | -1.00 | -0.000 | Binding constraint per run (max JC/dk): s30 `thruster_util` 0.805, s31 0.943, s32 0.920, Arm N 0.887, dgxseed30 0.853, dgxseed31 0.852, dgxseed32 0.865.

[EVIDENCE: engine per-constraint table, JC/dk (fraction of budget consumed), anchor s30 shown in full; binding constraint listed for all 7]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
