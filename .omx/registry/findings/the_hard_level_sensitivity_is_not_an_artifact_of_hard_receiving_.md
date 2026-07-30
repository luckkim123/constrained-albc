---
title: "The hard-level sensitivity is not an artifact of hard receiving a larger absolut"
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

# The hard-level sensitivity is not an artifact of hard receiving a larger absolut

The hard-level sensitivity is not an artifact of hard receiving a larger absolute perturbation: normalized by the perturbation actually injected, hard is still 5x soft and 30-40x none/medium at the smallest k.

[EVIDENCE: sigma is level-dependent so k=0.5 injects `||delta l_hat||` of 0.395 at hard versus 0.249 at none; dividing the attitude degradation by that realized norm leaves hard at 1.070 deg/unit against none 0.036, medium 0.027, soft 0.214]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
