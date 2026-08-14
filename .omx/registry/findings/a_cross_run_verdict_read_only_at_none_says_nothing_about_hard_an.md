---
title: "A cross-run verdict read only at none says nothing about hard: anchor asymmetry makes the hard exams incomparable, and re-scoring under one saturated anchor is 30 minutes with no retraining"
tags: ["eval", "doraemon", "anchor", "cross-run", "methodology", "num_envs", "paired-test"]
created: 2026-08-09T06:41:18.847327
updated: 2026-08-09T06:41:18.847327
sources: ["diagnose-20260809-142000"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# A cross-run verdict read only at none says nothing about hard: anchor asymmetry makes the hard exams incomparable, and re-scoring under one saturated anchor is 30 minutes with no retraining

A cross-run verdict read only at `none` is a verdict about nominal physics, not about deployment. The
teacher_envscale_dgx campaign concluded "4x envs bought nothing" from `none` alone, and it could not
do otherwise: the two runs' `hard` exams were different boxes, so no hard-level comparison existed.

WHY THE HARD EXAM DIVERGED. `eval.py static --doraemon-dr-from <dir>` grades against the DORAEMON
distribution recorded in that dir's TB event file. Run A (`trpo_iterbudget_s30_260805_012813`) was
anchored on E-int, whose box was only 65% expanded (0 of 21 dims at Beta(1,1) at iteration 4999),
while `trpo_dgx16k_s30_260805_185713` graded itself on its OWN saturated box. Measured on the eval
npz at `hard`: the 16k draws are systematically wider (std ratios payload_mass 1.37x, cob_x 1.35x,
body_mass 1.19x, added_mass_0 1.16x, lin_damp_0 1.08x), while at `none` the same arrays are
elementwise identical. So Run A's hard 0.6599 deg and the 16k's hard 0.9702 deg were scored on
different exams and may not be quoted against each other in either direction.

THE FIX IS CHEAP AND REQUIRES NO RETRAINING. Re-score every finalist under ONE saturated anchor.
Executed 2026-08-09 (3 evals, 31.8 min, zero training GPU): pairing then verified 24/24 elementwise
identical at `none`, `hard` AND `ood` across all three. Paired per-env attitude error over 64 shared
seed-42 scenarios, positive t = B worse:

  RunA model_9998 -> 16k model_7500 : none t=-2.51 (57/64 B better), hard t=+1.51, ood t=+0.17
  RunA model_9998 -> 16k model_13400: none t=+4.28, hard t=+1.93, ood t=+1.54
  16k model_7500  -> 16k model_13400: none t=+9.69, hard t=-0.12, ood t=+3.16

RESULT. The 4096x10000 run wins or ties at hard and ood against both 16384 checkpoints; 16384
separates only at `none`, by 0.033 deg. The env-scaling no-benefit conclusion SURVIVES at the
deployment-relevant levels — but it was not established until this re-score, and it was luck that the
answer did not change.

A per-axis trade the aggregate hides: 16k model_7500 is better on roll (`none` 0.2927 vs 0.4479,
`ood` 0.5840 vs 0.7408) while Run A is better on pitch (`none` 0.1905 vs 0.3224, `hard` 0.3376 vs
0.5551, `ood` 0.3060 vs 0.4882) — every one past the 0.10 deg floor, while `att_norm` stays inside
floors at every level. Two policies that differ on both axes can read as identical in the aggregate.

RULE. Before any cross-run verdict that will be used to size a run or pick a deployment artifact:
(1) check what box each side's eval was anchored to; (2) if they differ, re-score under one anchor
before quoting hard/ood; (3) read the per-axis rows, not only `att_norm`. Anchor asymmetry is
invisible in summary.json — it shows up only in the dr_* draw spans of the npz.

SOURCE: .omx/programs/dgx-final-teacher/PLAN.md gate G0 (RESULT block); evals
teacher_iter_budget/.../eval/static_260809_150721 and
teacher_envscale_dgx/.../eval/static_260809_151752 + static_260809_152826, all with
--ood --doraemon-dr-from <16k train dir> --seed 42.

