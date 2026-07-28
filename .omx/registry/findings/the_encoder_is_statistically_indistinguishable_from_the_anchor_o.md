---
title: "The encoder is statistically indistinguishable from the anchor on every logged l"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder is statistically indistinguishable from the anchor on every logged l

The encoder is statistically indistinguishable from the anchor on every logged latent and gradient statistic, so the composed DR neither collapsed nor destabilised the latent, and no encoder-side explanation for the verdict is available or needed.

[EVIDENCE: `Encoder/z_std` 0.3976 vs 0.3965, `Encoder/z_min` -0.7214 vs -0.7168, `Encoder/z_max` 0.7300 vs 0.7421, `Policy/encoder_grad_norm` 0.0376 vs 0.0393, `Grad/enc_step` 0.00152 vs 0.00231; engine [TIER 1] z_std 0.39 with z_range [-0.71, 0.74]]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
