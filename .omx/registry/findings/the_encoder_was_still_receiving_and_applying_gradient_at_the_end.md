---
title: "The encoder was still receiving and applying gradient at the end of training in "
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The encoder was still receiving and applying gradient at the end of training in 

The encoder was still receiving and applying gradient at the end of training in all three runs, so the flat aggregate latent statistics reflect a converged encoder rather than a detached one.

[EVIDENCE: TB last-200-iter means — `Policy/encoder_grad_norm` A1 0.05468 / ref5k 0.04110 / extend8k 0.04860; `Grad/enc_step` A1 0.00113 / ref5k 0.00132 / extend8k 0.00121]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
