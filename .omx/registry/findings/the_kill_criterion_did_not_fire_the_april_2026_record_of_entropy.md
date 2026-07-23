---
title: "The kill criterion did not fire: the April 2026 record of `entropy_coef=0` colla"
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

# The kill criterion did not fire: the April 2026 record of `entropy_coef=0` colla

The kill criterion did not fire: the April 2026 record of `entropy_coef=0` collapsing the run does not replicate in its CONSEQUENCE, because return went UP, not down.

[EVIDENCE: `Train/mean_reward` last-200 means — A2 276.83 vs anchor 272.05 (+1.8%); finals 277.68 vs 272.46; wiki `april_2026_entropy_collapse_campaign_...` records coef=0 -> noise_std 0.12 vs 0.55 (run 04-10)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
