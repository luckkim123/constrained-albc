---
title: "success_rate settled at 0.50, essentially exactly at alpha=0.5 (the designed DOR"
tags: ["auto-captured", "trpo_perflb200-moreiters_260715_195227"]
created: 2026-07-15T19:00:13.758977
updated: 2026-07-15T19:00:13.758977
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# success_rate settled at 0.50, essentially exactly at alpha=0.5 (the designed DOR

success_rate settled at 0.50, essentially exactly at alpha=0.5 (the designed DORAEMON equilibrium point per wiki `doraemon_alpha_is_a_feasibility_floor...`), not below it. This distinguishes the result from the documented over-widen-backfire failure mode (wiki `doraemon_over_widens_then_oscillates...`, whose own example ended with success 0.368 < alpha). `mode` stayed 0 throughout (no re-stall).

[EVIDENCE: engine deep output "success=doraemon_success_rate ... mode=..." line, P-A8 run]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
