---
title: "The env-to-env dispersion moves in opposite directions at the two ends: CV falls"
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

# The env-to-env dispersion moves in opposite directions at the two ends: CV falls

The env-to-env dispersion moves in opposite directions at the two ends: CV falls 51.8 -> 31.8 at none but rises 138.9 -> 167.4 at hard, so the channels stabilise the easy regime and destabilise the hard one.

[EVIDENCE: `ss_error_std` / `ss_error` from `summary.json`; hard `ss_error_std` 0.7740 -> 1.1679 is a +50.9% growth in absolute env spread]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
