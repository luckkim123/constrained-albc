---
title: "The profile's diagnostic engine produces no diagnosis for a distillation run and"
tags: ["auto-captured", "trpo_sdeint_b4b_beta05_s30_260729_153436"]
created: 2026-07-29T07:25:05.571851
updated: 2026-07-29T07:25:05.571851
sources: ["/workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The profile's diagnostic engine produces no diagnosis for a distillation run and

The profile's diagnostic engine produces no diagnosis for a distillation run and cannot be cited for time-series structure here.

[EVIDENCE: analyze_training.py --tier 3 --deep on the B4b run returns "[TIER 1] Core Health STATUS: HEALTHY iters=0 last_step=0", resolves only iter/grad_norm/loss_action/time_collect/time_train as auto targets, emits no [DIAGNOSIS], changepoint, plateau or regime line, and reports both ruptures and hmmlearn unavailable under [DEEP]]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
