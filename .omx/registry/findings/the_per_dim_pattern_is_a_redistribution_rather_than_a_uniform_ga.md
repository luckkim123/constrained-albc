---
title: "The per-dim pattern is a REDISTRIBUTION rather than a uniform gain — five dims i"
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

# The per-dim pattern is a REDISTRIBUTION rather than a uniform gain — five dims i

The per-dim pattern is a REDISTRIBUTION rather than a uniform gain — five dims improve (d0, d5, d6, d7, d8) and four regress (d1, d2, d3, d4) inside an unwidened 128-unit GRU — which is the capacity-crowding signature the pre-registration attributes to Lane 2, even though the W-latent region did not fire because the aggregate ROSE.

[EVIDENCE: the MSE column of the per-dim table; `StudentCfg.gru_hidden` = 128 unchanged in all three arms]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
