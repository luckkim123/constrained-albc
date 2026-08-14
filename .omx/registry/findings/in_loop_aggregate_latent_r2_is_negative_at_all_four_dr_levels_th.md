---
title: "In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student late"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T05:08:41.653435
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

> **SCOPE 2026-08-13 -- this page is about ONE run: `trpo_sdobs76_c3_gruselect_s30_260804_124951`.**
> It does NOT contradict `in_loop_aggregate_latent_r2_improves_at_all_four_dr_levels_and_a.md`,
> which measures a DIFFERENT run (`trpo_sdobs76_x1_tailsplit_s30_260804_151400`). The two
> titles are near-identical and opposite, so a reader who greps "latent R2" will hit one
> headline and conclude the other is stale. Both are correct, for their own run.
> State the run or the record is unreadable.


# In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student late

In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student latent is worse in closed loop than a constant-mean predictor of the teacher latent.

[EVIDENCE: latent_<level>.npz, per-dim R2 = 1 - MSE/Var_total via scratch `.omx/scratch/<sid>/py/latent_r2.py` — aggregate R2 = -1.581 (none), -0.904 (soft), -0.131 (medium), -0.078 (hard); at hard sum MSE 0.7007 exceeds sum Var 0.6500]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student latent is worse in closed loop than a constant-mean predictor of the teacher latent.

[EVIDENCE: latent_<level>.npz, per-dim R2 = 1 - MSE/Var_total via scratch `.omx/scratch/<sid>/py/latent_r2.py` — aggregate R2 = -1.581 (none), -0.904 (soft), -0.131 (medium), -0.078 (hard); at hard sum MSE 0.7007 exceeds sum Var 0.6500]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
