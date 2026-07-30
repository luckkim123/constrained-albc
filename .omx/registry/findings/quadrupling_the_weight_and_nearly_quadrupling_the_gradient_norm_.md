---
title: "Quadrupling the weight and nearly quadrupling the gradient norm improves the lat"
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

# Quadrupling the weight and nearly quadrupling the gradient norm improves the lat

Quadrupling the weight and nearly quadrupling the gradient norm improves the latent loss by 1.5%, so the open-loop latent residual is at a floor the optimizer cannot push through and is not weight-limited.

[EVIDENCE: `loss_latent` 0.003040 -> 0.002993 (-1.5%) for a 4x weight and a 3.72x `grad_norm` (0.023759 -> 0.088345)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
