---
title: "Latent error shows up as oscillation as well as steady-state offset, and jitter "
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Latent error shows up as oscillation as well as steady-state offset, and jitter 

Latent error shows up as oscillation as well as steady-state offset, and jitter carries the same hard-first ordering — which independently corroborates the ss_error reading on a metric that was not used to define the floor crossing.

[EVIDENCE: jitter rises monotonically with k at every level; at k=0.5 hard has already more than doubled (0.2144 -> 0.4841) while none moves 0.1240 -> 0.1538]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
