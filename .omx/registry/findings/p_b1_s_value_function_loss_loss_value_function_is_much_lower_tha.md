---
title: "P-B1's value function loss (Loss/value_function) is much lower than the referenc"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-16T07:19:42.517477
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# P-B1's value function loss (Loss/value_function) is much lower than the referenc

P-B1's value function loss (Loss/value_function) is much lower than the reference's (0.38 vs 0.96); cost-value loss (Loss/cost_value) is similar (0.82 vs 0.79). Lower value loss is consistent with a return distribution the critic finds easier to fit — plausibly because bias_ema obs removes an unobservable source of return variance.

[EVIDENCE: engine deep output "value=... cost_val=... kl=..." line — value=Loss/value_function, cost_val=Loss/cost_value]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md

---

## Update (2026-07-16T07:19:42.517477)

P-B1's value function loss (Loss/value_function) is much lower than the reference's (0.38 vs 0.96); cost-value loss (Loss/cost_value) is similar (0.82 vs 0.79). Lower value loss is consistent with a return distribution the critic finds easier to fit — plausibly because bias_ema obs removes an unobservable source of return variance.

[EVIDENCE: engine deep output "value=... cost_val=... kl=..." line — value=Loss/value_function, cost_val=Loss/cost_value]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
