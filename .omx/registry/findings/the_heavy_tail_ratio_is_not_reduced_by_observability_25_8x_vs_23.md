---
title: "The heavy-tail RATIO is NOT reduced by observability (25.8x vs 23.2x, top-6 45.8"
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

# The heavy-tail RATIO is NOT reduced by observability (25.8x vs 23.2x, top-6 45.8

The heavy-tail RATIO is NOT reduced by observability (25.8x vs 23.2x, top-6 45.8% vs 48.7%) — H1's tail thresholds (<=12x, <=38%) are missed and H2's (>=18x, >=45%) hold, so the DC-bias tail is authority-limited, not observability-limited.

[EVIDENCE: data_hard.npz per-env median|error_roll| max/median e2 25.8 vs bl 23.2, top-6 45.8% vs 48.7%; absolute max e2 3.785 < bl 4.802 and median e2 0.147 < bl 0.207 (the ratio is inflated by a smaller median, per wiki teacher_hard_dr_cv_explodes DC-bias-dispersion lens)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
