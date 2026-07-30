---
title: "Yaw moves proportionally more than attitude under latent perturbation but remain"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Yaw moves proportionally more than attitude under latent perturbation but remain

Yaw moves proportionally more than attitude under latent perturbation but remains unjudgeable, re-confirming the profile's floor-unit defect on a second dataset.

[EVIDENCE: yaw ss_error at k=0 -> k=2 goes 0.0051 -> 0.0296 rad/s at none (5.8x) and 0.0086 -> 0.0624 at hard (7.3x), against a nominal floor of 0.1 rad/s that no observed value approaches]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
