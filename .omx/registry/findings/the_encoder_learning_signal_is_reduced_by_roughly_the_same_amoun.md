---
title: "The encoder learning signal is reduced by roughly the same amount in both obs76 "
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

# The encoder learning signal is reduced by roughly the same amount in both obs76 

The encoder learning signal is reduced by roughly the same amount in both obs76 runs, so it tracks the observation width and not the plant — the one clearly plant-independent effect this experiment found besides the axis trade.

[EVIDENCE: `Grad/enc_step` 0.00245 -> 0.00157 here (-35.9%) versus 0.00245 -> 0.00156 in attempt 1 (-36.3%), a 0.4 pp difference across a plant change that moved `Constraint/margin/thruster_util` by 1.34 and `DORAEMON/success_rate` by 0.06]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
