---
title: "The engine flags `entropy COLLAPSED / noise_std LOW` for BOTH runs, so that diag"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The engine flags `entropy COLLAPSED / noise_std LOW` for BOTH runs, so that diag

The engine flags `entropy COLLAPSED / noise_std LOW` for BOTH runs, so that diagnosis is a fixed property of this config family (per-dim floors + 0.003 entropy coef) and does not discriminate A3 from the anchor; A3 is in fact the less-collapsed of the two.

[EVIDENCE: `analyze_training.py --tier 3 --deep` TIER 1 block, A3 entropy -7.22 / noise 0.10 vs anchor -9.07 / 0.09, both tagged COLLAPSED/LOW]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
