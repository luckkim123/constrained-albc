---
title: "The TRPO optimiser behaved identically to the anchor — the trust region never fa"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The TRPO optimiser behaved identically to the anchor — the trust region never fa

The TRPO optimiser behaved identically to the anchor — the trust region never failed a line search and the KL step stayed pinned at target — so the verdict is not confounded by an optimisation difference.

[EVIDENCE: `Policy/line_search_success` 1.00 for both runs; the trust-region target is the configured `max_kl` = 0.005 (engine [CONFIG]) and the engine measured [TIER 3] `kl` reads 0.01 anchor vs 0.00 E-int; `Policy/surrogate_loss` -0.0999 vs -0.1031, `Grad/actor_step` 0.0205 vs 0.0230, `Grad/sigma_step` 0.00064 vs 0.00088 (last-20-step means)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
