---
title: "Posttam encoder is alive and specialized (z-sweep) — exploration collapse is a converged optimum, not a dead encoder"
tags: ["encoder", "z-sweep", "exploration", "doraemon", "p-a1"]
created: 2026-07-15T05:05:54.627769
updated: 2026-07-15T05:05:54.627769
sources: ["trpo_baseline_260714_192020"]
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
