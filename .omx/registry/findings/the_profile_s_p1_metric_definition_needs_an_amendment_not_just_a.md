---
title: "The profile's P1 metric definition needs an amendment, not just a caveat: the ag"
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

# The profile's P1 metric definition needs an amendment, not just a caveat: the ag

The profile's P1 metric definition needs an amendment, not just a caveat: the aggregate ratio should be reported against per-dim R2, because the two are the same quantity for a calibrated predictor and their divergence is the actual diagnostic.

[EVIDENCE: ratio-vs-R2 divergence separates the three regimes cleanly — calibrated (A0 d4 at none, 0.072 vs 0.083), over-dispersed (B1a d5 at none, 11.122 vs -94.199), and under-dispersed-but-honest (B1b d4 at none, 0.042 vs 0.025)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
