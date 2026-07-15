---
title: "A NEW regime changepoint was detected at iter 5295 (past the original run's 4999"
tags: ["auto-captured", "trpo_perflb200-moreiters_260715_195227"]
created: 2026-07-15T19:00:13.758977
updated: 2026-07-15T19:00:13.758977
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# A NEW regime changepoint was detected at iter 5295 (past the original run's 4999

A NEW regime changepoint was detected at iter 5295 (past the original run's 4999 endpoint) — `mean_reward(down), success_rate(down), z_std(up)` — flagging the exact point where continued training started trading return for DR expansion. This is genuinely new information the 5000-iter run could not have surfaced.

[EVIDENCE: engine deep output, changepoints line, P-A8 run]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
