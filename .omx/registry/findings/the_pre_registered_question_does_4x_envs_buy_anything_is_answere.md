---
title: "The pre-registered question — does 4x envs buy anything — is answered negatively"
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

# The pre-registered question — does 4x envs buy anything — is answered negatively

The pre-registered question — does 4x envs buy anything — is answered negatively on both axes. Saturation moved by 250 iterations out of ~7000, and the best checkpoint on the invariant exam matches the 4096-env lineage to within 2%: this run's 0.4968 deg (model_7500) against 0.5070 for `teacher_iter_budget/trpo_iterbudget_s30_260805_012813` (4096 envs, 5000 iterations) and 0.5067 for `teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136` (4096 envs, 5000 iterations). All three are seed 30 on the current plant. This run spent roughly 11x the compute (4x envs, 2.7x iterations) to land in the same place.

[EVIDENCE: `none` att_norm ss_error from each run's own eval summary.json — 0.4968 / 0.5070 / 0.5067; num_envs and max_iterations read from each manifest.json]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
