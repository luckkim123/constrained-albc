---
title: "d6, the pre-registered dimension, improves for a real reason and not only throug"
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

# d6, the pre-registered dimension, improves for a real reason and not only throug

d6, the pre-registered dimension, improves for a real reason and not only through its denominator: its MSE falls 32.1% (0.0543 -> 0.0369) and the error-only part of its `R2` delta is +0.4579 of the +0.6278 total (73%).

[EVIDENCE: per-dim table above; `1 - mse_B2[6]/var_CTL[6]` against CTL's own d6 `R2`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
