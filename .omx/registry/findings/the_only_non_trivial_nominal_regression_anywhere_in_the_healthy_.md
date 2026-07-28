---
title: "The only non-trivial nominal regression anywhere in the healthy grid is yaw over"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The only non-trivial nominal regression anywhere in the healthy grid is yaw over

The only non-trivial nominal regression anywhere in the healthy grid is yaw overshoot at the two low-DR levels, which independently corroborates yaw as the axis paying for the composition — the same axis flagged by the m4-dead advantage and by the reward decomposition.

[EVIDENCE: exhaustive 68-cell scan — the largest worsened cell is `none` yaw `os_env_mean` 2.6942 -> 4.0353 pp (+1.3411, a 50 percent relative rise on a small base), then `soft` yaw `os_env_mean` +0.4495 pp; the remaining eleven are rise_time and yaw jitter/ss_error cells all under 0.03 in their own units; the 10 pp os_env_mean floor is untouched]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
