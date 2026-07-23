---
title: "Env-to-env spread worsened even where the mean improved — pitch CV roughly doubl"
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

# Env-to-env spread worsened even where the mean improved — pitch CV roughly doubl

Env-to-env spread worsened even where the mean improved — pitch CV roughly doubles at every level (none 10 -> 21, soft 18 -> 43, medium 35 -> 92, hard 116 -> 197), so pitch's headline -47% DC gain is not uniformly distributed across envs.

[EVIDENCE: summary.json ss_error_std/ss_error per level; pitch none 0.0221/0.1028 = 21% vs anchor 0.0193/0.1946 = 10%]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
