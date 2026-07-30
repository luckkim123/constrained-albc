---
title: "d4's ratio falls monotonically with lambda while its MSE is flat, which is the t"
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

# d4's ratio falls monotonically with lambda while its MSE is flat, which is the t

d4's ratio falls monotonically with lambda while its MSE is flat, which is the textbook signature of MSE regression shrinking toward the conditional mean on a weakly-identifiable target — pushing harder on the matching loss buys shrinkage, not fidelity.

[EVIDENCE: ratio 0.1166 -> 0.0721 -> 0.0416 across lambda 0 -> 1 -> 4, while in-loop MSE moves only 0.0621 -> 0.0540 -> 0.0582 against a target variance of ~0.059 that is essentially unchanged]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
