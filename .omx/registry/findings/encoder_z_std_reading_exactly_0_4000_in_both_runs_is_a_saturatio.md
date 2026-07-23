---
title: "`Encoder/z_std` reading exactly 0.4000 in both runs is a saturation signature of"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `Encoder/z_std` reading exactly 0.4000 in both runs is a saturation signature of

`Encoder/z_std` reading exactly 0.4000 in both runs is a saturation signature of the softsign output plus LayerNorm, not a per-run measurement; it should not be read as evidence of encoder health in either direction without a `encoder_tools.py sweep`.

[EVIDENCE: TB z_std identical to 4 decimals across two independently-trained runs; workspace rule that encoder verification requires a per-dimension z sweep]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
