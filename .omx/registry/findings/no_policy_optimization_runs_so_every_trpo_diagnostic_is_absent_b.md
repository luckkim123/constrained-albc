---
title: "No policy optimization runs, so every TRPO diagnostic is absent by construction."
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

# No policy optimization runs, so every TRPO diagnostic is absent by construction.

No policy optimization runs, so every TRPO diagnostic is absent by construction.

[EVIDENCE: none of `entropy`, `noise_std`, `line_search_success`, `kl`, `Policy/surrogate_loss`, `Grad/actor_step`, `Grad/sigma_step` appears among the 9 logged tags; the actor is loaded frozen from the teacher checkpoint and never updated]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

No policy optimization runs, so every TRPO diagnostic is absent by construction.

[EVIDENCE: none of `entropy`, `noise_std`, `line_search_success`, `kl`, `Policy/surrogate_loss`, `Grad/actor_step`, `Grad/sigma_step` appears among the 9 logged tags; the actor is loaded frozen from the teacher checkpoint and never updated]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T07:04:05.217247)

No policy optimization runs, so every TRPO diagnostic is absent by construction.

[EVIDENCE: none of `Policy/entropy`, `Policy/mean_noise_std`, `Policy/line_search_success`, `Loss/kl`, `Policy/surrogate_loss`, `Grad/actor_step`, `Grad/sigma_step` appears among the 9 logged tags; the actor is loaded frozen from `model_4999.pt` and never updated]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

No policy optimization runs, so every TRPO diagnostic is absent by construction.

[EVIDENCE: none of `Policy/entropy`, `Policy/mean_noise_std`, `Policy/line_search_success`, `Loss/kl`, `Policy/surrogate_loss`, `Grad/actor_step`, `Grad/sigma_step` appears among the 9 logged tags; the actor is loaded frozen from `model_4999.pt` and never updated]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
