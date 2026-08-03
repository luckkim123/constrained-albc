---
title: "Widening the encoder made latent reconstruction WORSE in absolute error: `sum(MS"
tags: ["auto-captured", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:16:03.279468
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Widening the encoder made latent reconstruction WORSE in absolute error: `sum(MS

Widening the encoder made latent reconstruction WORSE in absolute error: `sum(MSE)` at hard rose 13.5%, which is a denominator-free quantity and therefore immune to the variance movement that dominates the ratio.

[EVIDENCE: `sum(MSE)` 0.4996 -> 0.5672 from `latent_hard.npz` of `static_260803_220328` and `static_260803_233436`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-03T15:16:03.279468)

Widening the encoder made latent reconstruction WORSE in absolute error: `sum(MSE)` at hard rose 13.5%, which is a denominator-free quantity and therefore immune to the variance movement that dominates the ratio.

[EVIDENCE: `sum(MSE)` 0.4996 -> 0.5672 from `latent_hard.npz` of `static_260803_220328` and `static_260803_233436`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
