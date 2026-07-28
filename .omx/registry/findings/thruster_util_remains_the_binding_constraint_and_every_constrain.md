---
title: "`thruster_util` remains the binding constraint and every constraint stayed insid"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `thruster_util` remains the binding constraint and every constraint stayed insid

`thruster_util` remains the binding constraint and every constraint stayed inside budget, so the composition did not push any constraint to violation — the H2 prediction of a newly binding actuation budget does not appear.

[EVIDENCE: engine [TIER 2] Constraints — binding (max J_C/d_k) is `thruster_util` at 0.821 with deepest slack `attitude`; per-constraint J_C/d_k rp_vel_settling 0.542, rp_rate 0.349, manipulability 0.146, arm_torque 0.091, arm_joint_vel 0.066, yaw_rate 0.038, attitude/cumul_yaw/joint1_pos ~ -0.000; all margins positive in the table above]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
