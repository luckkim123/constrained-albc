---
title: "The optimiser signature matches the baseline more closely than attempt 1 did, so"
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

# The optimiser signature matches the baseline more closely than attempt 1 did, so

The optimiser signature matches the baseline more closely than attempt 1 did, so the engine's standing anomalies are recipe properties rather than effects of the widened observation.

[EVIDENCE: profile engine tier 1 reports the same DIAGNOSIS items 1 and 2 (entropy collapse with `noise_std` at the floor region, early plateau) for both; `entropy` -8.95 vs -8.98 where attempt 1 read -9.12, and `Grad/actor_step` -5.0% here against -11.9% in attempt 1]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
