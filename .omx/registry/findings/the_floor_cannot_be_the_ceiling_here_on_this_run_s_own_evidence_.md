---
title: "The floor cannot be the ceiling here, on this run's own evidence: 5/8 dims were "
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

# The floor cannot be the ceiling here, on this run's own evidence: 5/8 dims were 

The floor cannot be the ceiling here, on this run's own evidence: 5/8 dims were already clamped at iteration 5000, yet the policy improved significantly from 5000 to 7500 (paired t = -3.89) and again from 9000 to 13400 (six consecutive significant steps). Improvement demonstrably occurs while the clamp is binding.

[EVIDENCE: paired tables above; sigma floored 5/8 at every readout from iter 2500 onward]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
