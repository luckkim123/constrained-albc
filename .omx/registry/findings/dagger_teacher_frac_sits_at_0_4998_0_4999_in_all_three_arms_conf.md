---
title: "`dagger_teacher_frac` sits at 0.4998-0.4999 in all three arms, confirming the fi"
tags: ["auto-captured", "trpo_sdeint_b2_extraobs_s30_260803_215117"]
created: 2026-08-03T13:52:43.764401
updated: 2026-08-03T13:52:43.764401
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `dagger_teacher_frac` sits at 0.4998-0.4999 in all three arms, confirming the fi

`dagger_teacher_frac` sits at 0.4998-0.4999 in all three arms, confirming the fixed beta of 0.5 recorded in the pre-registration's correction rather than the 1.0 -> 0.0 anneal the obs4 program plan described.

[EVIDENCE: TensorBoard `student/dagger_beta` constant 0.500000 over all 1000 iterations in all three runs]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
