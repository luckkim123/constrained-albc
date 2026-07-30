---
title: "The probe measures the actor's transfer function, not the encoder's quality, and"
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

# The probe measures the actor's transfer function, not the encoder's quality, and

The probe measures the actor's transfer function, not the encoder's quality, and deliberately leaves the encoder untouched: `last_l_hat` publishes the true encoder output before the perturbation is added, so the latent diagnostic in this sweep still describes A0g's encoder exactly as the arm report did.

[EVIDENCE: `student_policy.py` sets `self.last_l_hat = l_hat` and only then adds `k * sigma * randn_like(l_hat)` to the copy handed to `teacher.actor_forward`; the k=0 run reproduces the published A0g summary on all 376 fields]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_a0g_gru_s30_260729_151017/analysis/diagnose-20260729-184021/report.md
