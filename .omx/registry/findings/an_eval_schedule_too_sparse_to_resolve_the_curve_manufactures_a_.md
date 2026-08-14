---
title: "An eval schedule too sparse to resolve the curve manufactures a false plateau and fires the stop rule on an artifact"
tags: ["eval", "methodology", "stop-rule", "paired-test", "plateau", "scheduling"]
created: 2026-08-09T05:18:54.500867
updated: 2026-08-09T05:18:54.500867
sources: ["diagnose-20260809-142000"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# An eval schedule too sparse to resolve the curve manufactures a false plateau and fires the stop rule on an artifact

An eval schedule sparse enough to straddle a transient regression will report it as a plateau, and a stop rule reading that schedule will fire on an artifact. This happened: trpo_dgx16k_s30_260805_185713 was stopped at iteration 13419 of 20000 on a "performance has plateaued" verdict that three extra eval points overturned.

THE ARTIFACT. The pre-approved schedule evaluated 5000 / 7500 / 10000 / 12500. Read alone, that is an oscillation around a flat level — 0.5606, 0.4968, 0.6179, 0.5466 deg `none` ss_error — with 12500 statistically indistinguishable from 5000 (paired t = +0.59), i.e. 7500 iterations of training for no net gain. Adding 9000 / 11000 / 13400 turns it into one regression followed by a clean monotone recovery: 0.5606, 0.4968, **0.6644**, 0.6179, 0.5963, 0.5466, 0.5366.

EVERY CONSECUTIVE STEP FROM 9000 TO 13400 IMPROVES, and the paired per-env test resolves each one: t = -4.72, -9.45, -8.85, -2.80. A per-env linear fit over 9000..13400 has 62 of 64 environments improving, slope t = -13.16. The run was stopped mid-recovery, roughly 0.063 deg short of its own best checkpoint.

WHY THE 4-POINT READ FAILS. Two of the four points (10000, 12500) sit on the recovery limb, so the sequence "good, bad, less bad" reads as noise around a mean rather than as a trajectory. Nothing about the four values themselves signals that a fifth point between 7500 and 10000 is far worse than either.

RULES.
1. Before declaring a plateau, evaluate consecutive points and require the paired test to fail to reject at EACH step. A plateau is a chain of nulls, not a scatter of values near each other.
2. Do not let a two-strikes stop rule ("two consecutive eval points worse than the running best by more than X") read a schedule with 2500-iteration gaps. On this run the rule reached 2/2 at iteration 10000 and was broken at 12500 purely by where the samples landed.
3. Use the paired per-env instrument, not summary means. All evals at seed 42 see the same 64 scenarios, so per-env differencing is available and is far more sensitive than a mean against its spread — the recovery steps are 0.01-0.02 deg, invisible against a between-env sd of ~0.1 but decisive when paired.
4. The training log will not rescue a sparse schedule; see within_one_run_the_training_log_is_blind_to_eval_regressions.

SOURCE: experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md, section "tracking"; paired per-env series over seven data_none.npz files.

