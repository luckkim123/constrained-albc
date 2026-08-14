---
title: "The reward decomposition does not exist in this run — no reward is computed at a"
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

# The reward decomposition does not exist in this run — no reward is computed at a

The reward decomposition does not exist in this run — no reward is computed at all.

[EVIDENCE: none of `Reward/att_rp`, `Reward/yaw_vel`, `Reward/bias`, `Reward/smoothness`, `Reward/thruster`, `Reward/torque` appears among the 9 logged tags; the stage-2 objective is `MSE(a_hat, a_t) + lambda_latent * MSE(l_hat, l_t)`, logged as `student/loss_action` and `student/loss_latent`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

The reward decomposition does not exist in this run — no reward is computed at all.

[EVIDENCE: none of `Reward/att_rp`, `Reward/yaw_vel`, `Reward/bias`, `Reward/smoothness`, `Reward/thruster`, `Reward/torque` appears among the 9 logged tags; the stage-2 objective is `MSE(a_hat, a_t) + lambda_latent * MSE(l_hat, l_t)`, logged as `student/loss_action` and `student/loss_latent`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T07:04:05.217247)

The reward decomposition does not exist in this run — no reward is computed at all.

[EVIDENCE: none of `Reward/att_rp`, `Reward/yaw_vel`, `Reward/bias`, `Reward/smoothness`, `Reward/thruster`, `Reward/torque` appears among the 9 logged tags; the stage-2 objective is `MSE(a_hat, a_t) + lambda_latent * MSE(l_hat, l_t)`, logged as `student/loss_action` and `student/loss_latent`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md

---

## Update (2026-08-05T09:49:50.734092)

The reward decomposition does not exist in this run — no reward is computed at all.

[EVIDENCE: none of `Reward/att_rp`, `Reward/yaw_vel`, `Reward/bias`, `Reward/smoothness`, `Reward/thruster`, `Reward/torque` appears among the 9 logged tags; the stage-2 objective is `MSE(a_hat, a_t) + lambda_latent * MSE(l_hat, l_t)`, logged as `student/loss_action` and `student/loss_latent`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
