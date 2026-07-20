---
title: "The load-bearing regression is roll TRANSIENT overshoot at low DR: the count of "
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:13:39.392281
updated: 2026-07-20T03:13:39.392281
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The load-bearing regression is roll TRANSIENT overshoot at low DR: the count of 

The load-bearing regression is roll TRANSIENT overshoot at low DR: the count of envs with roll peak > 20° explodes while roll steady-state falls (floor down, spike up). The eval plot shows roll overshoot ≈ 27% at `none`, above the 20% line.

[EVIDENCE: summary.json roll/n_gt20 (envs with peak > 20°); eval_attitude_summary.png Overshoot panel]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-115818/report.md
