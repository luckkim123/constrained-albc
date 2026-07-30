---
title: "The reward decomposition shifts toward attitude and away from yaw-rate, and the "
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

# The reward decomposition shifts toward attitude and away from yaw-rate, and the 

The reward decomposition shifts toward attitude and away from yaw-rate, and the penalty terms stay flat, so the composition buys attitude accuracy at a small yaw-tracking cost rather than by loosening any penalty.

[EVIDENCE: `Reward/att_rp` 6.833 -> 6.958 (+0.125) and `Reward/yaw_vel` 2.109 -> 2.006 (-0.103) while `Reward/thruster` -0.0218 -> -0.0240, `Reward/smoothness` -0.0153 -> -0.0162, `Reward/bias` -0.0078 -> -0.0083, `Reward/torque` -0.0605 -> -0.0539 all move under 0.007 in magnitude; engine [TIER 3] Rewards total 8.81]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
