---
title: "The asymmetric critic splits cleanly: the value (reward) head fits 2.5x better o"
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

# The asymmetric critic splits cleanly: the value (reward) head fits 2.5x better o

The asymmetric critic splits cleanly: the value (reward) head fits 2.5x better on P-B1 while the cost head is essentially tied. The bias-EMA observation helps predict return, not cost.

[EVIDENCE: TB final scalars: `Loss/value_function` 0.3839 (P-B1) vs 0.9591 (REF); `Loss/cost_value` 0.8204 vs 0.7921]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The asymmetric critic splits cleanly: the value (reward) head fits 2.5x better on P-B1 while the cost head is essentially tied. The bias-EMA observation helps predict return, not cost.

[EVIDENCE: TB final scalars: `Loss/value_function` 0.3839 (P-B1) vs 0.9591 (REF); `Loss/cost_value` 0.8204 vs 0.7921]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
