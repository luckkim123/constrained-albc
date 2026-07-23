---
title: "`rp_rate` also moved toward binding (margin 5.91 -> 4.88, J_C/d_k 0.409 -> 0.512"
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

# `rp_rate` also moved toward binding (margin 5.91 -> 4.88, J_C/d_k 0.409 -> 0.512

`rp_rate` also moved toward binding (margin 5.91 -> 4.88, J_C/d_k 0.409 -> 0.512), the roll/pitch rate constraint — the same axes whose jitter exploded at `hard`. The constraint set independently corroborates the oscillation seen in the eval.

[EVIDENCE: `analyze_training.py` TIER 2 rp_rate row; summary.json hard roll/pitch ss_jitter +225%/+414%]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
