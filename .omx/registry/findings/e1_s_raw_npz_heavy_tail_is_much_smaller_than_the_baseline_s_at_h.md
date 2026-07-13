---
title: "e1's raw-npz heavy-tail is much smaller than the baseline's at hard and ood, but"
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

# e1's raw-npz heavy-tail is much smaller than the baseline's at hard and ood, but

e1's raw-npz heavy-tail is much smaller than the baseline's at hard and ood, but this is the §0 confound (e1's exam is narrower), NOT a real tail fix — the causal read "latency shrank the tail" is REJECTED.

[EVIDENCE: data_hard.npz per-env median|error_roll| max/median e1 5.5 vs bl 23.2, top-6 26% vs 49%; but eval distributions differ per run (dr_config.py:206 run-relative), so the numbers are not comparable]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
