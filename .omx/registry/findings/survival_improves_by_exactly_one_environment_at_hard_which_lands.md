---
title: "Survival improves by exactly one environment at hard, which lands just under the"
tags: ["auto-captured", "trpo_sdobs76_x1_tailsplit_s30_260804_151400"]
created: 2026-08-04T07:04:05.217247
updated: 2026-08-04T07:04:05.217247
sources: ["experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Survival improves by exactly one environment at hard, which lands just under the

Survival improves by exactly one environment at hard, which lands just under the floor.

[EVIDENCE: `summary.json` `survival_pct` 96.875 -> 98.438 at hard (+1.562 pp against a 1.6 pp floor), 100.000 at none/soft/medium in both runs; `data_hard.npz` `time_to_failure` names the failing envs — baseline env 43 at 17.76 s and env 45 at 20.40 s, X1 env 43 only at 17.54 s]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_student/student_distill_obs76/trpo_sdobs76_x1_tailsplit_s30_260804_151400/analysis/diagnose-20260804-154122/report.md
