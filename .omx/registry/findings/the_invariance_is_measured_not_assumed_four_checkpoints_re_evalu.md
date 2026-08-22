---
title: "The invariance is measured, not assumed. Four checkpoints re-evaluated two days "
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

# The invariance is measured, not assumed. Four checkpoints re-evaluated two days 

The invariance is measured, not assumed. Four checkpoints re-evaluated two days apart reproduce their `none` score to four decimals, while the same `model_5000` moved 1.2174 -> 1.3865 at `hard` because the box had grown between the two evals.

[EVIDENCE: `static_260806_201904` vs `static_260808_162023` (5000): none 0.5606/0.5606, hard 1.2174/1.3865; likewise 7500, 10000, 13400]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
