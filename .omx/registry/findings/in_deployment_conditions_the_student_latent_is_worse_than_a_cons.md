---
title: "In deployment conditions the student latent is worse than a constant mean predic"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# In deployment conditions the student latent is worse than a constant mean predic

In deployment conditions the student latent is worse than a constant mean predictor on 8 of 9 dims at `none` and 5 of 9 at `hard`, and the count is identical across all three lambda values — the deficit is a property of in-loop covariate shift, not of the loss weighting.

[EVIDENCE: per-dim R2 = 1 - in-loop MSE / total variance of `l_true`; the same four dims (d0, d1, d5, d8) are positive at hard in every arm, with A0 the best of the three at all four (0.395 / 0.219 / 0.384 / 0.208)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
