---
title: "The anchor's `hard` advantage in mean AttErr is partly carried by a single patho"
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

# The anchor's `hard` advantage in mean AttErr is partly carried by a single patho

The anchor's `hard` advantage in mean AttErr is partly carried by a single pathological env — its roll ss_max of 3.55 against a ss_mean of 0.182 is a ~20x outlier, which A3 does not have (0.56 vs 0.157, ~3.6x). The near-tie in `hard` att_norm ss_error (-1.5%) therefore understates A3's robustness at the extreme.

[EVIDENCE: `analyze.py eval_dr` HEAVY-TAIL HARD block for both runs]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
