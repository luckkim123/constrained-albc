---
title: "No tail effect accompanies the degradation — the damage is a steady-state and di"
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

# No tail effect accompanies the degradation — the damage is a steady-state and di

No tail effect accompanies the degradation — the damage is a steady-state and dispersion effect, not envs falling off a cliff.

[EVIDENCE: roll `n_gt20` does not rise systematically with k (none 2.33/1.67/1.00/0.67/1.67, hard 7.00/5.33/6.00/5.00/8.33 across k=0..4), every value far below the declared 15-env floor; survival is 100.0% at all four levels for all five k]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
