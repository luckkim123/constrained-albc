---
title: "Roll is the only axis that degrades at hard — its q90 crosses 20 and its count o"
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

# Roll is the only axis that degrades at hard — its q90 crosses 20 and its count o

Roll is the only axis that degrades at hard — its q90 crosses 20 and its count of envs peaking above 20 deg rises 4.67 -> 7.00 — while pitch and yaw both improve and yaw's heavy-tail count goes to zero.

[EVIDENCE: `summary.json hard/{roll,pitch,yaw}` in `static_260803_221435` vs `static_260803_220328`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
