---
title: "The covariate-shift multiplier at hard falls from 22.4x to 18.7x, but this compa"
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

# The covariate-shift multiplier at hard falls from 22.4x to 18.7x, but this compa

The covariate-shift multiplier at hard falls from 22.4x to 18.7x, but this comparison is not like-for-like and should not be read as a DAgger win.

[EVIDENCE: in-loop MSE divided by that arm's own iters-900-999 training loss_latent = 0.071386/0.003809 = 18.7x (B4b) vs 0.068040/0.003040 = 22.4x (A0); B4b's denominator is a beta-0.5 mixed-rollout loss, not an open-loop loss, so it is inflated by construction]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
