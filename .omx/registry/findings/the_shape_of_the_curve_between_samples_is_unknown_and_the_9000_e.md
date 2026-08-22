---
title: "The SHAPE of the curve between samples is unknown and the 9000 excursion is not "
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

# The SHAPE of the curve between samples is unknown and the 9000 excursion is not 

The SHAPE of the curve between samples is unknown and the 9000 excursion is not established as unique. Seven of 269 checkpoints were evaluated, at gaps of 1000-2500 iterations. The data cannot distinguish "one regression at 9000 followed by recovery" from "a trajectory that wobbles by ~0.15 deg at 50-checkpoint granularity, sampled once near a trough". Each individual comparison is sound — same seed, same 64 scenarios, paired — but the interpolation between them is not measured.

[EVIDENCE: 269 checkpoints on disk, 7 evaluated (5000/7500/9000/10000/11000/12500/13400)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
