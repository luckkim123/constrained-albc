---
title: "The encoder is still receiving gradient on both runs, but P-B1's encoder learnin"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-16T07:48:44.950263
updated: 2026-07-16T13:13:10.984465
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder is still receiving gradient on both runs, but P-B1's encoder learnin

The encoder is still receiving gradient on both runs, but P-B1's encoder learning has slowed to roughly half the reference's — consistent with P-B1 having converged earlier (its reward plateaued from ~10%).

[EVIDENCE: TB final scalars: `Policy/encoder_grad_norm` 0.0423 (P-B1) vs 0.0618 (REF); `Grad/enc_step` 0.0014 vs 0.0030]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md

---

## Update (2026-07-16T13:13:10.984465)

The encoder is still receiving gradient on both runs, but P-B1's encoder learning has slowed to roughly half the reference's — consistent with P-B1 having converged earlier (its reward plateaued from ~10%).

[EVIDENCE: TB final scalars: `Policy/encoder_grad_norm` 0.0423 (P-B1) vs 0.0618 (REF); `Grad/enc_step` 0.0014 vs 0.0030]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260716-164016/report.md
