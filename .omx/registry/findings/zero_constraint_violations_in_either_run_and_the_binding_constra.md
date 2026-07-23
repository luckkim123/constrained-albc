---
title: "Zero constraint violations in either run and the binding constraint is unchanged"
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

# Zero constraint violations in either run and the binding constraint is unchanged

Zero constraint violations in either run and the binding constraint is unchanged — `thruster_util` remains the single active constraint (J_C/d_k 0.812 vs 0.846) with every other constraint deeply slack.

[EVIDENCE: `analyze_training.py` TIER 2 block for both runs; all `viol` entries negative (margin not breached)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
