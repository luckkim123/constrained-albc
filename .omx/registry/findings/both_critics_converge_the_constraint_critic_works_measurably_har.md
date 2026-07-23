---
title: "Both critics converge; the constraint critic works measurably harder on the corr"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T04:54:21.766685
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Both critics converge; the constraint critic works measurably harder on the corr

Both critics converge; the constraint critic works measurably harder on the corrected plant. | run | Loss/value_function | Loss/cost_value | |:--|--:|--:| | anchor s30 (new plant) | 0.44 | 0.77 | | anchor s31 (new plant) | 0.44 | 1.02 | | anchor s32 (new plant) | 0.55 | 0.99 | | Arm N (new plant) | 0.54 | 0.83 | | dgxseed30 (old plant) | 0.33 | 0.70 | | dgxseed31 (old plant) | 0.39 | 0.83 | | dgxseed32 (old plant) | 0.51 | 0.85 | New-plant `cost_value` mean 0.90 vs old-plant 0.79; `value_function` 0.49 vs 0.41.

[EVIDENCE: engine final-window means]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
