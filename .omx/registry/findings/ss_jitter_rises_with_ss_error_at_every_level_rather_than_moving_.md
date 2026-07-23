---
title: "`ss_jitter` rises with `ss_error` at every level rather than moving against it, "
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

# `ss_jitter` rises with `ss_error` at every level rather than moving against it, 

`ss_jitter` rises with `ss_error` at every level rather than moving against it, so the degradation is not a policy-oscillation artifact sitting on top of an unchanged DC offset — both the AC and DC components worsen together.

[EVIDENCE: `summary.json` roll `ss_jitter` A2 vs anchor — none 0.113/0.094, soft 0.108/0.122, medium 0.145/0.141, hard 0.487/0.206]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
