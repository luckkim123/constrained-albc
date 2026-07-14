---
title: "At `none`, e3's per-env median roll error is 2.80° vs baseline 0.18° (15.5x). Th"
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

# At `none`, e3's per-env median roll error is 2.80° vs baseline 0.18° (15.5x). Th

At `none`, e3's per-env median roll error is 2.80° vs baseline 0.18° (15.5x). The max/median collapses to 1.2x — NOT because the tail is healthy but because ALL 64 envs are uniformly bad (~2.8°): a uniform DC-bias at nominal physics, the opposite of a shrunk tail.

[EVIDENCE: data_none.npz per-env median |roll| — e3 median 2.797° / max 3.269° (max/median 1.2x), baseline median 0.180° / max 1.031°]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
