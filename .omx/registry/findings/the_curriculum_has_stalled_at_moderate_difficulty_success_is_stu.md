---
title: "The curriculum has stalled at moderate difficulty: success is stuck at 0.40 with"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-14T16:41:28.339995
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The curriculum has stalled at moderate difficulty: success is stuck at 0.40 with

The curriculum has stalled at moderate difficulty: success is stuck at 0.40 with a healthy ESS, but because entropy/noise have collapsed (see trpo) DORAEMON has no exploration headroom to expand difficulty — the env "ended" at a moderate level rather than being pushed harder.

[EVIDENCE: engine TIER 2 DORAEMON + TB final-window: success_rate 0.40 (mode -2.00), ess_ratio 0.414, entropy_before -29.24, kl_step 0.00048]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
