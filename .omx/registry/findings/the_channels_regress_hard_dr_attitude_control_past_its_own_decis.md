---
title: "The channels regress hard-DR attitude control past its own decision floor: +0.14"
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

# The channels regress hard-DR attitude control past its own decision floor: +0.14

The channels regress hard-DR attitude control past its own decision floor: +0.1401 deg against a floor of 0.1, while none / soft / medium all stay sub-floor.

[EVIDENCE: `summary.json` `hard/att_norm/ss_error`, `static_260803_221435` 0.5574 vs `static_260803_220328` 0.6975; floor from `summary.json decision_floors.ss_error`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
