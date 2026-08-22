---
title: "`model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 750"
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 750

`model_13400` is the only checkpoint with zero OOD failures (0/64 vs 1/64 at 7500 and 10000, 3/64 at 5000), but 0-vs-1 of 64 is not a distinguishable difference and must not be quoted as a robustness win.

[EVIDENCE: `terminated.any(axis=0)` per env; Fisher exact 0/64 vs 1/64 gives p = 1.0]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
