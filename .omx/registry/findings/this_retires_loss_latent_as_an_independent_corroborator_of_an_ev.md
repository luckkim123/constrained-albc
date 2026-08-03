---
title: "This retires `loss_latent` as an independent corroborator of an eval-side latent"
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

# This retires `loss_latent` as an independent corroborator of an eval-side latent

This retires `loss_latent` as an independent corroborator of an eval-side latent result, which the Phase C report used it as. Phase C cited B2's `loss_latent` -5.9% as agreeing with its eval `R2` gain; this arm demonstrates the same signal agreeing while the eval disagrees, so the agreement carried no information.

[EVIDENCE: Phase C report `diagnose-20260803-223517`, the `distillation loss` section; against the WIDE row above. Phase C's VERDICT is unaffected — it was INCONCLUSIVE on the latent axis, not on this corroboration]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
