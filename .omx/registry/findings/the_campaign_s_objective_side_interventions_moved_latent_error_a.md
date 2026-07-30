---
title: "The campaign's objective-side interventions moved latent error almost exclusivel"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The campaign's objective-side interventions moved latent error almost exclusivel

The campaign's objective-side interventions moved latent error almost exclusively at the levels where the actor is least sensitive, and barely at all at the one level where it is most sensitive — which is a sufficient explanation for five consecutive sub-floor control nulls without needing any of them to have been mis-designed.

[EVIDENCE: lambda 0 -> 4 spans 2.56x of in-loop MSE at `none` (sensitivity 0.036 deg/unit) but only 1.04x at `hard` (sensitivity 1.070 deg/unit); the campaign's control verdicts were read across all four levels, three of which cannot resolve a latent change at these magnitudes]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
