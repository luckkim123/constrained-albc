---
title: "Five of the profile's seven metric groups are structurally absent from a distill"
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

# Five of the profile's seven metric groups are structurally absent from a distill

Five of the profile's seven metric groups are structurally absent from a distillation run, confirmed by dumping the raw TB tag set rather than trusting the engine's empty cells.

[EVIDENCE: EventAccumulator on the run's event file returns exactly 9 scalar tags, all under `student/`: dagger_beta, dagger_teacher_frac, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
