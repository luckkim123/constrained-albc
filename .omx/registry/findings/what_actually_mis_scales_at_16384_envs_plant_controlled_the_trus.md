---
title: "What actually mis-scales at 16384 envs, plant-controlled: the trust region does not, exploration does (sigma -11 to -29 percent) and the cost critic does (+29 percent)"
tags: ["num_envs", "batch-size", "entropy", "exploration", "trpo", "cost-critic", "scaling", "measurement"]
created: 2026-08-09T07:16:36.131841
updated: 2026-08-09T07:16:36.131841
sources: []
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# What actually mis-scales at 16384 envs, plant-controlled: the trust region does not, exploration does (sigma -11 to -29 percent) and the cost critic does (+29 percent)

Comparing 16384-env and 4096-env runs at matched iterations settles which hyperparameters actually
mis-scale with batch size on this plant. The comparison is only valid PLANT-CONTROLLED: against a
retired-plant 4096 run the value-function gap reads 25-33%, and almost all of that is the plant, not
the env count.

MEASURED 2026-08-09, `trpo_dgx16k_s30` (16384, DGX) vs `trpo_hydrorc_s30_260728_013136` (4096,
workstation), same current obs72 plant, TB scalars averaged over matched iteration windows:

| window | 400-600 | 2400-2600 | 4800-5000 |
|---|---|---|---|
| Loss/value_function | 0.850 vs 1.128 (16k better) | 0.447 vs 0.445 | 0.479 vs 0.428 (+12%) |
| Loss/cost_value | 0.523 vs 0.733 (better) | 0.631 vs 0.583 (+8%) | 0.861 vs 0.669 (**+29%**) |
| Policy/mean_noise_std | 0.1307 vs 0.1851 (**-29%**) | 0.0860 vs 0.1030 (-17%) | 0.0813 vs 0.0915 (-11%) |
| Loss/kl | 0.00496 vs 0.00490 | 0.00501 vs 0.00498 | 0.00499 vs 0.00503 |
| DORAEMON/success_rate | 0.327 vs 0.030 (**11x**) | 0.865 vs 0.854 | 0.772 vs 0.809 |
| Train/mean_reward | 237.0 vs 201.3 | 269.7 vs 268.5 | 262.1 vs 265.6 |

`Policy/entropy` follows sigma (-5.37 vs -2.62 at 400-600).

WHAT DOES NOT MIS-SCALE. The trust region: `Loss/kl` is identical to three digits at every window, so
`max_kl` needs no rescaling under a 4x batch. That confirms by measurement what the design argument
predicted — ConstraintTRPO has no actor learning rate at all (natural gradient plus line search inside
a KL trust region), so the classic "big batch needs a retuned lr" failure mode has no surface on the
actor. The value critic is also fine: ~1% mid-run, +12% only at the end.

WHAT DOES. Exploration, at every matched window (-11 to -29%), and the COST critic (+29% at the end
and diverging). The cost critic matters specifically for ConstraintTRPO, where it supplies the
constraint advantages; the regime-preserving correction is `num_mini_batches` 4 -> 16 (minibatch stays
65,536, critic takes 80 Adam steps instead of 20, no lr change), not a value_lr change.

THE STORY IN TWO NUMBERS. At iteration 400-600 the 16384 run is 11x ahead on `success_rate`
(0.327 vs 0.030) and 18% ahead on reward — the 4x batch really does learn faster per iteration. By
iteration 2400-2600 the advantage is gone (0.865 vs 0.854). What remains is the cost: exploration
spent getting there. Since the DR box has a fixed ceiling that both configurations reach well inside
the budget, converging faster to it buys nothing, and the run ends with less sigma in reserve for the
post-saturation stretch. That is consistent with the 16k run regressing at iteration 9000 and never
beating its own iteration-7500 checkpoint.

MECHANISM for the sigma deficit: the entropy bonus gradient is analytic and therefore noise-free,
while the surrogate gradient is a sample mean whose noise falls with batch size. At a larger batch the
sigma-REDUCING systematic component accumulates more consistently across trust-region steps while the
sigma-RAISING bonus is unchanged, so the same `entropy_coef_per_dim` buys relatively less exploration.
There is no closed-form scaling for this (the noise-scale literature excludes trust-region methods), so
the coefficient must be calibrated empirically against a measured 4096 sigma trajectory. The divergence
is fully resolved by iteration 1100, so a ~1100-iteration probe (about 3 h at 16384) suffices — do not
guess the coefficient across a 50-hour run.

SOURCE: TB event files of `teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/train` and
`teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/train`, window means over
`Loss/*`, `Policy/*`, `DORAEMON/success_rate`, `Train/mean_reward`; A2 (`trpo_entcoefzero`) for the
entropy-bonus-vs-IPO-barrier attribution; A3 (`trpo_minstdthr008`) for why `min_std_per_dim` is not
the lever.

