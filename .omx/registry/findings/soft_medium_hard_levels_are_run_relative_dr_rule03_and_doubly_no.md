---
title: "`soft`/`medium`/`hard` levels are RUN-RELATIVE-DR (rule03) and doubly non-compar"
tags: ["auto-captured", "trpo_perflb200-moreiters_260715_195227"]
created: 2026-07-15T19:00:13.758977
updated: 2026-07-15T19:00:13.758977
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `soft`/`medium`/`hard` levels are RUN-RELATIVE-DR (rule03) and doubly non-compar

`soft`/`medium`/`hard` levels are RUN-RELATIVE-DR (rule03) and doubly non-comparable here: both runs' DORAEMON boxes differ from each other AND from any other prior run (P-A8 is fully uniform-ceiling on ALL 20 params, the reference was mid-expansion). The pattern is directionally the same as `none` (roll/pitch ss_error up, jitter mostly up, n_gt20 down) but magnitudes should not be treated as precise deltas.

[EVIDENCE: eval/static_260716_034515 vs eval/static_260715_141532 summary.json, soft/medium/hard levels]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
