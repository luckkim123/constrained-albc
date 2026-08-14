---
title: "The reward gain over E-int shrinks to +1.7% once the plant is matched, and it is"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The reward gain over E-int shrinks to +1.7% once the plant is matched, and it is

The reward gain over E-int shrinks to +1.7% once the plant is matched, and it is concentrated in `Reward/att_rp` rather than spread across terms.

[EVIDENCE: `Reward/total` 8.8624 -> 9.0103 (+1.7%) against attempt 1's 9.22 (+4.0%); `Reward/att_rp` 6.9641 -> 7.1158 while `Reward/yaw_vel` is flat at 2.00 -> 2.00; `Train/mean_reward` 265.69 -> 270.63]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
