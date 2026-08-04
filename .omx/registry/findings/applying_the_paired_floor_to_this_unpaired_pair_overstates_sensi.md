---
title: "Applying the paired floor to this unpaired pair overstates sensitivity by roughl"
tags: ["auto-captured", "trpo_sdobs76_c3_gruselect_s30_260804_124951"]
created: 2026-08-04T04:31:12.085504
updated: 2026-08-04T04:31:12.085504
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Applying the paired floor to this unpaired pair overstates sensitivity by roughl

Applying the paired floor to this unpaired pair overstates sensitivity by roughly 3x at hard, which is exactly where the report's headline sits.

[EVIDENCE: floors `{ss_error: 0.10 deg}` vs SE(delta) = sqrt((std_t^2+std_s^2)/64) from summary.json — hard att_norm 0.2976 deg, hard roll 0.2790 deg, and none roll (the one genuinely paired level) 0.0696 deg]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
