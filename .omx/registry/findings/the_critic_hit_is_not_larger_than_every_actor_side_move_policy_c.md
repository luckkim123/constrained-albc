---
title: "The critic hit is NOT larger than every actor-side move — `Policy/clip_fraction`"
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

# The critic hit is NOT larger than every actor-side move — `Policy/clip_fraction`

The critic hit is NOT larger than every actor-side move — `Policy/clip_fraction` (+94.9%) exceeds it and `Grad/enc_step` (-39.8%) ties it. The honest reading is a coupled degradation across critic, encoder gradient flow and actor saturation, not a critic-only lesion.

[EVIDENCE: TB last-200-iter means — Loss/value_function +39.7%, Policy/clip_fraction +94.9%, Grad/enc_step -39.8%]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
