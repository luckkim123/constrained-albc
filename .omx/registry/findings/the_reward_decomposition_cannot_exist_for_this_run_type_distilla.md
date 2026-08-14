---
title: "The reward decomposition cannot exist for this run type: distillation freezes th"
tags: ["auto-captured", "trpo_sdeint_b2_extraobs_s30_260803_215117", "trpo_sdeint_b2wide_gru256_s30_260803_231320"]
created: 2026-08-03T13:52:43.764401
updated: 2026-08-04T05:08:41.653435
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md", "experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The reward decomposition cannot exist for this run type: distillation freezes th

The reward decomposition cannot exist for this run type: distillation freezes the teacher actor and optimises only the latent and action losses, so no `Reward/*` tag is emitted.

[EVIDENCE: the by-name census above, from a direct EventAccumulator dump of all three event files, against 1000 logged samples for every tag that DOES exist]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2_extraobs_s30_260803_215117/analysis/diagnose-20260803-223517/report.md

---

## Update (2026-08-03T15:00:28.482580)

The reward decomposition cannot exist for this run type: distillation freezes the teacher actor and optimises only the latent and action losses, so no `Reward/*` tag is emitted.

[EVIDENCE: the by-name census above from a direct EventAccumulator dump of `trpo_sdeint_b2wide_gru256_s30_260803_231320`'s event file, whose full scalar tag list is the nine `student/*` entries in the loss table]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-03T15:16:03.279468)

The reward decomposition cannot exist for this run type: distillation freezes the teacher actor and optimises only the latent and action losses, so no `Reward/*` tag is emitted.

[EVIDENCE: the by-name census above from a direct EventAccumulator dump of `trpo_sdeint_b2wide_gru256_s30_260803_231320`'s event file, whose full scalar tag list is the nine `student/*` entries in the loss table]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md

---

## Update (2026-08-04T05:08:41.653435)

The reward decomposition cannot exist for this run type: distillation freezes the teacher actor and optimises only the latent and action losses, so no `Reward/*` tag is emitted.

[EVIDENCE: the by-name census above from a direct EventAccumulator dump of `trpo_sdeint_b2wide_gru256_s30_260803_231320`'s event file, whose full scalar tag list is the nine `student/*` entries in the loss table]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
