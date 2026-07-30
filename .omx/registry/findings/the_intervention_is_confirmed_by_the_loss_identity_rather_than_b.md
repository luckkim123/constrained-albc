---
title: "The intervention is confirmed by the loss identity rather than by a config value"
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

# The intervention is confirmed by the loss identity rather than by a config value

The intervention is confirmed by the loss identity rather than by a config value: B1b's `loss_total` equals `loss_action + 4 * loss_latent` to five decimals.

[EVIDENCE: 0.000135 + 4 x 0.002993 = 0.012107 against the logged `loss_total` mean of 0.012108; A0's identity with coefficient 1 is 0.000131 + 0.003040 = 0.003171, matching its logged 0.003171]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
