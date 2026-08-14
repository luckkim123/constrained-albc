---
title: "DORAEMON curriculum saturation is iteration-clocked, not env-clocked: 4x num_envs (4096->16384) moved Gate A by only 250 of ~7000 iterations"
tags: ["doraemon", "curriculum", "saturation", "num_envs", "scale-up", "budgeting"]
created: 2026-08-09T05:17:29.261243
updated: 2026-08-09T05:19:03.843405
sources: ["diagnose-20260809-142000"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# DORAEMON curriculum saturation is iteration-clocked, not env-clocked: 4x num_envs (4096->16384) moved Gate A by only 250 of ~7000 iterations

DORAEMON's curriculum expansion clock runs in ITERATIONS, not in environment-steps, so raising num_envs does not buy a wider DR box before saturation. Measured on the current attitude-only obs72 plant: trpo_dgx16k_s30_260805_185713 at num_envs=16384 closed Gate A (all 21 dims at Beta(1,1), kl_step 0, ess_ratio exactly 1.000) at iteration 7250, against the ~7000 the 4096-env lineage reaches. Quadrupling the env count bought 250 iterations out of ~7000, i.e. ~3.5%.

WHY: a DORAEMON boundary fires every step_interval=250 ITERATIONS regardless of how many envs contributed episodes to that window. More envs make each iteration's success estimate less noisy, but they do not add boundary events, and it is boundary events that widen the box.

CONSEQUENCE for budgeting a scale-up: past saturation the extra env budget buys frozen-DR iterations only, at 4x the cost per iteration. This is exactly the guard pre-registered in experiments/.../teacher_baseline_posttam/README.md ("this config's box saturates at iter 7000 ... the expansion clock is in iteration units; without widening the DR bounds first, a budget increase only buys frozen-DR iterations"). That guard was written as an untested prediction about num_envs dependence; this run tests it and it holds.

So: to get a wider box, widen the declared DR bounds or lengthen the run, NOT the env count. Sizing an env scale-up should be justified by wall-clock per iteration or gradient noise, never by "more DR coverage".

Caveat: single seed, single run, non-reference machine (DGX GB10). The 250-iteration difference is a point measurement against a lineage figure, not a paired comparison.

Related: eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr (only none is cross-comparable), 32768_envs_fit_on_the_dgx_gb10_83_2_121_7_gb_peak_no_fallback_at (env-count cost curve on the same machine).

---

## Update (2026-08-09T05:19:03.843405)

DORAEMON's curriculum expansion clock runs in ITERATIONS, not in environment-steps, so raising num_envs does not buy a wider DR box before saturation. Measured on the current attitude-only obs72 plant: trpo_dgx16k_s30_260805_185713 at num_envs=16384 closed Gate A (all 21 dims at Beta(1,1), kl_step 0, ess_ratio exactly 1.000) at iteration 7250, against the ~7000 the 4096-env lineage reaches. Quadrupling the env count bought 250 iterations out of ~7000, i.e. ~3.5%.

WHY: a DORAEMON boundary fires every step_interval=250 ITERATIONS regardless of how many envs contributed episodes to that window. More envs make each iteration's success estimate less noisy, but they do not add boundary events, and it is boundary events that widen the box.

CONSEQUENCE for budgeting a scale-up: past saturation the extra env budget buys frozen-DR iterations only, at 4x the cost per iteration. This is exactly the guard pre-registered in experiments/.../teacher_baseline_posttam/README.md ("this config's box saturates at iter 7000 ... the expansion clock is in iteration units; without widening the DR bounds first, a budget increase only buys frozen-DR iterations"). That guard was written as an untested prediction about num_envs dependence; this run tests it and it holds.

So: to get a wider box, widen the declared DR bounds or lengthen the run, NOT the env count. Sizing an env scale-up should be justified by wall-clock per iteration or gradient noise, never by "more DR coverage".

Caveat: single seed, single run, non-reference machine (DGX GB10). The 250-iteration difference is a point measurement against a lineage figure, not a paired comparison.

Related: eval_py_static_doraemon_dr_grades_each_run_on_its_own_learned_dr (only none is cross-comparable), 32768_envs_fit_on_the_dgx_gb10_83_2_121_7_gb_peak_no_fallback_at (env-count cost curve on the same machine).

SOURCE: experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md, section "doraemon"; doraemon_state.pt Beta state at step_count 13401 (21/21 saturated); DORAEMON/kl_step 4.8e-04 -> 5.5e-05 -> 0 across the 6.5-7.25 / 7.25-8 / 8-8.75 kiter windows.

