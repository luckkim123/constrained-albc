---
title: "`Encoder/z_mean` -42.3% is a near-zero-base artifact (both means ~-0.02 to -0.03"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-22T01:58:11.799085
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `Encoder/z_mean` -42.3% is a near-zero-base artifact (both means ~-0.02 to -0.03

`Encoder/z_mean` -42.3% is a near-zero-base artifact (both means ~-0.02 to -0.03, well inside the +/-0.73 z-range), not a distribution shift; z_std moving only +3.7% confirms the latent distribution is stable.

[EVIDENCE: TB Encoder/z_mean -0.0289 vs -0.0203 against z_std 0.4147 vs 0.4000, z_range +/-0.73]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
