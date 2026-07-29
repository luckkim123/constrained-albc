---
title: "Lambda_latent is bracketed and CLOSED: no decision-grade control effect in [0,4] and lambda=1 is a measured local optimum"
tags: ["student", "distillation", "latent", "loss-weight", "albc", "lambda", "bracket", "null-result"]
created: 2026-07-29T08:30:37.609173
updated: 2026-07-29T08:30:37.609173
sources: ["diagnose-20260729-170800", "diagnose-20260729-172500"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: resolved
---

# Lambda_latent is bracketed and CLOSED: no decision-grade control effect in [0,4] and lambda=1 is a measured local optimum

The student distillation loss is `MSE(a_hat, a_t) + lambda_latent * MSE(l_hat, l_t)`
(`_core/student/runner.py:274`), default `lambda_latent = 1.0` (`_core/student/config.py:70`).
Campaign `student_distill_eint` bracketed that weight from both sides on 2026-07-29, single-variable
against the A0 anchor (TCN, dagger_beta 1.0, 2048 envs, 1000 iters, seed 30, teacher E-int
`trpo_eint_s30_rs2350_260727_195102/model_4999.pt`):

- B1a `trpo_sdeint_b1_lam0_s30_260729_163637` -- lambda 0 (latent term deleted)
- A0 `trpo_sdeint_a0_tcn_s30_260729_130559` -- lambda 1 (anchor)
- B1b `trpo_sdeint_b1_lam4_s30_260729_170008` -- lambda 4

## Control: no decision-grade effect anywhere in [0, 4]

att_norm `ss_error` delta vs A0, deg, against the eval's own declared floor of 0.1:

| level | B1a (lambda 0) | B1b (lambda 4) |
|:--|--:|--:|
| none | +0.0347 | -0.0069 |
| soft | +0.0200 | -0.0155 |
| medium | +0.0192 | +0.0361 |
| hard | +0.0741 | -0.0744 |

All eight below floor, and the two arms disagree in sign at every level -- the signature of noise, a
stronger null than either arm alone. Survival 100% at every level for both.

## lambda = 1 is a MEASURED local optimum, not an inherited default

In-loop latent MSE (`summary_latent.json` `overall_mse`) is U-shaped in lambda at none/soft/medium and
flat at hard:

| level | lambda 0 | lambda 1 | lambda 4 |
|:--|--:|--:|--:|
| none | 0.084381 | 0.032975 | 0.044489 |
| soft | 0.056464 | 0.030741 | 0.038266 |
| medium | 0.059666 | 0.040636 | 0.044823 |
| hard | 0.070786 | 0.068041 | 0.067976 |

At hard the spread is 4% across a 4x range of lambda -- the weight is simply irrelevant there.

## The residual is not weight-limited (saturation)

Quadrupling the weight and multiplying `grad_norm` by 3.72 (0.023759 -> 0.088345) improves open-loop
`loss_latent` by 1.5% (0.003040 -> 0.002993, iters 900-999 mean). The latent residual sits at a floor
bounded below by the conditional variance of the target given the student's observation window; no
reweighting goes below it.

`loss_action` is monotone in lambda -- 0.000113 / 0.000131 / 0.000135 for lambda 0 / 1 / 4 -- so the two
terms compete rather than cooperate, but the competition costs nothing measurable in control.

## Bite check by loss IDENTITY, not by config value

Both arms were verified from the logged losses, because a logged hyperparameter proves the flag was
parsed and NOT that the objective changed:

- B1a: `loss_total` 0.000113 == `loss_action` 0.000113 (latent term absent from the total)
- A0:  `loss_total` 0.003171 == 0.000131 + 1 x 0.003040
- B1b: `loss_total` 0.012108 == 0.000135 + 4 x 0.002993

Adopt this as the standard bite check for any loss-weight arm.

## Cost

Free. `time_train` 0.218767 / 0.218941 / 0.219568 s for lambda 0 / 1 / 4 -- a 0.4% spread. One arm is
~13 minutes on GPU1 at 2048 envs.

## Decision

Keep `lambda_latent = 1.0`. Lambda is CLOSED as an axis for this plant: do not spend another arm on it.
The remaining student-side leverage is representational (A0g's GRU is the only arm in the campaign to
clear the control floor), not objective-weighting. The metric correction this bracket produced lives on
`latent_dim_d4_collapses_at_none_dr_in_every_student_arm_and_the_` (ratio == R2 for a calibrated
predictor; the ratio's target is R2, not 1).

