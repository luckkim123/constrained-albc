---
title: "In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it cross"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

> **SCOPE 2026-08-13 -- this page is about ONE run: `trpo_sdobs76_x1_tailsplit_s30_260804_151400`.**
> It does NOT contradict `in_loop_aggregate_latent_r2_is_negative_at_all_four_dr_levels_th.md`,
> which measures a DIFFERENT run (`trpo_sdobs76_c3_gruselect_s30_260804_124951`). The two
> titles are near-identical and opposite, so a reader who greps "latent R2" will hit one
> headline and conclude the other is stale. Both are correct, for their own run.
> State the run or the record is unreadable.


# In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it cross

In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it crosses from negative to positive.

[EVIDENCE: computed from `latent_<level>.npz` in both evals as `1 - sumMSE/sumVar` over pooled (time x env) samples, 9 dims — R2 goes -1.7992 -> +0.0134 (none), -0.9436 -> -0.0466 (soft), -0.1315 -> +0.1838 (medium), -0.1044 -> +0.0645 (hard)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

In-loop aggregate latent R2 improves at ALL four DR levels, and at hard it crosses from negative to positive.

[EVIDENCE: computed from `latent_<level>.npz` in both evals as `1 - sumMSE/sumVar` over pooled (time x env) samples, 9 dims — R2 goes -1.7992 -> +0.0134 (none), -0.9436 -> -0.0466 (soft), -0.1315 -> +0.1838 (medium), -0.1044 -> +0.0645 (hard)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
