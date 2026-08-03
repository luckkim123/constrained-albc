---
title: "No TRPO learning-dynamics group exists: there is no policy optimisation in a dis"
tags: ["auto-captured", "trpo_sdeint_b2_extraobs_s30_260803_215117"]
created: 2026-08-03T13:52:43.764401
updated: 2026-08-03T13:52:43.764401
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# No TRPO learning-dynamics group exists: there is no policy optimisation in a dis

No TRPO learning-dynamics group exists: there is no policy optimisation in a distillation run, so `entropy`, `noise_std`, `line_search_success`, `kl`, `Policy/surrogate_loss`, `Grad/actor_step` and `Grad/sigma_step` are all absent.

[EVIDENCE: 0 tags under `Policy/` and `Grad/`; the only gradient scalar is `student/grad_norm`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
