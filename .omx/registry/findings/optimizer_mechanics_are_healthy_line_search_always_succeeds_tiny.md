---
title: "Optimizer mechanics are healthy (line search always succeeds, tiny KL); policy e"
tags: ["auto-captured", "trpo_e2_biasobs_260713_173456"]
created: 2026-07-13T13:47:17.958008
updated: 2026-07-13T13:47:17.958008
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Optimizer mechanics are healthy (line search always succeeds, tiny KL); policy e

Optimizer mechanics are healthy (line search always succeeds, tiny KL); policy entropy is collapsed and noise_std floored, but this is the converged-policy signature shared by baseline and e1 — NOT an e1-style curriculum stall (DORAEMON is feasible here, §7).

[EVIDENCE: analyze_training.py TIER 1 entropy -9.11 (COLLAPSED, same regime as e1 -9.22), noise_std 0.09 (floored ~min_std 0.05), line_search_success 1.00; kl 3.2e-4; Policy/surrogate_loss improving, Grad/actor_step + Grad/sigma_step in trust region (line search never rejected); changepoint iter 3499 minor late reward/noise dip]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
