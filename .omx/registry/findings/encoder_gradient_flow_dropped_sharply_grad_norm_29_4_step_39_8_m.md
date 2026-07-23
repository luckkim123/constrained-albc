---
title: "Encoder gradient flow dropped sharply (grad norm -29.4%, step -39.8%), meaning t"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Encoder gradient flow dropped sharply (grad norm -29.4%, step -39.8%), meaning t

Encoder gradient flow dropped sharply (grad norm -29.4%, step -39.8%), meaning the encoder had materially less to learn from a 24D input — the removed dims were carrying a large share of the learning signal.

[EVIDENCE: TB Policy/encoder_grad_norm 0.0290 vs 0.0411, Grad/enc_step 0.0008 vs 0.0013]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
