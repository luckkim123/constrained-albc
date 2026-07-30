---
title: "The single `barrier_penalty` spike that distinguishes this run from its referenc"
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

# The single `barrier_penalty` spike that distinguishes this run from its referenc

The single `barrier_penalty` spike that distinguishes this run from its references is a resume transient that healed, not a property of the composed configuration.

[EVIDENCE: the only `Constraint/barrier_penalty` value above 0.01 occurs at iteration 2431, 81 iterations after the 2350 resume point, at 0.1089 (anchor and B0c have zero such spikes across 5000 steps each); `Loss/value_function` reads 0.4659 at the resume step 2350, peaks at 1.9959 three steps later at 2353, and settles to a 0.5117 late-phase mean (last 500 steps), while `barrier_penalty` returns to -0.126 with no recurrence through iteration 4999]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
