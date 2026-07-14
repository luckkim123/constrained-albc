---
title: "The encoder latent stayed active and non-collapsed through the extension — its d"
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

# The encoder latent stayed active and non-collapsed through the extension — its d

The encoder latent stayed active and non-collapsed through the extension — its degradation is not the regression mechanism: z_std 0.37 and the latent spans the full softsign range, matching baseline.

[EVIDENCE: engine TIER1 e3 — Encoder/z_std 0.37, Encoder/z_min/Encoder/z_max span [−0.74, 0.73] (softsign full range), Policy/encoder_grad_norm active; baseline Encoder/z_std 0.387, range [−0.735, 0.737]]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
