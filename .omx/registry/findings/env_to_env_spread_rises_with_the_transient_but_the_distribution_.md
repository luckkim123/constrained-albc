---
title: "Env-to-env spread rises with the transient but the distribution stays DC-bias-li"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Env-to-env spread rises with the transient but the distribution stays DC-bias-li

Env-to-env spread rises with the transient but the distribution stays DC-bias-like rather than heavy-tailed: roll `ss_error` CV is 0.211 for A1 vs 0.172 (ref5k) and 0.251 (extend8k) — a modest widening, not a tail blow-up, and A1's `os_env_q90`/`os_env_mean` ratio (1.06) matches the references (1.10 / 1.07).

[EVIDENCE: `summary.json` none/roll — CV = ss_error_std/ss_error = 0.055/0.261 (A1), 0.037/0.215 (ref5k), 0.043/0.171 (extend8k)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
