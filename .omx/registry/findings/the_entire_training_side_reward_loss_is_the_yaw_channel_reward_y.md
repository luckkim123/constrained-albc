---
title: "The entire training-side reward loss is the yaw channel — `Reward/yaw_vel` -13.2"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The entire training-side reward loss is the yaw channel — `Reward/yaw_vel` -13.2

The entire training-side reward loss is the yaw channel — `Reward/yaw_vel` -13.2% accounts for -0.275 of the -0.247 total delta, while the attitude term is flat (+0.5%).

[EVIDENCE: TB last-200-iter means; yaw_vel 1.8173 vs 2.0927 = -0.2754 vs Reward/total 8.8187 vs 9.0654 = -0.2467]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
