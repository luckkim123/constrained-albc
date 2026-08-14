---
title: "Per-dim latent indices are not comparable across teachers, so no per-dim claim f"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T05:08:41.653435
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Per-dim latent indices are not comparable across teachers, so no per-dim claim f

Per-dim latent indices are not comparable across teachers, so no per-dim claim from the `student_distill_eint` campaign transfers to this run.

[EVIDENCE: the Phase-D teacher's encoder was trained from scratch on a 76D policy obs; nothing in the architecture pins latent dimension ordering or semantics, so index d_k denotes different directions in the two teachers' latent spaces]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md

---

## Update (2026-08-04T05:08:41.653435)

Per-dim latent indices are not comparable across teachers, so no per-dim claim from the `student_distill_eint` campaign transfers to this run.

[EVIDENCE: the Phase-D teacher's encoder was trained from scratch on a 76D policy obs; nothing in the architecture pins latent dimension ordering or semantics, so index d_k denotes different directions in the two teachers' latent spaces]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
