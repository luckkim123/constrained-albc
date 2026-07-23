---
title: "The two tail metrics disagree, and they disagree because they measure different "
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

# The two tail metrics disagree, and they disagree because they measure different 

The two tail metrics disagree, and they disagree because they measure different things: the COUNT-based tail (`n_gt20`, envs over 20% overshoot) is worse for A3 at EVERY DR level including `hard` (8.67 -> 13.67), while the MAGNITUDE-based tail (single worst env, `peak_max`) reverses only at `hard` (roll 2.12 vs the anchor's 8.70). A3 therefore has more mid-tail envs everywhere but no extreme outlier at `hard`; neither metric alone describes the tail.

[EVIDENCE: summary.json `n_gt20` all four levels — roll 4.33->38.00 (none), 3.33->16.00 (soft), 6.67->10.67 (medium), 8.67->13.67 (hard); `analyze.py eval_dr` HEAVY-TAIL block, roll hard ss_max 0.56 vs 3.55 and peak_max 2.12 vs 8.70]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
