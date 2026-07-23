---
title: "Why it appears in A2 and nowhere else follows from the manipulation: a smaller s"
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

# Why it appears in A2 and nowhere else follows from the manipulation: a smaller s

Why it appears in A2 and nowhere else follows from the manipulation: a smaller sigma makes the importance ratio more sensitive to a given mean displacement, so the same line-search backtracking produces more extreme cost surrogates. This is a mechanism proposed from the code and the sigma data, not an isolated measurement.

[EVIDENCE: A2 `Policy/mean_noise_std` 0.07661 vs anchor 0.08610 with `Grad/actor_step` comparable (0.01510 vs 0.01570); `constraint_trpo.py:468-473` ratio-driven `cost_surrs`]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
