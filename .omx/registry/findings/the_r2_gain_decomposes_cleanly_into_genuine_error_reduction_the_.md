---
title: "The R2 gain decomposes cleanly into genuine error reduction — the denominator di"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-04T07:04:05.217247
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The R2 gain decomposes cleanly into genuine error reduction — the denominator di

The R2 gain decomposes cleanly into genuine error reduction — the denominator did not inflate it.

[EVIDENCE: at hard, `sumMSE` falls 0.6367 -> 0.5544 (-12.9%) while `sumVar` RISES 0.5766 -> 0.5927 (+2.8%); a denominator-driven artefact would require sumVar to grow while sumMSE held, which is the opposite of the sumMSE column]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
