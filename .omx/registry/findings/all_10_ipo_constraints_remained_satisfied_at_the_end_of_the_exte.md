---
title: "All 10 IPO constraints remained satisfied at the end of the extension (every nor"
tags: ["auto-captured", "trpo_e3_extend10k_260713_224822"]
created: 2026-07-13T23:52:53.410508
updated: 2026-07-13T23:52:53.410508
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# All 10 IPO constraints remained satisfied at the end of the extension (every nor

All 10 IPO constraints remained satisfied at the end of the extension (every normalized margin > 0); the binding constraint shifted to thruster_util (J_C/d_k 0.881, the closest to its budget) — consistent with the policy expending more control effort under the wider DR.

[EVIDENCE: engine TIER2 e3 Constraint margins all >0 — attitude 1.00, joint1_pos 1.00, cumul_yaw 1.00, thruster_util m=4.75 (J_C/d_k 0.881 binding), rp_vel_settling 9.41, manipulability 4.65, arm_torque 7.46, arm_joint_vel 2.00, rp_rate 6.05, yaw_rate 9.32; barrier_penalty −0.122]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
