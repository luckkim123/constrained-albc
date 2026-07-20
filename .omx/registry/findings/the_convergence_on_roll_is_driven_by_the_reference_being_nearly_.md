---
title: "The convergence on roll is driven by the REFERENCE being nearly flat, not by P-B"
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

# The convergence on roll is driven by the REFERENCE being nearly flat, not by P-B

The convergence on roll is driven by the REFERENCE being nearly flat, not by P-B1 degrading unusually: the reference's roll ss_error barely moves from `none` to `hard` (1.08x) because it is already poor at `none`, while P-B1 has room to fall (2.77x). On pitch the ordering reverses — the reference degrades faster (1.95x vs 1.68x).

[EVIDENCE: `summary.json` ss_error none vs hard, degradation ratio = hard/none]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The convergence on roll is driven by the REFERENCE being nearly flat, not by P-B1 degrading unusually: the reference's roll ss_error barely moves from `none` to `hard` (1.08x) because it is already poor at `none`, while P-B1 has room to fall (2.77x). On pitch the ordering reverses — the reference degrades faster (1.95x vs 1.68x).

[EVIDENCE: `summary.json` ss_error none vs hard, degradation ratio = hard/none]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
