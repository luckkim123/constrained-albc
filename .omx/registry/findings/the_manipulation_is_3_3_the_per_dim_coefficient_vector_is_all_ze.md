---
title: "The manipulation is 3/3 — the per-dim coefficient vector is all-zero in the run'"
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

# The manipulation is 3/3 — the per-dim coefficient vector is all-zero in the run'

The manipulation is 3/3 — the per-dim coefficient vector is all-zero in the run's frozen config, the code takes the per-dim branch (making the scalar `entropy_coef=0.003` dead), and every other sigma-relevant knob is identical to the anchor.

[EVIDENCE: `config/agent.yaml:136-155` both runs; `constraint_trpo.py:107,490,497`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_entcoefzero_260721_014731/analysis/diagnose-20260721-065341/report.md
