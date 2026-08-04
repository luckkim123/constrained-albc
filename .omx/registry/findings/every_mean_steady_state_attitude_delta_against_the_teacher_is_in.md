---
title: "Every mean steady-state attitude delta against the teacher is inside env-draw sa"
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

# Every mean steady-state attitude delta against the teacher is inside env-draw sa

Every mean steady-state attitude delta against the teacher is inside env-draw sampling noise, at every DR level and on every attitude axis.

[EVIDENCE: summary.json, both evals; SE(delta) = sqrt((std_t^2 + std_s^2)/64), n=64 envs — |d|/SE ranges 0.11 (none pitch) to 1.43 (none roll), every one below 2]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
