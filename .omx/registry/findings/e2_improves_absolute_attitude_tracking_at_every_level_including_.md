---
title: "e2 improves absolute attitude tracking at EVERY level including the matched `non"
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

# e2 improves absolute attitude tracking at EVERY level including the matched `non

e2 improves absolute attitude tracking at EVERY level including the matched `none`, roughly halving mean errors, and simultaneously LOWERS env-to-env dispersion (CV) at medium/hard — the observability change helped both the level and the spread.

[EVIDENCE: summary.json att_norm ss_error e2 0.249/0.229/0.291/0.398 vs bl 0.532/0.410/0.422/0.723; hard CV e2 1.40 vs bl 2.13; none jitter e2 0.099 vs bl 0.200]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
