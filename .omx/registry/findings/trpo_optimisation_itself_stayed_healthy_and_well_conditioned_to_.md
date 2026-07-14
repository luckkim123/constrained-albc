---
title: "TRPO optimisation itself stayed healthy and well-conditioned to the end — the re"
tags: ["auto-captured", "trpo_e3_extend10k_260713_224822"]
created: 2026-07-13T23:52:53.410508
updated: 2026-07-13T23:52:53.410508
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# TRPO optimisation itself stayed healthy and well-conditioned to the end — the re

TRPO optimisation itself stayed healthy and well-conditioned to the end — the regression is a curriculum/target-shaping effect, not an optimiser failure: line-search 100%, KL on target, entropy collapsed as expected at convergence.

[EVIDENCE: engine TIER1 e3 — line_search_success 1.00, kl 0.01 (Loss/kl), entropy −8.11 (collapsed, expected), noise_std 0.10; baseline entropy −7.62]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
