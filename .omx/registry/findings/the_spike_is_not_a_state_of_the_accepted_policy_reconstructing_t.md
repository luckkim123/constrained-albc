---
title: "The spike is NOT a state of the accepted policy: reconstructing the barrier from"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The spike is NOT a state of the accepted policy: reconstructing the barrier from

The spike is NOT a state of the accepted policy: reconstructing the barrier from the ten post-update margins logged at iter 4438 gives exactly the neighbouring value, and the smallest margin at that iteration is a healthy `cumul_yaw` 0.9188.

[EVIDENCE: `-(sum ln margin_k)/barrier_t` over the 10 logged `Constraint/margin/*` at iter 4438 = -0.1275, matching the neighbours (iter 4437 -0.1268, iter 4439 -0.1305) and not the logged +0.1402; `Policy/line_search_success` = 1.0 at iter 4438]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
