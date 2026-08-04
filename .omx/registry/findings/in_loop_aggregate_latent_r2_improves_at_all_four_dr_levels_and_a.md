---
title: "In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it cross"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-04T07:04:05.217247
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it cross

In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it crosses from negative to positive.

[EVIDENCE: computed from `latent_<level>.npz` in both evals as `1 - sumMSE/sumVar` over pooled (time x env) samples, 9 dims — R2 goes -1.7992 -> +0.0134 (none), -0.9436 -> -0.0466 (soft), -0.1315 -> +0.1838 (medium), -0.1044 -> +0.0645 (hard)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
