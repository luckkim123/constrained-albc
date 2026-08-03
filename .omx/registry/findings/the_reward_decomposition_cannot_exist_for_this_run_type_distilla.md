---
title: "The reward decomposition cannot exist for this run type: distillation freezes th"
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

# The reward decomposition cannot exist for this run type: distillation freezes th

The reward decomposition cannot exist for this run type: distillation freezes the teacher actor and optimises only the latent and action losses, so no `Reward/*` tag is emitted.

[EVIDENCE: the by-name census above, from a direct EventAccumulator dump of all three event files, against 1000 logged samples for every tag that DOES exist]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
