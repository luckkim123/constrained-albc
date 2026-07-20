---
title: "The 7-term reward decomposition is near-identical in shape; P-B1's total is 24% "
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The 7-term reward decomposition is near-identical in shape; P-B1's total is 24% 

The 7-term reward decomposition is near-identical in shape; P-B1's total is 24% higher, and essentially all of the gap comes from the two tracking terms (att_rp and yaw_vel). The penalty terms are indistinguishable.

[EVIDENCE: engine `analyze_training.py --tier 3 --deep` [TIER 3] Rewards, both runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The 7-term reward decomposition is near-identical in shape; P-B1's total is 24% higher, and essentially all of the gap comes from the two tracking terms (att_rp and yaw_vel). The penalty terms are indistinguishable.

[EVIDENCE: engine `analyze_training.py --tier 3 --deep` [TIER 3] Rewards, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
