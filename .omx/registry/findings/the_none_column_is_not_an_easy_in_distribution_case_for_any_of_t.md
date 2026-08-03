---
title: "The `none` column is not an easy in-distribution case for any of these students:"
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

# The `none` column is not an easy in-distribution case for any of these students:

The `none` column is not an easy in-distribution case for any of these students: `configure_env_for_student` disables DORAEMON and installs a static hard DR box, so every student is evaluated off-distribution at `none` by construction, and the B2 CV improvement there (51.8 -> 31.8) is a generalization result rather than an in-distribution one.

[EVIDENCE: `configure_env_for_student` in the student runner (the pre-registration's Lane 2 states the same, `next-20260803-184816.md`); `summary.json none/att_norm`]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
