---
title: "The perturbation is large in latent terms even at k=1, which bounds how much of "
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

# The perturbation is large in latent terms even at k=1, which bounds how much of 

The perturbation is large in latent terms even at k=1, which bounds how much of the curve is extrapolation: at hard, k=1 injects a mean norm of 0.791 on a latent whose components are bounded in (-1,1).

[EVIDENCE: mean `||delta l_hat||` = 0.4983 / 0.4559 / 0.6415 / 0.7908 at k=1 for none/soft/medium/hard; the maximum possible norm of a 9-D vector in (-1,1)^9 is 3.0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
