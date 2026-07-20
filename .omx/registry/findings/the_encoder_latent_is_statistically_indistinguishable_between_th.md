---
title: "The encoder latent is statistically indistinguishable between the two runs — spr"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder latent is statistically indistinguishable between the two runs — spr

The encoder latent is statistically indistinguishable between the two runs — spread and both range ends match to within ~3%. The encoder is NOT the differentiator; whatever P-B1 changed, it did not change the latent's gross statistics.

[EVIDENCE: TB final scalars: `Encoder/z_std` 0.3970 (P-B1) vs 0.4100 (REF); `Encoder/z_min` -0.7199 vs -0.7273; `Encoder/z_max` 0.7369 vs 0.7269]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The encoder latent is statistically indistinguishable between the two runs — spread and both range ends match to within ~3%. The encoder is NOT the differentiator; whatever P-B1 changed, it did not change the latent's gross statistics.

[EVIDENCE: TB final scalars: `Encoder/z_std` 0.3970 (P-B1) vs 0.4100 (REF); `Encoder/z_min` -0.7199 vs -0.7273; `Encoder/z_max` 0.7369 vs 0.7269]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
