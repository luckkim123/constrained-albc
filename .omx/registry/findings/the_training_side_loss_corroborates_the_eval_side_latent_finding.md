---
title: "The training-side loss corroborates the eval-side latent finding independently: "
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

> # SUPERSEDED 2026-08-13 -- this page's method was refuted an hour after it was written.
>
> **Do not use `loss_latent` as a corroborator of an eval-side latent result.**
> `training_loss_latent_is_not_a_valid_corroborator_of_an_eval_side.md`
> (created 14:52, one hour after this page's 13:52; `confidence: high`,
> `status: resolved`) shows a four-arm table in which the widened-encoder arm moved
> train `loss_latent` and eval `sum(MSE)` in OPPOSITE directions. The agreement this
> page reports for B2 is therefore not evidence of anything -- it is one arm where
> two loosely-related quantities happened to point the same way.
>
> This page's number (B2's trailing-50 `loss_latent` 5.9 percent below control) is
> still a correct measurement. What is void is the inference drawn from it.


# The training-side loss corroborates the eval-side latent finding independently: 

The training-side loss corroborates the eval-side latent finding independently: B2's final-window `loss_latent` is 5.9% below the control's, in the same direction as the eval `R2` gain.

[EVIDENCE: TensorBoard `student/loss_latent`, trailing-50 mean over 1000 logged iterations per run]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
