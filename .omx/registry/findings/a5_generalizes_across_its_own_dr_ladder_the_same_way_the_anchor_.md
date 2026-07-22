---
title: "A5 generalizes across its own DR ladder the same way the anchor family does: ste"
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

# A5 generalizes across its own DR ladder the same way the anchor family does: ste

A5 generalizes across its own DR ladder the same way the anchor family does: steady-state error and per-env spread both grow monotonically none->hard, with no level showing an anomalous break -- the intervention did not change the OOD-degradation shape, only shifted the none anchor point. | level  | roll ss | roll CV | pitch ss | pitch CV | |--------|---------|---------|----------|----------| | none   | 0.2509  | 13%     | 0.1724   | 6%       | | soft   | 0.2749  | 41%     | 0.1936   | 17%      | | medium | 0.4146  | 101%    | 0.2389   | 54%      | | hard   | 1.1419  | 257%    | 0.5699   | 280%     |

[EVIDENCE: A5 summary.json, roll/pitch ss_error and CV per level]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
