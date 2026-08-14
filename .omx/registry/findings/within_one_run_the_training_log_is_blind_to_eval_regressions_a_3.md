---
title: "Within one run the training log is blind to eval regressions: a 34 percent none-level degradation moved every TB metric under 1 percent (bounds the cross-treatment reward-decomposition rule)"
tags: ["training-dynamics", "reward-decomposition", "eval", "regression-detection", "tensorboard", "methodology"]
created: 2026-08-09T05:18:00.488967
updated: 2026-08-09T05:19:53.114292
sources: ["diagnose-20260809-142000"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Within one run the training log is blind to eval regressions: a 34 percent none-level degradation moved every TB metric under 1 percent (bounds the cross-treatment reward-decomposition rule)

Within a single run, the training log cannot see an eval regression on this plant. Do not use TensorBoard to schedule evals, to pick a stopping point, or to detect that a policy has gotten worse — only the fixed exam sees it.

MEASURED: in trpo_dgx16k_s30_260805_185713, the `none`-level steady-state attitude error degraded 34% between model_7500 (0.4968 deg) and model_9000 (0.6644 deg). Across the iteration windows bracketing that degradation, every training-side metric moved by under 1%:

- Reward/att_rp 6.545 -> 6.496 (-0.7%), the term the exam measures, flat to three digits
- Reward/total 8.357 -> 8.290; Train/mean_reward 250.7 -> 248.6
- Policy/surrogate_loss -0.0976 -> -0.0980; Loss/kl 0.005012 -> 0.005040
- Grad/actor_step 0.0188 -> 0.0177; Grad/sigma_step 5.07e-04 -> 4.87e-04
- Loss/value_function 0.626 -> 0.616; Loss/cost_value 1.026 -> 0.912
- Encoder/z_std 0.394 -> 0.393; Policy/encoder_grad_norm 0.0370 -> 0.0376
- all 21 Constraint/* tags flat; no margin ever went negative
- Policy/entropy and mean_noise_std continued their slow monotone decline with NO inflection

The single exception is DORAEMON/success_rate, which bottoms at 0.5743 in the 9.25-10k window and recovers to ~0.60 — it tracks the exam curve in SHAPE but with ~3% amplitude against a 34% eval swing. Too weak to be a detector; useful only as corroboration after the fact.

BOUNDS AN EXISTING RULE. dr_harder_reward_decomposition_confirms_eval_trades_on_the_train establishes that Reward/* decomposition confirms eval trades on the training side. That result is CROSS-TREATMENT (three runs with different DR configs, att_rp 5.38 vs 4.50 vs 5.36). This finding is CROSS-ITERATION WITHIN ONE RUN, and there the same instrument is blind. Both are true; keep the axes separate. Reward decomposition discriminates between configurations, not between checkpoints of one configuration.

PRACTICAL RULE: a stopping decision or a checkpoint choice must be backed by fixed-exam evals at enough points to resolve the curve. See eval_schedule_too_sparse_can_manufacture_a_false_plateau for how sparse that must not be.

SOURCE: experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md, sections "reward" and "trpo"; window dump over the run's single event file (138 scalar tags).

---

## Update (2026-08-09T05:19:53.114292)

Within a single run, the training log cannot see an eval regression on this plant. Do not use TensorBoard to schedule evals, to pick a stopping point, or to detect that a policy has gotten worse — only the fixed exam sees it.

MEASURED: in trpo_dgx16k_s30_260805_185713, the `none`-level steady-state attitude error degraded 34% between model_7500 (0.4968 deg) and model_9000 (0.6644 deg). Across the iteration windows bracketing that degradation, every training-side metric moved by under 1%:

- Reward/att_rp 6.545 -> 6.496 (-0.7%), the term the exam measures, flat to three digits
- Reward/total 8.357 -> 8.290; Train/mean_reward 250.7 -> 248.6
- Policy/surrogate_loss -0.0976 -> -0.0980; Loss/kl 0.005012 -> 0.005040
- Grad/actor_step 0.0188 -> 0.0177; Grad/sigma_step 5.07e-04 -> 4.87e-04
- Loss/value_function 0.626 -> 0.616; Loss/cost_value 1.026 -> 0.912
- Encoder/z_std 0.394 -> 0.393; Policy/encoder_grad_norm 0.0370 -> 0.0376
- all 21 Constraint/* tags flat; no margin ever went negative
- Policy/entropy and mean_noise_std continued their slow monotone decline with NO inflection

The single exception is DORAEMON/success_rate, which bottoms at 0.5743 in the 9.25-10k window and recovers to ~0.60 — it tracks the exam curve in SHAPE but with ~3% amplitude against a 34% eval swing. Too weak to be a detector; useful only as corroboration after the fact.

BOUNDS AN EXISTING RULE. dr_harder_reward_decomposition_confirms_eval_trades_on_the_train establishes that Reward/* decomposition confirms eval trades on the training side. That result is CROSS-TREATMENT (three runs with different DR configs, att_rp 5.38 vs 4.50 vs 5.36). This finding is CROSS-ITERATION WITHIN ONE RUN, and there the same instrument is blind. Both are true; keep the axes separate. Reward decomposition discriminates between configurations, not between checkpoints of one configuration.

PRACTICAL RULE: a stopping decision or a checkpoint choice must be backed by fixed-exam evals at enough points to resolve the curve. See an_eval_schedule_too_sparse_to_resolve_the_curve_manufactures_a_ for how sparse that must not be.

SOURCE: experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md, sections "reward" and "trpo"; window dump over the run's single event file (138 scalar tags).

