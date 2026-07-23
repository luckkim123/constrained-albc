---
title: "The strong negative roll/yaw coupling at `none` (rho -0.56 for A3, -0.95 for the"
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

# The strong negative roll/yaw coupling at `none` (rho -0.56 for A3, -0.95 for the

The strong negative roll/yaw coupling at `none` (rho -0.56 for A3, -0.95 for the anchor) means envs that do well on roll do badly on yaw and vice versa — a real axis trade-off in this policy family, not an A3 artifact, though A3 weakens it.

[EVIDENCE: `analyze.py eval_dr` AXIS DECORRELATION blocks, roll_yaw column across all four levels]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
