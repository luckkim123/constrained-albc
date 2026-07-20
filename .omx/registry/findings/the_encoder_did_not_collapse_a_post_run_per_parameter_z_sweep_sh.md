---
title: "The encoder did not collapse: a post-run per-parameter z-sweep shows 8-9 of 9 la"
tags: ["auto-captured", "trpo_stepint400_260720_180208"]
created: 2026-07-20T17:13:19.523263
updated: 2026-07-20T17:13:19.523263
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The encoder did not collapse: a post-run per-parameter z-sweep shows 8-9 of 9 la

The encoder did not collapse: a post-run per-parameter z-sweep shows 8-9 of 9 latent dims active for the mass/buoyancy/geometry parameters that matter most, with the largest z ranges on Body Mass (1.250), Payload Mass (1.001) and Main CoB Z (1.005).

[EVIDENCE: `encoder_tools.py sweep` on `model_7999.pt` -> `train/encoder_analysis/sweep_heatmap.png`; active-dim counts at range>0.05]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_stepint400_260720_180208/analysis/diagnose-20260721-020253/report.md
