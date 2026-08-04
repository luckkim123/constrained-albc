---
title: "The recipe executed byte-for-byte as configured and the run converged cleanly."
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

# The recipe executed byte-for-byte as configured and the run converged cleanly.

The recipe executed byte-for-byte as configured and the run converged cleanly.

[EVIDENCE: checkpoint `cfg` comparison of `student_999.pt` (X1) vs `student_999.pt` (baseline) differs in exactly two of the 40 keys in their union (baseline 39, X1 40) — `extra_obs_from_policy_tail` (absent/False -> True) and the `run_name` label; `encoder_type=gru`, `gru_hidden=128`, `gru_head_hidden=64`, `gru_layers=1`, `dagger_mix=select`, `dagger_beta_start=dagger_beta_end=0.5`, `lambda_latent=1.0`, `seed=30`, `policy_obs_dim=76`, `privileged_dim=28`, `extra_obs_dim=0`, `teacher_run_dir` and `env_sensor_cfg` all identical]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
