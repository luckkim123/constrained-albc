---
title: "DORAEMON/kl_step final value 0.0000 is a sparse-logging artifact, NOT a frozen curriculum"
tags: ["doraemon", "kl_step", "sanity-gate", "tensorboard", "sparse-logging", "engine-output", "auto-captured", "trpo_biasema_260715_142543", "trpo_buoyanchor_s30_260722_134743", "gotcha"]
created: 2026-07-16T07:48:28.708915
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260716-164016", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "diagnose-20260723-134359"]
links: []
category: debugging
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# DORAEMON/kl_step final value 0.0000 is a sparse-logging artifact, NOT a frozen curriculum

TRAP: reading DORAEMON/kl_step final scalar as 0.0000 and concluding the curriculum froze / trust region collapsed is WRONG. The scalar is only written on the 250-iter curriculum steps (step_interval=250); between steps it logs 0. On P-B1 (trpo_biasema_260715_142543) the full 5000-point trajectory shows value=0.1200 at every sampled curriculum step (iter 500/1000/.../4500), max=0.1200, nonzero count 18/5000. The trust region stayed PINNED at the configured kl_ub=0.12 (config.py:544) the whole run. This is the exp-analyze 'empty cell is a hypothesis not a fact' rule applied to a sparse scalar: to check the kl_step sanity gate, pull the trajectory and look at the nonzero (curriculum-step) samples, never the final value. Same pattern will bite any DORAEMON per-step scalar (entropy_before/after also only move on curriculum steps). Found during report diagnose-20260716-164016.

---

## Merged from the_kl_step_sanity_gate_passes_the_trust_region_stayed_pinned_at.md (2026-07-20T07:52:44.177586)

# The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configu

The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configured 0.12 for the whole run. The final-step value of 0.0000 is a sparse-logging artifact (the scalar is only written on the 250-iter curriculum steps), NOT a frozen curriculum.

[EVIDENCE: TB `DORAEMON/kl_step` on P-B1, full 5000-point trajectory: value = 0.1200 at every curriculum step sampled (iter 500/1000/1500/2000/2500/3000/3500/4000/4500), max = 0.1200, nonzero count = 18/5000; config `doraemon(kl_ub=0.12, performance_lb=250.0, step_interval=250)` at `constrained_albc/envs/main/config.py:544`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The `kl_step` sanity gate PASSES — the trust region stayed pinned at the configured 0.12 for the whole run. The final-step value of 0.0000 is a sparse-logging artifact (the scalar is only written on the 250-iter curriculum steps), NOT a frozen curriculum.

[EVIDENCE: TB `DORAEMON/kl_step` on P-B1, full 5000-point trajectory: value = 0.1200 at every curriculum step sampled (iter 500/1000/1500/2000/2500/3000/3500/4000/4500), max = 0.1200, nonzero count = 18/5000; config `doraemon(kl_ub=0.12, performance_lb=250.0, step_interval=250)` at `constrained_albc/envs/main/config.py:544`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Merged from doraemon_kl_step_reads_0_0_in_a_200_sample_trailing_window_on_al.md (2026-07-23T07:32:14.143051)

# `DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — thi

`DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — this is a LOGGING artifact, not a stalled curriculum. `DORAEMON/kl_step` has n=5000 samples of which only **19** are non-zero: the tag is written only at the ~20 curriculum update points implied by `step_interval=250` over 5000 iters. The trailing-200 window contains no update point. `DORAEMON/success_rate` by contrast has 4776 of 5000 non-zero and reads 0.808 at iter 4999.

[EVIDENCE: raw TB series, anchor s30]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

`DORAEMON/kl_step` reads 0.0 in a 200-sample trailing window on all 7 runs — this is a LOGGING artifact, not a stalled curriculum. `DORAEMON/kl_step` has n=5000 samples of which only **19** are non-zero: the tag is written only at the ~20 curriculum update points implied by `step_interval=250` over 5000 iters. The trailing-200 window contains no update point. `DORAEMON/success_rate` by contrast has 4776 of 5000 non-zero and reads 0.808 at iter 4999.

[EVIDENCE: raw TB series, anchor s30]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md


---

## Merged from doraemon_kl_step_final_window_mean_reads_0_0_a_logging_artifact_.md (2026-07-23T07:32:14.143051)

# DORAEMON/kl_step final-window mean reads 0.0 -- a logging artifact, not a stalled curriculum

GOTCHA: 'omx reduce tb-final --window 200' on DORAEMON/kl_step returns 0.0 for every run, which reads as 'the curriculum stopped stepping'. It has not. EVIDENCE (raw EventAccumulator dump, buoyanchor s30): DORAEMON/kl_step has n=5000 samples of which only 19 are non-zero -- the tag is written ONLY at the ~20 curriculum update points implied by step_interval=250 over 5000 iters, and a trailing-200 window contains no update point. Contrast DORAEMON/success_rate: 4776 of 5000 non-zero, reads 0.808 at iter 4999. CHECK INSTEAD: read the non-zero subsequence, or read curriculum_trajectory.json (the Beta a/b snapshots) which shows the curriculum state directly. This is the 'engine empty cell is a HYPOTHESIS not a fact' rule applied to a trailing-window reducer: a sparse tag's window mean is meaningless, not evidence of absence. Re-visit: analysis diagnose-20260723-134359 section 'doraemon'.
