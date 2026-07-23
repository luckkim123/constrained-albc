---
title: "The training-side return loss (-5.0%) is modest relative to the eval collapse, a"
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

# The training-side return loss (-5.0%) is modest relative to the eval collapse, a

The training-side return loss (-5.0%) is modest relative to the eval collapse, and is split between the yaw tracking term (-12.3%) and the thruster penalty (-25.2%) — the policy pays more actuator cost for worse tracking.

[EVIDENCE: TB last-200-iter means, all 7 Reward/* tags present]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
