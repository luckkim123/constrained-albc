---
title: "Value function loss (Loss/value_function) and cost-value loss (Loss/cost_value) "
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

# Value function loss (Loss/value_function) and cost-value loss (Loss/cost_value) 

Value function loss (Loss/value_function) and cost-value loss (Loss/cost_value) are essentially unchanged (value 1.18->1.17, cost_val 0.92->0.93) — the critic tracks the harder-DR return distribution about as well as it tracked the original one, no degradation in critic fit quality.

[EVIDENCE: engine deep output "value=... cost_val=... kl=..." line — value=Loss/value_function, cost_val=Loss/cost_value]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_perflb200-moreiters_260715_195227/analysis/diagnose-20260716-035505/report.md
