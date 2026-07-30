---
title: "The `decision_floors` block remains field-keyed while units are axis-keyed, so y"
tags: ["auto-captured"]
created: 2026-07-29T12:20:47.836515
updated: 2026-07-29T12:20:47.836515
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The `decision_floors` block remains field-keyed while units are axis-keyed, so y

The `decision_floors` block remains field-keyed while units are axis-keyed, so yaw is still unscreened at any usable resolution.

[EVIDENCE: `decision_floors.ss_error = 0.1` applied through `units.field_units.ss_error = "axis"` yields 0.1 rad/s on yaw against B1b values of 0.0049-0.0082 rad/s]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b1_lam4_s30_260729_170008/analysis/diagnose-20260729-172500/report.md
