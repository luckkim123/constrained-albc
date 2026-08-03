---
title: "`dagger_teacher_frac` is 0.499958 in both B2 and WIDE, identical to six decimals"
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `dagger_teacher_frac` is 0.499958 in both B2 and WIDE, identical to six decimals

`dagger_teacher_frac` is 0.499958 in both B2 and WIDE, identical to six decimals, confirming the two arms saw the same teacher/student mix and the difference is the encoder width alone.

[EVIDENCE: TensorBoard `student/dagger_beta` constant at 0.500000 across all 1000 iterations in both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
