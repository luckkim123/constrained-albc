---
title: "The corrected metric is R2, not the env-variance ratio: for a calibrated MSE-opt"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T05:08:41.653435
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The corrected metric is R2, not the env-variance ratio: for a calibrated MSE-opt

The corrected metric is R2, not the env-variance ratio: for a calibrated MSE-optimal predictor `Var(l_hat)/Var(l_true) = 1 - MSE/Var = R2`, so a low ratio is REQUIRED of an honest weak predictor and a target of 1 is wrong.

[EVIDENCE: campaign wiki `latent_dim_d4_collapses...` CORRECTION 2026-07-29, derived from the law of total variance; reproduced here as R2 = 1 - MSE_d/Var_total_d per dim from latent_<level>.npz]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

The corrected metric is R2, not the env-variance ratio: for a calibrated MSE-optimal predictor `Var(l_hat)/Var(l_true) = 1 - MSE/Var = R2`, so a low ratio is REQUIRED of an honest weak predictor and a target of 1 is wrong.

[EVIDENCE: campaign wiki `latent_dim_d4_collapses...` CORRECTION 2026-07-29, derived from the law of total variance; reproduced here as R2 = 1 - MSE_d/Var_total_d per dim from latent_<level>.npz]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
