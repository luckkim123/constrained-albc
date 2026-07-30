---
title: "The higher training losses are expected rather than a defect: at beta 0.5 the lo"
tags: ["auto-captured", "trpo_sdeint_b4b_beta05_s30_260729_153436"]
created: 2026-07-29T07:25:05.571851
updated: 2026-07-29T07:25:05.571851
sources: ["/workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The higher training losses are expected rather than a defect: at beta 0.5 the lo

The higher training losses are expected rather than a defect: at beta 0.5 the loss is evaluated on a harder, partly self-induced state distribution, so a larger number does not mean worse learning.

[EVIDENCE: loss_latent 0.003809 (B4b) vs 0.003040 (A0), +25%; loss_action 0.000208 vs 0.000131, +59%; yet grad_norm 0.021950 vs 0.023759, i.e. B4b's gradients are the smallest of the three despite the largest loss]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc-student/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b4b_beta05_s30_260729_153436/analysis/diagnose-20260729-161459/report.md
