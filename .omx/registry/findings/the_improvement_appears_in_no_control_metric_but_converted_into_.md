---
title: "The improvement appears in no control metric, but converted into the unit that a"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-05T09:49:50.734092
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The improvement appears in no control metric, but converted into the unit that a

The improvement appears in no control metric, but converted into the unit that actually couples to control the latent gain is small enough that this null is EXPECTED — it is not evidence that latent fidelity and control are decoupled.

[EVIDENCE: hard sumMSE 0.6367 -> 0.5544 is an RMSE ratio sqrt(0.5544/0.6367) = 0.9331, a 6.69% reduction, NOT the ~17% a naive reading of delta R2 = +0.169 suggests; probe C1-latsens (wiki page `the_frozen_actor_s_sensitivity_to_latent_error_is_strongly_level`, analysis `diagnose-20260729-184021`) measured hard att_norm ss_error at 0.6496 deg for k=0 and 1.0728 deg for k=0.5, where k scales that student's OWN per-dim in-loop RMSE — 0.4232 deg per 50% RMSE change, so 6.69% prices at 0.4232 * 0.0669 / 0.5 = 0.057 deg against a 0.10 deg floor]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

The improvement appears in no control metric, but converted into the unit that actually couples to control the latent gain is small enough that this null is EXPECTED — it is not evidence that latent fidelity and control are decoupled.

[EVIDENCE: hard sumMSE 0.6367 -> 0.5544 is an RMSE ratio sqrt(0.5544/0.6367) = 0.9331, a 6.69% reduction, NOT the ~17% a naive reading of delta R2 = +0.169 suggests; probe C1-latsens (wiki page `the_frozen_actor_s_sensitivity_to_latent_error_is_strongly_level`, analysis `diagnose-20260729-184021`) measured hard att_norm ss_error at 0.6496 deg for k=0 and 1.0728 deg for k=0.5, where k scales that student's OWN per-dim in-loop RMSE — 0.4232 deg per 50% RMSE change, so 6.69% prices at 0.4232 * 0.0669 / 0.5 = 0.057 deg against a 0.10 deg floor]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
