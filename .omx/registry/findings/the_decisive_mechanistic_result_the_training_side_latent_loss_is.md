---
title: "The decisive mechanistic result: the TRAINING-side latent loss is unchanged — X1"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-04T07:04:05.217247
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The decisive mechanistic result: the TRAINING-side latent loss is unchanged — X1

The decisive mechanistic result: the TRAINING-side latent loss is unchanged — X1 is marginally WORSE on it — while the CLOSED-LOOP latent error improves, so the intervention did not increase fitting capacity but changed what the fitted model generalizes to.

[EVIDENCE: trailing-100-iteration means of the TB scalars via a scratch EventAccumulator script under `.omx/scratch/<sid>/py/tb_window_means.py` (the documented workaround for `omx reduce tb-final` being unrunnable in this container) — `student/loss_latent` 0.004062 -> 0.004236 (+4.3%), `student/loss_action` 0.000274 -> 0.000289 (+5.7%), `student/loss_total` 0.004335 -> 0.004526 (+4.4%), `student/grad_norm` 0.050254 -> 0.039029 (-22.3%)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
