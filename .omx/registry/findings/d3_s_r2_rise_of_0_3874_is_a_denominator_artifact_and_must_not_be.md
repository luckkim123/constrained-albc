---
title: "d3's `R2` rise of +0.3874 is a denominator artifact and must not be read as an i"
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

# d3's `R2` rise of +0.3874 is a denominator artifact and must not be read as an i

d3's `R2` rise of +0.3874 is a denominator artifact and must not be read as an improvement: its MSE got 23.6% WORSE over the same interval.

[EVIDENCE: d3 MSE 0.0631 -> 0.0780 while its `Var(l_true)` grew enough to lift the ratio]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
