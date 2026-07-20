---
title: "The gradient steps confirm the collapse mechanically: P-B1's `Grad/sigma_step` i"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The gradient steps confirm the collapse mechanically: P-B1's `Grad/sigma_step` i

The gradient steps confirm the collapse mechanically: P-B1's `Grad/sigma_step` is 4x smaller than the reference's, i.e. the std head has all but stopped moving, while the actor step remains comparable.

[EVIDENCE: TB final scalars: `Grad/actor_step` 0.0157 (P-B1) vs 0.0190 (REF); `Grad/sigma_step` 0.0002 vs 0.0008]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The gradient steps confirm the collapse mechanically: P-B1's `Grad/sigma_step` is 4x smaller than the reference's, i.e. the std head has all but stopped moving, while the actor step remains comparable.

[EVIDENCE: TB final scalars: `Grad/actor_step` 0.0157 (P-B1) vs 0.0190 (REF); `Grad/sigma_step` 0.0002 vs 0.0008]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
