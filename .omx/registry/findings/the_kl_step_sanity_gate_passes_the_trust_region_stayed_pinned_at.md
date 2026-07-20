---
title: "The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configu"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configu

The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configured 0.12 for the whole run. The final-step value of 0.0000 is a sparse-logging artifact (the scalar is only written on the 250-iter curriculum steps), NOT a frozen curriculum.

[EVIDENCE: TB `DORAEMON/kl_step` on P-B1, full 5000-point trajectory: value = 0.1200 at every curriculum step sampled (iter 500/1000/1500/2000/2500/3000/3500/4000/4500), max = 0.1200, nonzero count = 18/5000; config `doraemon(kl_ub=0.12, performance_lb=250.0, step_interval=250)` at `constrained_albc/envs/main/config.py:544`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configured 0.12 for the whole run. The final-step value of 0.0000 is a sparse-logging artifact (the scalar is only written on the 250-iter curriculum steps), NOT a frozen curriculum.

[EVIDENCE: TB `DORAEMON/kl_step` on P-B1, full 5000-point trajectory: value = 0.1200 at every curriculum step sampled (iter 500/1000/1500/2000/2500/3000/3500/4000/4500), max = 0.1200, nonzero count = 18/5000; config `doraemon(kl_ub=0.12, performance_lb=250.0, step_interval=250)` at `constrained_albc/envs/main/config.py:544`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
