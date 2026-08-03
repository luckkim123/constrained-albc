---
title: "C3's unrecoverable dirty-tree diff was INERT on the training path: the control's"
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

# C3's unrecoverable dirty-tree diff was INERT on the training path: the control's

C3's unrecoverable dirty-tree diff was INERT on the training path: the control's iteration-0 values are bit-identical to C3's on every logged tag.

[EVIDENCE: first-sample values identical to 6 decimals — `loss_latent` 0.067585, `loss_action` 0.003916, `loss_total` 0.071501, `grad_norm` 0.393604, `dagger_teacher_frac` 0.502889 — with final-window `loss_latent` diverging only 0.35% (0.004842 vs 0.004859), consistent with GPU nondeterminism accumulating from an identical start]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
