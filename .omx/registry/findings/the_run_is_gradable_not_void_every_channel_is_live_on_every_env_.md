---
title: "The run is gradable, not VOID: every channel is live on every env, the zero-orde"
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

# The run is gradable, not VOID: every channel is live on every env, the zero-orde

The run is gradable, not VOID: every channel is live on every env, the zero-order hold is physically present, and the heave channel carries 2.2x to 4.2x its own sensor-noise floor.

[EVIDENCE: `student_extra_summary_{none,soft,medium,hard}.json` in `static_260803_220328`; noise floor 0.1260 derived by the producer's own chain, `n_env_degenerate` computed per env rather than pooled]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
