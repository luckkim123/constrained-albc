---
title: "The training-log diagnostic engine cannot diagnose this run type, reproducing th"
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

# The training-log diagnostic engine cannot diagnose this run type, reproducing th

The training-log diagnostic engine cannot diagnose this run type, reproducing the recorded gap exactly.

[EVIDENCE: `/isaac-sim/python.sh .omx/profile/analyze_training.py <run> --tier 3 --deep` returns `STATUS: HEALTHY / iters=0 / last_step=0` on a run with 1000 logged samples per tag, emitting no DIAGNOSIS, changepoint, plateau or regime line — it cannot resolve the iteration axis under the `student/` namespace]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
