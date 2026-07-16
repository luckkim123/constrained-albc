---
title: "The encoder is alive, not collapsed, and unsaturated: z_std well above the 0.1 c"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-16T06:36:01.268339
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder is alive, not collapsed, and unsaturated: z_std well above the 0.1 c

The encoder is alive, not collapsed, and unsaturated: z_std well above the 0.1 collapse floor, z within the softsign range (no clipping at +-0.95), and gradient flow non-trivial (grad_norm >> 1e-4 DEAD threshold).

[EVIDENCE: TB final-window means: z_std 0.412, z_min -0.730, z_max 0.728, z_mean ~0.02, encoder_grad_norm 0.061, enc_step 0.0028]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md

---

## Update (2026-07-16T06:36:01.268339)

The encoder is alive, not collapsed, and unsaturated: z_std well above the 0.1 collapse floor, z within the softsign range (no clipping at +-0.95), and gradient flow non-trivial (grad_norm >> 1e-4 DEAD threshold).

[EVIDENCE: TB final-window means: z_std 0.412, z_min -0.730, z_max 0.728, z_mean ~0.02, encoder_grad_norm 0.061, enc_step 0.0028]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
