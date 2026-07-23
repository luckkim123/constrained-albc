---
title: "Optimisation is healthy and near-identical across all runs; entropy collapse and"
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T04:54:21.766685
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Optimisation is healthy and near-identical across all runs; entropy collapse and

Optimisation is healthy and near-identical across all runs; entropy collapse and a low noise floor are universal, not a property of the new plant. | run | entropy | noise_std | surrogate_loss | line_search_success | Loss/kl | Grad/actor_step | Grad/sigma_step | |:--|--:|--:|--:|--:|--:|--:|--:| | anchor s30 | -8.93 | 0.09 | -0.1010 | 1.00 | 0.00496 | 0.0219 | 0.000682 | | anchor s31 | -9.07 | 0.09 | -0.0951 | 1.00 | 0.00503 | 0.0180 | 0.000580 | | anchor s32 | -9.07 | 0.09 | -0.0930 | 1.00 | 0.00500 | 0.0187 | 0.000580 | | Arm N 8192 | -9.22 | 0.08 | -0.0958 | 1.00 | 0.00488 | 0.0181 | 0.000669 | | dgxseed30 | -9.06 | 0.08 | -0.0974 | 1.00 | 0.00504 | 0.0159 | 0.000847 | | dgxseed31 | -9.11 | 0.09 | -0.0971 | 1.00 | 0.00504 | 0.0150 | 0.000626 | | dgxseed32 | -8.99 | 0.09 | -0.0988 | 1.00 | 0.00503 | 0.0184 | 0.000735 | `Loss/kl` ~0.005 against `max_kl=0.005` — the trust region is saturated, and `line_search_success` is 1.00 everywhere, so every step is accepted at the cap.

[EVIDENCE: `omx reduce tb-final --window 200` + engine TIER lines]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
