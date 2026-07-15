---
title: "The cost of the fix: the typical-env roll floor ROSE. The distribution shifted f"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-14T16:41:28.339995
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The cost of the fix: the typical-env roll floor ROSE. The distribution shifted f

The cost of the fix: the typical-env roll floor ROSE. The distribution shifted from "steep tail over a low body" to "compressed tail over a raised body" — visible as the void curve (plot 1) spiking to 5deg at rank 1 then dropping BELOW the post-TAM curves for ranks ~8-64. Void hard median 0.199deg -> MATCHED 0.440deg; void none median 0.174deg -> MATCHED 0.548deg. The per-env mean rose too (hard +46%, none +133%), confirming the whole body — not just the median — shifted up.

[EVIDENCE: per-env roll ss code-exec (per_env_roll.py, data_none.npz/data_hard.npz): median void hard 0.199 -> MATCHED 0.440 (+121%), void none 0.174 -> MATCHED 0.548; mean void hard 0.389 -> MATCHED 0.568 (+46%), void none 0.229 -> MATCHED 0.534 (+133%)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
