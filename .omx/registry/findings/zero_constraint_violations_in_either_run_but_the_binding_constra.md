---
title: "Zero constraint violations in either run, but the binding constraint tightened s"
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

# Zero constraint violations in either run, but the binding constraint tightened s

Zero constraint violations in either run, but the binding constraint tightened sharply: `thruster_util` margin fell from 6.14 to 2.77 (-55%) while its J_C/d_k rose to 0.931. A4's policy is spending far more of its actuator budget to achieve worse tracking.

[EVIDENCE: `analyze_training.py` TIER 2 both runs; all `viol` entries negative]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
