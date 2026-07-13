---
title: "The encoder latent is alive and bounded (not collapsed to a constant), so the de"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The encoder latent is alive and bounded (not collapsed to a constant), so the de

The encoder latent is alive and bounded (not collapsed to a constant), so the delay did not break representation learning — but whether the actor USES the latent is not established here.

[EVIDENCE: analyze_training.py TIER 1 Encoder/z_std 0.42, Encoder/z_min -0.72, Encoder/z_max 0.76, z_mean -0.01; z aggregates only rule out collapse, per rule 03 a "latent is used" claim needs encoder_tools.py sweep (not run for this probe)]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
