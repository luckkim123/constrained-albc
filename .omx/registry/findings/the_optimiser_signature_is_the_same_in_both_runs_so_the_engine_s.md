---
title: "The optimiser signature is the same in both runs, so the engine's \"2 ANOMALIES\" "
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

# The optimiser signature is the same in both runs, so the engine's "2 ANOMALIES" 

The optimiser signature is the same in both runs, so the engine's "2 ANOMALIES" status is a property of this recipe rather than of the widened observation.

[EVIDENCE: profile engine tier 1 on both runs reports the identical DIAGNOSIS items 1 and 2 (entropy collapse with `noise_std` at the floor region, early plateau); `Policy/surrogate_loss` matches to 4 decimal places (-0.10268 vs -0.10258) and `Policy/line_search_success` is exactly 1.00000 in both]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
