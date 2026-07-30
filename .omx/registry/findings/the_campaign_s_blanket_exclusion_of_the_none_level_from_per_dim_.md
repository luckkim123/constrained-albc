---
title: "The campaign's blanket exclusion of the `none` level from per-dim collapse count"
tags: ["auto-captured", "trpo_sdeint_b4b_beta05_s30_260729_153436"]
created: 2026-07-29T07:25:05.571851
updated: 2026-07-29T07:25:05.571851
sources: ["/workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The campaign's blanket exclusion of the `none` level from per-dim collapse count

The campaign's blanket exclusion of the `none` level from per-dim collapse counting is too broad: d4 is the best-conditioned dimension at that level, yet all three arms drive its ratio under 0.1 there, so that collapse is a real under-dispersion rather than a denominator artifact.

[EVIDENCE: l_true per-dim env-variance at none, d4 = 5.85e-2 (A0), 5.93e-2 (A0g), 6.04e-2 (B4b), the maximum across the nine dims in every arm, while the per-dim ratio at d4 is 0.0721/0.0740/0.0380 respectively; the aggregate caveat is real (l_true env-variance spans 122x across dims at none vs 64x at hard) but does not apply to the dimension actually collapsing]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
