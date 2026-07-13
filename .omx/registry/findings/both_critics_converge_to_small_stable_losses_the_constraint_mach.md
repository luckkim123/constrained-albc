---
title: "Both critics converge to small stable losses — the constraint machinery (cost cr"
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

# Both critics converge to small stable losses — the constraint machinery (cost cr

Both critics converge to small stable losses — the constraint machinery (cost critic) is well-conditioned, so IPO/ConstraintTRPO is not the failure locus.

[EVIDENCE: analyze_training.py TIER 3 Losses Loss/value_function 1.02, Loss/cost_value 0.56, kl 0.01]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
