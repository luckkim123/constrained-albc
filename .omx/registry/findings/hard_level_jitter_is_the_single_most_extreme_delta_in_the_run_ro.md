---
title: "`hard`-level jitter is the single most extreme delta in the run (roll +225%, pit"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# `hard`-level jitter is the single most extreme delta in the run (roll +225%, pit

`hard`-level jitter is the single most extreme delta in the run (roll +225%, pitch +414%), indicating sustained oscillation rather than a DC offset — the policy is hunting because it cannot observe the velocity state it is reacting to.

[EVIDENCE: summary.json hard ss_jitter roll 0.670 vs 0.206, pitch 0.479 vs 0.093]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
