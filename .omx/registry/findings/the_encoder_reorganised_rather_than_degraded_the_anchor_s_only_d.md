---
title: "The encoder REORGANISED rather than degraded: the anchor's only dead parameter, "
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

# The encoder REORGANISED rather than degraded: the anchor's only dead parameter, 

The encoder REORGANISED rather than degraded: the anchor's only dead parameter, `Joint Stiffness` (0/9 active, max range 0.0411), came alive under A4 (4/9, 0.1673). Freed capacity was redeployed onto a previously-ignored input — which is healthy encoder behaviour and further isolates the damage to the missing signal itself.

[EVIDENCE: `encoder_tools.py sweep` both runs, Joint Stiffness row]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
