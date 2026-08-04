---
title: "The train-to-in-loop latent MSE gap — the campaign's covariate-shift measure — n"
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

# The train-to-in-loop latent MSE gap — the campaign's covariate-shift measure — n

The train-to-in-loop latent MSE gap — the campaign's covariate-shift measure — narrows at every DR level, and the narrowing is strongest where DR is weakest.

[EVIDENCE: per-dim mean in-loop MSE (`sumMSE/9` from `latent_<level>.npz`) divided by the same run's trailing-100 training `student/loss_latent` — 9.7x -> 3.2x (none), 9.4x -> 4.7x (soft), 9.8x -> 6.7x (medium), 17.4x -> 14.5x (hard)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
