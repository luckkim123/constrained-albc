---
title: "Roughly 40% of that headline is the denominator moving, not the error falling: B"
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

# Roughly 40% of that headline is the denominator moving, not the error falling: B

Roughly 40% of that headline is the denominator moving, not the error falling: B2's MSE measured against the CONTROL's denominator gives +0.1837, so the error-only delta is +0.0931 (1.75 sigma) and the denominator contributes +0.0624.

[EVIDENCE: `1 - sum(mse_B2)/sum(var_CTL)` = +0.1837 vs CTL's own +0.0905; `sum(Var)` 0.6120 -> 0.6626 = +8.3%]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
