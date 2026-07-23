---
title: "The likeliest reason the two diverge is that April's configuration predates toda"
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

# The likeliest reason the two diverge is that April's configuration predates toda

The likeliest reason the two diverge is that April's configuration predates today's per-dim `min_std` floors, which would make the floors — not the bonus — what prevents the catastrophic version of this failure; no run in this report tests bonus-off with floors-off, so the attribution is inference rather than measurement.

[EVIDENCE: `min_std_per_dim` (0.1, 0.1, 0.05 x6) present in both runs' `config/agent.yaml:148-155`; wiki `april_2026_entropy_collapse_campaign_...` dates per-dim `min_std` to commit `b64c6e6` (04-13), i.e. AFTER the 04-10 coef=0 run it is being compared against]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
