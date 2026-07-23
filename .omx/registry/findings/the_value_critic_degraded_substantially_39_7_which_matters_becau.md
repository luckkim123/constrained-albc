---
title: "The value critic degraded substantially (+39.7%), which matters because the crit"
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

# The value critic degraded substantially (+39.7%), which matters because the crit

The value critic degraded substantially (+39.7%), which matters because the critic is the ASYMMETRIC consumer of p_t — it is the component that actually reads the removed dims. Return prediction got harder, and a noisier advantage signal is a sufficient mechanism for the actor's behavioural shift.

[EVIDENCE: TB last-200-iter means Loss/value_function 0.5388 vs 0.3857]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
