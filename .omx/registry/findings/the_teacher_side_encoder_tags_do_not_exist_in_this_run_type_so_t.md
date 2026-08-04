---
title: "The teacher-side encoder tags do not exist in this run type, so the encoder grou"
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

# The teacher-side encoder tags do not exist in this run type, so the encoder grou

The teacher-side encoder tags do not exist in this run type, so the encoder group is instrumented entirely from the eval side.

[EVIDENCE: none of `Encoder/z_std`, `Encoder/z_min`, `Encoder/z_max`, `Policy/encoder_grad_norm`, `Grad/enc_step` appears among the 9 logged TB tags; the student encoder is fit against a frozen teacher whose own encoder is not stepped]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
