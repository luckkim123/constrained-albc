---
title: "Survival is perfect at none/soft/medium and drops to 96.875% at hard, where two "
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

# Survival is perfect at none/soft/medium and drops to 96.875% at hard, where two 

Survival is perfect at none/soft/medium and drops to 96.875% at hard, where two envs terminate that the teacher carries to the end.

[EVIDENCE: data_hard.npz `terminated` / `time_to_failure`; teacher dead_envs = [] (0/64), student dead_envs = [19, 39] at t = 13.3 s and 22.3 s]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_c3_gruselect_s30_260804_124951/analysis/diagnose-20260804-132500/report.md
