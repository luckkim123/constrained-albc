---
title: "The curriculum STALLED in the infeasible branch for the entire run and never rec"
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

# The curriculum STALLED in the infeasible branch for the entire run and never rec

The curriculum STALLED in the infeasible branch for the entire run and never recovered — this is the mechanism behind every symptom above.

[EVIDENCE: analyze_training.py TIER 2 DORAEMON mode=-2, doraemon_success_rate 0.09 (baseline peaked 0.594), DORAEMON/ess_ratio 0.10, DORAEMON/kl_step ~0 (no move accepted), DORAEMON/entropy_before flat; PELT changepoint iter 3411 = mean_reward + success_rate both down]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
