---
title: "Entropy collapse with a floored `Policy/mean_noise_std` is a pre-existing plant-"
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

# Entropy collapse with a floored `Policy/mean_noise_std` is a pre-existing plant-

Entropy collapse with a floored `Policy/mean_noise_std` is a pre-existing plant-wide condition on this task rather than an E-int effect, so the engine DIAGNOSIS "exploration dead" item does not belong to the composition verdict.

[EVIDENCE: engine [TIER 1] reports entropy COLLAPSED and noise LOW on all three runs — `Policy/entropy` last-20 means anchor -8.931, B0c -8.804, E-int -8.952 with `Policy/mean_noise_std` 0.0884 / 0.0905 / 0.0881; the engine emits the identical DIAGNOSIS item 1 for each]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
