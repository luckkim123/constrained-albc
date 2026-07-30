---
title: "All twelve roll/pitch/att_norm `ss_error` comparisons moved in the improving dir"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# All twelve roll/pitch/att_norm `ss_error` comparisons moved in the improving dir

All twelve roll/pitch/att_norm `ss_error` comparisons moved in the improving direction and survival is saturated at every level, so the composition carries no floor-clearing nominal cost; an exhaustive scan of all 68 healthy cells (4 levels x roll/pitch/yaw x five fields, plus att_norm ss_error/ss_jitter) finds 13 worsened cells, every one below its screening floor.

[EVIDENCE: 12/12 roll/pitch/att_norm ss_error deltas negative in the table above, four clearing the 0.10 deg floor (none roll -0.1114, none att_norm -0.1052, soft att_norm -0.1027, hard att_norm -0.1139); survival_pct 100.0 for both runs at none/soft/medium/hard; yaw `ss_error` healthy 0.0062 vs anchor 0.0057 rad/s at none]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
