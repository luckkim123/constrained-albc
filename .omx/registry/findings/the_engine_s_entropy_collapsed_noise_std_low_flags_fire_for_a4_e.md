---
title: "The engine's `entropy COLLAPSED / noise_std LOW` flags fire for A4 exactly as fo"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The engine's `entropy COLLAPSED / noise_std LOW` flags fire for A4 exactly as fo

The engine's `entropy COLLAPSED / noise_std LOW` flags fire for A4 exactly as for the anchor and A3, confirming again that this diagnosis is a constant of the config family and carries no per-run information.

[EVIDENCE: `analyze_training.py --tier 3 --deep` TIER 1, A4 entropy -9.00 / noise 0.09 vs anchor -9.07 / 0.09]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
