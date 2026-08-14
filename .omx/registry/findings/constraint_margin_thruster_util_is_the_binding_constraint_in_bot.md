---
title: "`Constraint/margin/thruster_util` is the binding constraint in both runs and E-o"
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

> **SCOPE 2026-08-14 -- this page is about the `trpo_obs76_s30_260803_233239` pair**
> (report `diagnose-20260804-045000`), where the margin is **8.51 vs 7.17**.
> It does NOT contradict `constraint_margin_thruster_util_is_binding_in_both_runs_at_an_id.md`,
> which reports an **identical** margin of 7.17 -- that page measures a DIFFERENT pair,
> `trpo_obs76fault_s30_260804_043926` (report `diagnose-20260804-093500`). Both are correct for
> their own run pair. State the run or the record is unreadable.


# `Constraint/margin/thruster_util` is the binding constraint in both runs and E-o

`Constraint/margin/thruster_util` is the binding constraint in both runs and E-obs76 sits on it slightly less hard with a wider margin, which is what a fault-free plant predicts: a policy that never loses a thruster does not have to over-drive the survivors.

[EVIDENCE: profile engine tier 2 Constraints on both runs — JC/dk 0.787 vs 0.821, margin 8.51 vs 7.17; the same mechanism is recorded in wiki `ftc_fault_dr_a_b_result_2026_07_27_fault_dr_adopted_5_12x_less_m` as "Arm A's margin is HALVED because a fault-blind policy must over-drive the survivors"]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_obs76/trpo_obs76_s30_260803_233239/analysis/diagnose-20260804-045000/report.md
