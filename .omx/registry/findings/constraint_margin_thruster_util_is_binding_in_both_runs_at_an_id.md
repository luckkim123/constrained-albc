---
title: "`Constraint/margin/thruster_util` is binding in both runs at an identical margin"
tags: ["auto-captured"]
created: 2026-08-04T05:08:41.653435
updated: 2026-08-04T05:08:41.653435
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

> **SCOPE 2026-08-14 -- this page is about the `trpo_obs76fault_s30_260804_043926` pair**
> (report `diagnose-20260804-093500`), where the margin is **identical at 7.17**.
> It does NOT contradict `constraint_margin_thruster_util_is_the_binding_constraint_in_bot.md`,
> which reports margin **8.51 vs 7.17** -- that page measures a DIFFERENT pair,
> `trpo_obs76_s30_260803_233239` (report `diagnose-20260804-045000`). "Identical margin" and
> "wider margin" are both true, for their own run pair. State the run or the record is unreadable.


# `Constraint/margin/thruster_util` is binding in both runs at an identical margin

`Constraint/margin/thruster_util` is binding in both runs at an identical margin and pressure, so the widened observation does not change how hard the policy leans on its actuator budget.

[EVIDENCE: profile engine tier 2 — margin 7.17 and JC/dk 0.821 in both, with `attitude` the deepest slack in both]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76fault_s30_260804_043926/analysis/diagnose-20260804-093500/report.md
