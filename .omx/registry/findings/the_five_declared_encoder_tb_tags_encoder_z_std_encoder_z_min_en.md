---
title: "The five declared encoder TB tags (`Encoder/z_std`, `Encoder/z_min`, `Encoder/z_"
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The five declared encoder TB tags (`Encoder/z_std`, `Encoder/z_min`, `Encoder/z_

The five declared encoder TB tags (`Encoder/z_std`, `Encoder/z_min`, `Encoder/z_max`, `Policy/encoder_grad_norm`, `Grad/enc_step`) are absent because the teacher's encoder is frozen during distillation; encoder quality is measured from `latent_hard.npz` instead and is the subject of the `encoder` section above.

[EVIDENCE: 0 tags under the `Encoder/` prefix; `Policy/encoder_grad_norm` and `Grad/enc_step` likewise absent]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
