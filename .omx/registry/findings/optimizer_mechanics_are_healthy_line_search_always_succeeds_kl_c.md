---
title: "Optimizer mechanics are healthy (line search always succeeds, KL controlled) but"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Optimizer mechanics are healthy (line search always succeeds, KL controlled) but

Optimizer mechanics are healthy (line search always succeeds, KL controlled) but policy entropy has COLLAPSED and noise_std floored — exploration is dead, consistent with a curriculum frozen narrow (§7) leaving little to explore.

[EVIDENCE: analyze_training.py TIER 1 entropy -9.22 (COLLAPSED), noise_std 0.08 (LOW), line_search_success 1.00, kl 0.01, Policy/surrogate_loss improving, Grad/actor_step + Grad/sigma_step in trust region]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
