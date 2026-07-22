---
title: "The encoder is healthy and slightly more active: latent std unchanged, grad flow"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-22T01:58:11.799085
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The encoder is healthy and slightly more active: latent std unchanged, grad flow

The encoder is healthy and slightly more active: latent std unchanged, grad flow UP (encoder_grad_norm +33.8%, enc_step +17.7%) -- releasing the settling barrier gave the encoder marginally more to learn, with no latent collapse. | tag                   | A5      | anchor  | delta% | |-----------------------|---------|---------|--------| | Encoder/z_std         | 0.4147  | 0.4000  | +3.7%  | | Policy/encoder_grad_norm | 0.0550 | 0.0411 | +33.8% | | Grad/enc_step         | 0.0016  | 0.0013  | +17.7% | | Encoder/z_mean        | -0.0289 | -0.0203 | -42.3% |

[EVIDENCE: TB last-200-iter means]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
