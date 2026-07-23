---
title: "Policy updates were substantially larger under the raised floor (actor step +33."
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

# Policy updates were substantially larger under the raised floor (actor step +33.

Policy updates were substantially larger under the raised floor (actor step +33.3%, sigma step +89.9%, clip fraction +15.8%) — the floor does not merely clamp sigma, it changes the step geometry the whole run.

[EVIDENCE: TB last-200-iter means for Grad/actor_step, Grad/sigma_step, Policy/clip_fraction]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
