---
title: "All ten constraints are satisfied with negative `Constraint/viol/*` at every row"
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

# All ten constraints are satisfied with negative `Constraint/viol/*` at every row

All ten constraints are satisfied with negative `Constraint/viol/*` at every row, and `thruster_util`'s margin widens from 6.14 to 7.76, so the deep-slack pattern this lineage records persists and no constraint was pushed toward its limit by the manipulation.

[EVIDENCE: engine `[TIER 2]` — binding `thruster_util` (0.806, m=7.76) vs anchor (0.846, m=6.14); deepest slack `attitude` (A2) / `arm_joint_vel` (anchor); all `viol` negative in both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
