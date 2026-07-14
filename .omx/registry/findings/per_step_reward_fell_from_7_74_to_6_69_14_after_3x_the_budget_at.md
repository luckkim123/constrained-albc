---
title: "Per-step reward fell from 7.74 to 6.69 (−14%) after 3x the budget: attitude-trac"
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

# Per-step reward fell from 7.74 to 6.69 (−14%) after 3x the budget: attitude-trac

Per-step reward fell from 7.74 to 6.69 (−14%) after 3x the budget: attitude-tracking reward dropped (6.22→5.35) while the bias penalty grew (−0.025→−0.04) — the decomposition confirms the extension degraded tracking and increased steady-state bias, consistent with §1–§2.

[EVIDENCE: engine TIER3 Rewards e3 total 6.69, att_rp 5.35, bias −0.04 vs baseline total 7.74, att_rp 6.22, bias −0.025]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
