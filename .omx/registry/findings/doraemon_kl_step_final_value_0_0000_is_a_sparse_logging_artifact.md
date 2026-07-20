---
title: "DORAEMON/kl_step final value 0.0000 is a sparse-logging artifact, NOT a frozen curriculum"
tags: ["doraemon", "kl_step", "sanity-gate", "tensorboard", "sparse-logging", "engine-output", "auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:28.708915
updated: 2026-07-20T07:52:44.177586
sources: ["diagnose-20260716-164016", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
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
