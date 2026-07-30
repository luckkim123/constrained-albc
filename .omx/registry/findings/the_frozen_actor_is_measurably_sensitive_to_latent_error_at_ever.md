---
title: "The frozen actor is measurably sensitive to latent error at every DR level, and "
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

# The frozen actor is measurably sensitive to latent error at every DR level, and 

The frozen actor is measurably sensitive to latent error at every DR level, and the response is monotone in the perturbation magnitude at all four — so latent fidelity is a real control lever, refuting the reading that the actor barely uses the latent at all.

[EVIDENCE: att_norm ss_error rises monotonically with k at every level in the table above; at k=4 the degradation is +0.624 / +0.568 / +1.088 / +1.524 deg for none/soft/medium/hard against a 0.1 deg floor]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
