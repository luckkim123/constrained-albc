---
title: "Even on e3's OWN (harder) hard exam the tail is WORSE than baseline's, not bette"
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

# Even on e3's OWN (harder) hard exam the tail is WORSE than baseline's, not bette

Even on e3's OWN (harder) hard exam the tail is WORSE than baseline's, not better: max/median 41.6x vs 23.2x, worst env 13.8° vs 4.8°, top-6/64 53% vs 49% — so budget did not shrink the tail on any basis, fair or confounded.

[EVIDENCE: data_hard.npz per-env median |roll| — e3 max/median 41.6x, max 13.798°, top-6 53%; baseline 23.2x, 4.802°, 49%]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
