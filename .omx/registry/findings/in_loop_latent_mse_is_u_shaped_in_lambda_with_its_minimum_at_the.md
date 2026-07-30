---
title: "In-loop latent MSE is U-shaped in lambda with its minimum at the campaign's defa"
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

# In-loop latent MSE is U-shaped in lambda with its minimum at the campaign's defa

In-loop latent MSE is U-shaped in lambda with its minimum at the campaign's default at none, soft and medium, and completely flat in lambda at hard — so the default weight is a local optimum of the quantity it is supposed to control, and at hard the weight is irrelevant.

[EVIDENCE: table above; at none the three values are 0.0844 / 0.0330 / 0.0445 for lambda 0 / 1 / 4, at hard 0.070786 / 0.068041 / 0.067976, a spread of 4% across a 4x range of lambda]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
