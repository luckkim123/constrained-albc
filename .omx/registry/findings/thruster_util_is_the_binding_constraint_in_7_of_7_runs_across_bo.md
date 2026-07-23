---
title: "`thruster_util` is the binding constraint in 7 of 7 runs, across both plants, bo"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

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
