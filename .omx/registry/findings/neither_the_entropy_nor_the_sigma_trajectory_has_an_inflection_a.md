---
title: "Neither the entropy nor the sigma trajectory has an inflection at the regression"
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

# Neither the entropy nor the sigma trajectory has an inflection at the regression

Neither the entropy nor the sigma trajectory has an inflection at the regression. Both continue their slow monotone decline straight through iteration 9000; whatever produced the eval excursion did not register as a change of learning regime.

[EVIDENCE: window table above — entropy -9.445 -> -9.497 -> -9.652 monotone, sigma 0.08091 -> 0.08027 -> 0.07829 monotone]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
