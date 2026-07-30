---
title: "The composed configuration is sub-additive on the shared actuation budget: the b"
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

# The composed configuration is sub-additive on the shared actuation budget: the b

The composed configuration is sub-additive on the shared actuation budget: the binding constraint `thruster_util` lands at J_C/d_k 0.821, BELOW both single-change runs and far below the 0.950 exact-additivity prediction, so the band and fault DR do not compete for actuation headroom as H2 proposed.

[EVIDENCE: engine [TIER 2] Constraints binding line per run — anchor 0.805, B0c 0.853 (band only), FaultDR Arm A 0.902 (fault only), E-int 0.821 with `Constraint/margin/thruster_util` 7.77 and `Constraint/viol/thruster_util` -7.77; exact additivity 0.805 + 0.048 + 0.097 = 0.950 per proposal line 136]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md
