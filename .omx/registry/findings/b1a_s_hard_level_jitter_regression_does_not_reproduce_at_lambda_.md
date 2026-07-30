---
title: "B1a's hard-level jitter regression does NOT reproduce at lambda 4, which localiz"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# B1a's hard-level jitter regression does NOT reproduce at lambda 4, which localiz

B1a's hard-level jitter regression does NOT reproduce at lambda 4, which localizes it: removing the latent term costs oscillation (+62% at hard), while adding more of it costs only +12%, so the effect is specific to dropping the constraint rather than to perturbing lambda in general.

[EVIDENCE: att_norm ss_jitter at hard = 0.2169 (lambda 1), 0.3511 (lambda 0, +61.9%), 0.2427 (lambda 4, +11.9%); the same ordering holds at none, soft and medium]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
