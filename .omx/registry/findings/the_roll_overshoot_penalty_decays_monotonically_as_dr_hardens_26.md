---
title: "The roll overshoot penalty decays monotonically as DR hardens (+26 -> +13 -> +8 "
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

# The roll overshoot penalty decays monotonically as DR hardens (+26 -> +13 -> +8 

The roll overshoot penalty decays monotonically as DR hardens (+26 -> +13 -> +8 -> +4%), so the cost of the raised floor is largest exactly where the plant is nominal — added action noise is pure disturbance against a known plant and only becomes comparatively cheap once model uncertainty already dominates.

[EVIDENCE: summary.json roll os_env_mean across the four levels for both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
