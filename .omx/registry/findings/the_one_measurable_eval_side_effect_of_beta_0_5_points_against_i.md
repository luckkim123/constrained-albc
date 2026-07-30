---
title: "The one measurable eval-side effect of beta 0.5 points against it: absolute in-l"
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

# The one measurable eval-side effect of beta 0.5 points against it: absolute in-l

The one measurable eval-side effect of beta 0.5 points against it: absolute in-loop latent MSE is worse than A0 at every DR level, by margins far larger than anything in the control metrics.

[EVIDENCE: closed-loop overall_mse recomputed from latent_<level>.npz reproducing eval.py:_summarize_latent (eval.py:982-1000) = 0.046257/0.040382/0.045696/0.071386 (B4b) vs 0.032975/0.030741/0.040636/0.068040 (A0)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
