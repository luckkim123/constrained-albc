---
title: "In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student late"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T04:31:12.085504
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student late

In-loop aggregate latent R2 is NEGATIVE at all four DR levels — the student latent is worse in closed loop than a constant-mean predictor of the teacher latent.

[EVIDENCE: latent_<level>.npz, per-dim R2 = 1 - MSE/Var_total via scratch `.omx/scratch/<sid>/py/latent_r2.py` — aggregate R2 = -1.581 (none), -0.904 (soft), -0.131 (medium), -0.078 (hard); at hard sum MSE 0.7007 exceeds sum Var 0.6500]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
