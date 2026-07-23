---
title: "Exactly one constraint is binding (`thruster_util`) and A2 binds it LESS than th"
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Exactly one constraint is binding (`thruster_util`) and A2 binds it LESS than th

Exactly one constraint is binding (`thruster_util`) and A2 binds it LESS than the anchor, i.e. the low-noise policy leaves more actuator headroom — the same direction as its reward gain and the opposite direction from its eval regression.

[EVIDENCE: engine `[TIER 2] Constraints`, all 10 rows, both runs; `Constraint/margin/*` and `Constraint/viol/*`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
