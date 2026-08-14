---
title: "The median-attitude env is unrepresentative on roll for BOTH runs and on yaw for"
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

# The median-attitude env is unrepresentative on roll for BOTH runs and on yaw for

The median-attitude env is unrepresentative on roll for BOTH runs and on yaw for E-obs76, so single-env trajectory plots remain unsafe to compare across these runs.

[EVIDENCE: `analyze.py eval_dr` SAMPLE-MEAN DIVERGENCE HARD — roll sample rank 2% (E-int) and 3% (E-obs76), yaw rank 0% (E-obs76)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
