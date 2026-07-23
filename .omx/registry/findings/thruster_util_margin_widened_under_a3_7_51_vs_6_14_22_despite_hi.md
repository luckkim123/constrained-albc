---
title: "`thruster_util` margin WIDENED under A3 (7.51 vs 6.14, +22%) despite higher acti"
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

# `thruster_util` margin WIDENED under A3 (7.51 vs 6.14, +22%) despite higher acti

`thruster_util` margin WIDENED under A3 (7.51 vs 6.14, +22%) despite higher action noise, so the raised sigma floor did not push the actuators closer to saturation — the extra dither is absorbed well inside the thruster budget.

[EVIDENCE: `analyze_training.py` TIER 2, thruster_util m=7.51 (A3) vs m=6.14 (anchor)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
