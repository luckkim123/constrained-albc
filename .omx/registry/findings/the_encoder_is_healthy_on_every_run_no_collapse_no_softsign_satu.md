---
title: "The encoder is healthy on every run — no collapse, no softsign saturation, live "
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T06:44:07.820188
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder is healthy on every run — no collapse, no softsign saturation, live 

The encoder is healthy on every run — no collapse, no softsign saturation, live gradients. | run | Encoder/z_std | Encoder/z_min | Encoder/z_max | Policy/encoder_grad_norm | Grad/enc_step | |:--|--:|--:|--:|--:|--:| | anchor s30 | 0.40 | -0.724 | 0.728 | 0.0377 | 0.00176 | | anchor s31 | 0.39 | -0.735 | 0.737 | 0.0333 | 0.00115 | | anchor s32 | 0.39 | -0.734 | 0.735 | 0.0343 | 0.00116 | | Arm N 8192 | 0.39 | -0.729 | 0.737 | 0.0316 | 0.00150 | | dgxseed30 | 0.39 | -0.736 | 0.731 | 0.0418 | 0.00138 | | dgxseed31 | 0.41 | -0.715 | 0.729 | 0.0385 | 0.00110 | | dgxseed32 | 0.41 | -0.726 | 0.726 | 0.0435 | 0.00189 | Against the profile's thresholds: `z_std` 0.39-0.41 is well above the 0.1 LOW flag; `z_min/z_max` ~+-0.73 is well inside the +-0.95 softsign-saturation flag; `encoder_grad_norm` ~0.03-0.04 is two-plus orders above the 1e-4 DEAD flag.

[EVIDENCE: `omx reduce tb-final` + engine]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md

---

## Update (2026-07-23T06:44:07.820188)

The encoder is healthy on every run — no collapse, no softsign saturation, live gradients. | run | Encoder/z_std | Encoder/z_min | Encoder/z_max | Policy/encoder_grad_norm | Grad/enc_step | |:--|--:|--:|--:|--:|--:| | anchor s30 | 0.40 | -0.724 | 0.728 | 0.0377 | 0.00176 | | anchor s31 | 0.39 | -0.735 | 0.737 | 0.0333 | 0.00115 | | anchor s32 | 0.39 | -0.734 | 0.735 | 0.0343 | 0.00116 | | Arm N 8192 | 0.39 | -0.729 | 0.737 | 0.0316 | 0.00150 | | dgxseed30 | 0.39 | -0.736 | 0.731 | 0.0418 | 0.00138 | | dgxseed31 | 0.41 | -0.715 | 0.729 | 0.0385 | 0.00110 | | dgxseed32 | 0.41 | -0.726 | 0.726 | 0.0435 | 0.00189 | Against the profile's thresholds: `z_std` 0.39-0.41 is well above the 0.1 LOW flag; `z_min/z_max` ~+-0.73 is well inside the +-0.95 softsign-saturation flag; `encoder_grad_norm` ~0.03-0.04 is two-plus orders above the 1e-4 DEAD flag.

[EVIDENCE: `omx reduce tb-final` + engine]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
