---
title: "The five declared encoder TB tags are absent because the teacher's encoder is fr"
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

# The five declared encoder TB tags are absent because the teacher's encoder is fr

The five declared encoder TB tags are absent because the teacher's encoder is frozen during distillation, so encoder quality is measured from `latent_hard.npz` instead — the substance is in the `encoder` section above, not skipped.

[EVIDENCE: 0 tags under the `Encoder/` prefix; `Policy/encoder_grad_norm` and `Grad/enc_step` likewise absent]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md
