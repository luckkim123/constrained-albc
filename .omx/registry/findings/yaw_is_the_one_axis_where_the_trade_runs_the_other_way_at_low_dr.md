---
title: "Yaw is the one axis where the trade runs the other way at low DR — `os_env_mean`"
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

# Yaw is the one axis where the trade runs the other way at low DR — `os_env_mean`

Yaw is the one axis where the trade runs the other way at low DR — `os_env_mean` improves 59% at `none` and 48% at `soft` but regresses 37% at `hard`, while yaw `ss_error` worsens at every level (+26 to +61% on a small absolute base of 0.005-0.011 deg).

[EVIDENCE: summary.json none/yaw/os_env_mean 1.459 vs 3.593; hard/yaw/os_env_mean 4.382 vs 3.192; yaw ss_error 0.007->0.011 across levels]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
