---
title: "The fault_severity curriculum now drives real faults and lands between E-int and"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The fault_severity curriculum now drives real faults and lands between E-int and

The fault_severity curriculum now drives real faults and lands between E-int and the fault-free run, which is what a restored plant with a slightly easier observation predicts.

[EVIDENCE: `DORAEMON/mean/fault_severity` 0.07704 / 0.10090 / 0.11291 and `DORAEMON/success_rate` 0.81044 / 0.85807 / 0.91889 across E-int, this run, attempt 1, with `albc_env.py:1652` gating fault sampling on `cfg.fault.enable` which this run's recorded config sets true]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
