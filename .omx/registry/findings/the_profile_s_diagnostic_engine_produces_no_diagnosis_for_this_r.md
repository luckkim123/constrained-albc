---
title: "The profile's diagnostic engine produces no diagnosis for this run either, so no"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The profile's diagnostic engine produces no diagnosis for this run either, so no

The profile's diagnostic engine produces no diagnosis for this run either, so no changepoint, plateau or regime evidence is available for B1b and none is claimed.

[EVIDENCE: `analyze_training.py <b1b run> --tier 3 --deep` prints "[TIER 1] Core Health / STATUS: HEALTHY / iters=0 last_step=0" plus a [TARGETS] line resolving iter/grad_norm/loss_action/time_collect/time_train, with no [DIAGNOSIS], changepoint, plateau or regime output; `ruptures` and `hmmlearn` are additionally unavailable]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
