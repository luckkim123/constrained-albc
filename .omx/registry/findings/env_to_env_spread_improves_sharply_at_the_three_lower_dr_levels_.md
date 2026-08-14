---
title: "Env-to-env spread improves sharply at the three lower DR levels and collapses at"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Env-to-env spread improves sharply at the three lower DR levels and collapses at

Env-to-env spread improves sharply at the three lower DR levels and collapses at hard, so the mean delta alone understates what changed.

[EVIDENCE: `summary.json` att_norm `ss_error_std` at none/soft/medium/hard — E-int 0.1975/0.1847/0.2440/1.2791, E-obs76 0.0551/0.0944/0.1304/2.7643, i.e. -72% at none and +116% at hard, CV 178% -> 271%]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
