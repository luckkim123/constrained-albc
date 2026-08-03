---
title: "B2 draws an independent env set from both baselines while the control and C3 sha"
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

# B2 draws an independent env set from both baselines while the control and C3 sha

B2 draws an independent env set from both baselines while the control and C3 share one exactly, which is the behaviour validity gate 1 predicted from `depth_noise_std` being the only new RNG consumer.

[EVIDENCE: `dr_*` arrays in `data_hard.npz` of `static_260803_220328` / `static_260803_221435` / `static_260729_194845`; none of the differing keys are reorderings of each other (0 of 23 match after sorting)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
