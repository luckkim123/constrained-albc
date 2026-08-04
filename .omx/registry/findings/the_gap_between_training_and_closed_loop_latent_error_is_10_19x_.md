---
title: "The gap between training and closed-loop latent error is 10-19x — the quantified"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T04:31:12.085504
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The gap between training and closed-loop latent error is 10-19x — the quantified

The gap between training and closed-loop latent error is 10-19x — the quantified covariate-shift signature, unchanged by the obs76 intervention.

[EVIDENCE: TB `student/loss_latent` final-50-iter mean 0.00400 (per-element MSE) vs in-loop per-element MSE 0.0414 at none (0.3722/9) and 0.0779 at hard (0.7007/9)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
