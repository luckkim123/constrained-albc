---
title: "Encoder latent statistics are unchanged between runs — the probe did not perturb"
tags: ["auto-captured", "trpo_perflb200_260715_023744"]
created: 2026-07-15T04:54:53.987453
updated: 2026-07-15T04:54:53.987453
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Encoder latent statistics are unchanged between runs — the probe did not perturb

Encoder latent statistics are unchanged between runs — the probe did not perturb the encoder.

[EVIDENCE: engine TIER1 `Encoder/z_std`=0.41 both; `Encoder/z_min`/`Encoder/z_max` (z_range) [-0.73,0.73]->[-0.74,0.74]; z_mean 0.02->0.03; `Policy/encoder_grad_norm`/`Grad/enc_step` not separately surfaced by the engine and no anomaly flagged]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200_260715_023744/analysis/diagnose-20260715-133249/report.md
