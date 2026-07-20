---
title: "The reward trajectory is a warmup-then-plateau shape with plateau onset at ~5% o"
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

# The reward trajectory is a warmup-then-plateau shape with plateau onset at ~5% o

The reward trajectory is a warmup-then-plateau shape with plateau onset at ~5% of training and two changepoints, matching extend8k's shape almost exactly — so the extra 3000 iterations are spent entirely inside the plateau.

[EVIDENCE: engine `[TRENDS]` — A1 phase warmup(1)->plateau(7), plateau since ~5%, cv=0.009, changepoints iter 503 and 5527; extend8k plateau since ~5%, changepoints 500 and 5531; ref5k plateau since ~10%, changepoints 360 and 3499]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
