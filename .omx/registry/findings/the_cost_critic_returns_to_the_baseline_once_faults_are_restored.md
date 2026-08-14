---
title: "The cost critic returns to the baseline once faults are restored, while the valu"
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

# The cost critic returns to the baseline once faults are restored, while the valu

The cost critic returns to the baseline once faults are restored, while the value function still fits 21.6% better than E-int, so part of attempt 1's value-loss drop was the observation and not only the easier plant.

[EVIDENCE: TB final-50 means — `Loss/cost_value` 0.74542 / 0.71109 / 0.81613 and `Loss/value_function` 0.50622 / 0.39663 / 0.35931 across E-int, this run, attempt 1]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
