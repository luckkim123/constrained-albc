---
title: "The latent statistics are unchanged (z_std/z_min/z_max all within 1.5%), so the "
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The latent statistics are unchanged (z_std/z_min/z_max all within 1.5%), so the 

The latent statistics are unchanged (z_std/z_min/z_max all within 1.5%), so the encoder output distribution is healthy — the failure is upstream, in what the encoder was given, not in how it encodes.

[EVIDENCE: TB last-200-iter means; z_sweep active-dim counts show no newly-dead parameter]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
