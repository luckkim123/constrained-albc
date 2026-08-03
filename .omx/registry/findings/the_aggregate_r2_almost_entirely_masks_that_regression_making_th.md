---
title: "The aggregate `R2` almost entirely masks that regression, making this the fifth "
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The aggregate `R2` almost entirely masks that regression, making this the fifth 

The aggregate `R2` almost entirely masks that regression, making this the fifth denominator artifact in this campaign and the first where the artifact hides a LOSS rather than manufacturing a gain: the raw delta of -0.0164 reads as "no change" while the error-only delta is -0.1020.

[EVIDENCE: the decomposition table above; `1 - sum(mse_WIDE)/sum(var_B2)` = +0.1440 against B2's own +0.2460, with `sum(Var)` 0.6626 -> 0.7362]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
