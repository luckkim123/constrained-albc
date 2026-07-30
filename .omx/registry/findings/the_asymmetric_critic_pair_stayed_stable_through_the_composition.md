---
title: "The asymmetric critic pair stayed stable through the composition, and the cost-c"
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

# The asymmetric critic pair stayed stable through the composition, and the cost-c

The asymmetric critic pair stayed stable through the composition, and the cost-critic value did NOT inflate the way the band-only run recorded, which is evidence against the H2 mechanism operating through critic mis-valuation.

[EVIDENCE: `Loss/value_function` anchor 0.4516 -> E-int 0.4827 and `Loss/cost_value` anchor 0.7809 -> E-int 0.7510 (last-20 means; engine [TIER 3] Losses value 0.53 cost_val 0.72); B0c by contrast carried cost-critic value 0.77 -> 0.96 (+25%) as its watch item in diagnose-20260727-151917]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
