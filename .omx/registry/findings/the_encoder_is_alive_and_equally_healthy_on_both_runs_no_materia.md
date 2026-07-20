---
title: "The encoder is alive and equally healthy on both runs — no material difference f"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder is alive and equally healthy on both runs — no material difference f

The encoder is alive and equally healthy on both runs — no material difference from adding bias_ema to the observation (it is a small 3-dim addition to an already-72-89D input stream). z_std well above the 0.1 collapse floor on both; z stays within the softsign range (no clipping at +-0.95). Policy/encoder_grad_norm and Grad/enc_step are not broken out as separate scalars by the engine's tier-3 summary line for either run (the summary reports z-statistics only, no raw gradient-norm figure was printed) — this sub-metric is genuinely absent from the engine's printed output for both runs, not selectively omitted.

[EVIDENCE: engine deep output — Encoder/z_std (z_std), Encoder/z_min and Encoder/z_max (z_range bounds)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md

---

## Update (2026-07-16T07:19:42.517477)

The encoder is alive and equally healthy on both runs — no material difference from adding bias_ema to the observation (it is a small 3-dim addition to an already-72-89D input stream). z_std well above the 0.1 collapse floor on both; z stays within the softsign range (no clipping at +-0.95). Policy/encoder_grad_norm and Grad/enc_step are not broken out as separate scalars by the engine's tier-3 summary line for either run (the summary reports z-statistics only, no raw gradient-norm figure was printed) — this sub-metric is genuinely absent from the engine's printed output for both runs, not selectively omitted.

[EVIDENCE: engine deep output — Encoder/z_std (z_std), Encoder/z_min and Encoder/z_max (z_range bounds)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
