---
title: "P-A8's total decomposed reward is lower than the reference's (5.40 vs 7.35), dri"
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

# P-A8's total decomposed reward is lower than the reference's (5.40 vs 7.35), dri

P-A8's total decomposed reward is lower than the reference's (5.40 vs 7.35), driven mainly by a lower `att_rp` term — consistent with the degraded `none`-level tracking precision above, and expected given training return is measured on the (now much harder) DORAEMON-sampled DR mix, not the fair `none` point the eval isolates separately.

[EVIDENCE: engine deep output, both runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
