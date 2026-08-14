---
title: "The value function fits noticeably better on the fault-free plant while the cost"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The value function fits noticeably better on the fault-free plant while the cost

The value function fits noticeably better on the fault-free plant while the cost critic fits slightly worse, which is the expected signature of removing a stochastic actuator failure from the return distribution.

[EVIDENCE: TB final-50 means by name — `Loss/value_function` 0.50622 -> 0.35931, `Loss/cost_value` 0.74542 -> 0.81613]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
