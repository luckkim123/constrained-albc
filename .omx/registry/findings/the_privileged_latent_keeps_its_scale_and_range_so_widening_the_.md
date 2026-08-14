---
title: "The privileged latent keeps its scale and range, so widening the policy observat"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The privileged latent keeps its scale and range, so widening the policy observat

The privileged latent keeps its scale and range, so widening the policy observation does not collapse or inflate the encoder.

[EVIDENCE: TB final-50 means — `Encoder/z_std` 0.39330 -> 0.38228 (-2.8%), `Encoder/z_min` and `Encoder/z_max` matching to within 0.019]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
