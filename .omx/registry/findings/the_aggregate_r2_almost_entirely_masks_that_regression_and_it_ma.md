---
title: "The aggregate `R2` almost entirely masks that regression, and it masks it in the"
tags: ["auto-captured", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T15:16:03.279468
updated: 2026-08-04T05:08:41.653435
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The aggregate `R2` almost entirely masks that regression, and it masks it in the

The aggregate `R2` almost entirely masks that regression, and it masks it in the opposite direction from every previously recorded instance in this campaign: the raw delta of -0.0164 reads as "no change" while the error-only delta is -0.1020, so here the denominator hides a LOSS rather than manufacturing a gain.

[EVIDENCE: the decomposition table above; `1 - sum(mse_WIDE)/sum(var_B2)` = +0.1440 against B2's own +0.2460, with `sum(Var)` 0.6626 -> 0.7362. The direction claim is bounded to the instances actually on record: the Phase C report's d3 finding (`R2` +0.3874 while MSE worsened 23.6%) and its aggregate finding (~40% of the headline denominator-driven), both in `diagnose-20260803-223517`; no exhaustive campaign tally is asserted]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-04T05:08:41.653435)

The aggregate `R2` almost entirely masks that regression, and it masks it in the opposite direction from every previously recorded instance in this campaign: the raw delta of -0.0164 reads as "no change" while the error-only delta is -0.1020, so here the denominator hides a LOSS rather than manufacturing a gain.

[EVIDENCE: the decomposition table above; `1 - sum(mse_WIDE)/sum(var_B2)` = +0.1440 against B2's own +0.2460, with `sum(Var)` 0.6626 -> 0.7362. The direction claim is bounded to the instances actually on record: the Phase C report's d3 finding (`R2` +0.3874 while MSE worsened 23.6%) and its aggregate finding (~40% of the headline denominator-driven), both in `diagnose-20260803-223517`; no exhaustive campaign tally is asserted]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
