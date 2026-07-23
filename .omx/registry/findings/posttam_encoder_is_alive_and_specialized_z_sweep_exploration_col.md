---
title: "Posttam encoder is alive and specialized (z-sweep) — exploration collapse is a converged optimum, not a dead encoder"
tags: ["encoder", "z-sweep", "exploration", "doraemon", "p-a1", "auto-captured", "trpo_buoyanchor_s30_260722_134743", "trpo_budgetslack_260721_181133"]
created: 2026-07-15T05:05:54.627769
updated: 2026-07-23T07:32:14.143051
sources: ["trpo_baseline_260714_192020", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Posttam encoder is alive and specialized (z-sweep) — exploration collapse is a converged optimum, not a dead encoder

encoder_tools.py sweep on posttam baseline trpo_baseline_260714_192020/model_4999.pt (28D priv-obs -> 9D softsign latent, 100pt/param). RESULT: encoder ALIVE and structured — every one of the 9 z dims responds strongly to some physics param (no dead/collapsed dim). Strongly ENCODED (max z range 0.8-1.19): Body Mass, Main Volume, Payload Mass, Main CoB Z, Main CoG Z, Ocean Current Z; z_1 specializes in Ocean Current Z (1.07)+Lin Vel W (0.83); z_4 is a broad generalist. Weakly encoded (<0.3): Joint Stiffness, Joint Damping, Thrust Coeff, Time Const Up, Water Density, Payload CoG Z, Lin Vel U/V.

IMPLICATION for the exploration-collapse question (perflb H2 verdict, diagnose-20260715-133249): the actor receives a RICH, specialized DR latent and achieves competent tracking (return ~215, att_rp 6.2) — so the collapsed exploration (entropy ~-7.8, noise_std at min_std floor) coexists with a functional DR-conditioned policy. This reads as a CONVERGED OPTIMUM (the policy learned a competent low-variance response to observed DR), NOT a learning-starving pathology. => P-A1 (actor-side exploration revive via min_std raise) is DEPRIORITIZED: forcing noise onto a competent converged policy risks the e3-style oscillation for unproven gain. The z-sweep is the necessity check the plan doc P-C1 called for; it argues AGAINST spending the P-A1 GPU slot before the tracking-quality track (P-B1). Artifact: train/encoder_analysis/sweep_heatmap.png.

---

## Merged from the_encoder_is_healthy_on_every_run_no_collapse_no_softsign_satu.md (2026-07-23T07:32:14.143051)

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


---

## Merged from the_encoder_is_healthy_and_slightly_more_active_latent_std_uncha.md (2026-07-23T07:32:14.143051)

# The encoder is healthy and slightly more active: latent std unchanged, grad flow

The encoder is healthy and slightly more active: latent std unchanged, grad flow UP (encoder_grad_norm +33.8%, enc_step +17.7%) -- releasing the settling barrier gave the encoder marginally more to learn, with no latent collapse. | tag                   | A5      | anchor  | delta% | |-----------------------|---------|---------|--------| | Encoder/z_std         | 0.4147  | 0.4000  | +3.7%  | | Policy/encoder_grad_norm | 0.0550 | 0.0411 | +33.8% | | Grad/enc_step         | 0.0016  | 0.0013  | +17.7% | | Encoder/z_mean        | -0.0289 | -0.0203 | -42.3% |

[EVIDENCE: TB last-200-iter means]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

The encoder is healthy and slightly more active: latent std unchanged, grad flow UP (encoder_grad_norm +33.8%, enc_step +17.7%) -- releasing the settling barrier gave the encoder marginally more to learn, with no latent collapse. | tag                   | A5      | anchor  | delta% | |-----------------------|---------|---------|--------| | Encoder/z_std         | 0.4147  | 0.4000  | +3.7%  | | Policy/encoder_grad_norm | 0.0550 | 0.0411 | +33.8% | | Grad/enc_step         | 0.0016  | 0.0013  | +17.7% | | Encoder/z_mean        | -0.0289 | -0.0203 | -42.3% |

[EVIDENCE: TB last-200-iter means]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
