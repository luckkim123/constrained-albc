---
title: "Pitch generalizes more gracefully than roll on both runs (smaller none->hard mul"
tags: ["auto-captured", "trpo_biasema_260715_142543"]
created: 2026-07-15T10:45:08.430019
updated: 2026-07-15T10:45:08.430019
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Pitch generalizes more gracefully than roll on both runs (smaller none->hard mul

Pitch generalizes more gracefully than roll on both runs (smaller none->hard multiplier), consistent with the reference-run finding that pitch is DC-bias+AC mixed while roll is DC-bias-dominated (wiki `roll_error_is_dc_bias_dominated_ss_jitter_ss_error_pitch_carries`).

[EVIDENCE: pitch none->hard: ref 0.273->0.532 (1.9x), P-B1 0.195->0.488 (2.5x) — both axes widen, roll more]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_biasema_260715_142543/analysis/diagnose-20260715-193800/report.md
