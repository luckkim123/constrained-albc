---
title: "The optimiser is healthy and behaves identically on both runs — the line search "
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The optimiser is healthy and behaves identically on both runs — the line search 

The optimiser is healthy and behaves identically on both runs — the line search essentially never failed and the trust region landed on the same KL. TRPO mechanics do not distinguish the two policies.

[EVIDENCE: TB final scalars both runs: `Policy/line_search_success` 1.0000 (run mean 0.9998) on each; `Loss/kl` 0.0050 on each; `Policy/surrogate_loss` -0.1003 vs -0.1072; config `max_kl=0.005`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The optimiser is healthy and behaves identically on both runs — the line search essentially never failed and the trust region landed on the same KL. TRPO mechanics do not distinguish the two policies.

[EVIDENCE: TB final scalars both runs: `Policy/line_search_success` 1.0000 (run mean 0.9998) on each; `Loss/kl` 0.0050 on each; `Policy/surrogate_loss` -0.1003 vs -0.1072; config `max_kl=0.005`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
