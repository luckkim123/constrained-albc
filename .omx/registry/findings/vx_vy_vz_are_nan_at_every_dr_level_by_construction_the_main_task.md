---
title: "`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `vx/vy/vz` are NaN at every DR level by construction — the main task is attitude

`vx/vy/vz` are NaN at every DR level by construction — the main task is attitude-only (no `lin_vel` tracking target), so the linear-velocity rows carry no information for this run.

[EVIDENCE: A1 enhanced summary, vx/vy/vz all `nan` across none/soft/medium/hard]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
