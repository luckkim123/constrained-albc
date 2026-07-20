---
title: "Therefore neither `performance_lb` nor `kl_ub` was the limiting factor on this c"
tags: ["auto-captured", "trpo_biasema_extend8k_260716_162849"]
created: 2026-07-20T03:53:52.371991
updated: 2026-07-20T03:53:52.371991
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Therefore neither `performance_lb` nor `kl_ub` was the limiting factor on this c

Therefore neither `performance_lb` nor `kl_ub` was the limiting factor on this config. The curriculum was time-limited only up to iter 7000 and ceiling-limited afterwards, and the feasibility gate never bound either — success_rate ended 0.789, far above `alpha=0.5`. Lowering `performance_lb` or raising `kl_ub` cannot make this exam harder; the box is exhausted.

[EVIDENCE: train/params/env.yaml performance_lb=250.0, alpha=0.5, kl_ub=0.12, step_interval=250; TB DORAEMON/success_rate]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_extend8k_260716_162849/analysis/diagnose-20260720-125306/report.md
