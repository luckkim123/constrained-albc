---
title: "e3's end-of-training DR is materially WIDER than baseline's on every curriculum "
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

# e3's end-of-training DR is materially WIDER than baseline's on every curriculum 

e3's end-of-training DR is materially WIDER than baseline's on every curriculum param, so e3's soft/medium/hard eval is a HARDER exam than baseline's — direct cross-run hard/soft/medium deltas are non-comparable (the e1 confound). Only `none` (fixed nominal physics, identical for both) is a fair cross-run point.

[EVIDENCE: TB DORAEMON/std/* — ocean_current 0.055→0.261 (4.7x), lin_damp 0.230→0.313, added_mass 0.158→0.219, payload_mass 0.487→0.571 (e3 wider on all)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e3_extend10k_260713_224822/analysis/diagnose-20260714-084409/report.md
