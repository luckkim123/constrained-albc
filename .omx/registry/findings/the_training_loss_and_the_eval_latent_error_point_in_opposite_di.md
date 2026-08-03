---
title: "The training loss and the eval latent error point in OPPOSITE directions for thi"
tags: ["auto-captured", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:16:03.279468
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The training loss and the eval latent error point in OPPOSITE directions for thi

The training loss and the eval latent error point in OPPOSITE directions for this arm: WIDE has the best `loss_latent` of all four runs at -9.1% below B2, while its eval `sum(MSE)` is 13.5% worse. The wider encoder fits the training state distribution better and transfers worse.

[EVIDENCE: TensorBoard `student/loss_latent` trailing-50 over 1000 iterations vs `sum(MSE)` from `latent_hard.npz`; DAgger at fixed beta 0.5 makes the training states half teacher-driven while the eval is fully student-driven, so the two distributions are genuinely different]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-03T15:16:03.279468)

The training loss and the eval latent error point in OPPOSITE directions for this arm: WIDE has the best `loss_latent` of all four runs at -9.1% below B2, while its eval `sum(MSE)` is 13.5% worse. The wider encoder fits the training state distribution better and transfers worse.

[EVIDENCE: TensorBoard `student/loss_latent` trailing-50 over 1000 iterations vs `sum(MSE)` from `latent_hard.npz`; DAgger at fixed beta 0.5 makes the training states half teacher-driven while the eval is fully student-driven, so the two distributions are genuinely different]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
