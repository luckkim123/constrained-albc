---
title: "The reward decomposition shows A2 slightly AHEAD of the anchor on every term, wi"
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

# The reward decomposition shows A2 slightly AHEAD of the anchor on every term, wi

The reward decomposition shows A2 slightly AHEAD of the anchor on every term, with the gain concentrated in `Reward/yaw_vel` — so nothing in the training objective registers the transient and robustness regressions the eval exposes.

[EVIDENCE: engine `[TIER 3] Rewards` final values, both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
