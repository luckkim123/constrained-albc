---
title: "Yaw-rate is essentially solved on all runs/levels (ss_error <= 0.007, well insid"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-14T16:41:28.339995
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Yaw-rate is essentially solved on all runs/levels (ss_error <= 0.007, well insid

Yaw-rate is essentially solved on all runs/levels (ss_error <= 0.007, well inside the 0.5 threshold); no heavy-tail concern (yaw peak counts are a threshold-crossing artifact, not a failure).

[EVIDENCE: summary.json yaw ss_error: void none 0.001 -> hard 0.005 -> ood 0.005; MATCHED none 0.001 -> hard 0.006 -> ood 0.005; FULL hard 0.007]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
