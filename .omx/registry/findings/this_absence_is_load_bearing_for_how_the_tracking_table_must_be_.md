---
title: "This absence is load-bearing for how the `tracking` table must be read, not mere"
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

# This absence is load-bearing for how the `tracking` table must be read, not mere

This absence is load-bearing for how the `tracking` table must be read, not merely bookkeeping: with the curriculum replaced by a fixed hard box, the four DR columns are four fixed evaluation points rather than curriculum stages, which is why `none` is the out-of-distribution end rather than the easy end.

[EVIDENCE: the same `configure_env_for_student` substitution; corroborated by `none` carrying the HIGHEST CV of the four levels in both baselines (C3 53.5%, CTL 51.8% against 33.0% / 34.0% at soft)]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
