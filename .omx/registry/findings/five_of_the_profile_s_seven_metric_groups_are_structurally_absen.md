---
title: "Five of the profile's seven metric groups are structurally absent from a distill"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Five of the profile's seven metric groups are structurally absent from a distill

Five of the profile's seven metric groups are structurally absent from a distillation run, confirmed by dumping the raw TB tag set rather than trusting the engine's empty cells.

[EVIDENCE: EventAccumulator on the run's event file returns exactly 9 scalar tags, all under `student/`: dagger_beta, dagger_teacher_frac, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

Five of the profile's seven metric groups are structurally absent from a distillation run, confirmed by dumping the raw TB tag set rather than trusting the engine's empty cells.

[EVIDENCE: EventAccumulator on the run's event file returns exactly 9 scalar tags, all under `student/`: dagger_beta, dagger_teacher_frac, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T07:04:05.217247)

Five of the profile's seven metric groups are structurally absent from a distillation run, confirmed by dumping the raw TB tag set rather than trusting the engine's empty cells.

[EVIDENCE: EventAccumulator on this run's event file returns exactly 9 scalar tags, all under `student/`: dagger_beta, dagger_teacher_frac, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

Five of the profile's seven metric groups are structurally absent from a distillation run, confirmed by dumping the raw TB tag set rather than trusting the engine's empty cells.

[EVIDENCE: EventAccumulator on this run's event file returns exactly 9 scalar tags, all under `student/`: dagger_beta, dagger_teacher_frac, grad_norm, iter, loss_action, loss_latent, loss_total, time_collect, time_train]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
