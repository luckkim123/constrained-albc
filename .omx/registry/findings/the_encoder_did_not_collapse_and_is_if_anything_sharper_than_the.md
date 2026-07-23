---
title: "The encoder did not collapse and is if anything sharper than the lineage: a post"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The encoder did not collapse and is if anything sharper than the lineage: a post

The encoder did not collapse and is if anything sharper than the lineage: a post-run per-parameter z-sweep on `model_4999.pt` gives 9 of 9 latent dims active on the mass/volume/geometry parameters that matter most, with the largest z ranges on Main Volume (1.309), Body Mass (1.301) and Payload Mass (1.266).

[EVIDENCE: `encoder_tools.py sweep --checkpoint .../train/model_4999.pt` -> `train/encoder_analysis/sweep_heatmap.png`; active-dim counts at z range > 0.05, 28 parameters x 100 points, latent dim 9]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
