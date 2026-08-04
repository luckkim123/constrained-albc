---
title: "More training is not the lever: the latent loss has flattened into a plateau whe"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T04:31:12.085504
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# More training is not the lever: the latent loss has flattened into a plateau whe

More training is not the lever: the latent loss has flattened into a plateau where even a LINEAR extrapolation needs ~1600 further iterations to halve it.

[EVIDENCE: `student/loss_latent` trailing windows, iters 600-800 mean 0.00442 vs 800-1000 mean 0.00417 (-5.63%, slope -1.25e-6/iter); 0.00400 / 1.25e-6 = 1605 iters, i.e. 2.6x the run just to halve a quantity whose in-loop counterpart is 10-19x larger]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
