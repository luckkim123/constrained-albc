---
title: "Widening did not rescue the hard-DR control regression, it deepened it: hard `at"
tags: ["auto-captured"]
created: 2026-08-03T15:00:28.482580
updated: 2026-08-03T15:00:28.482580
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Widening did not rescue the hard-DR control regression, it deepened it: hard `at

Widening did not rescue the hard-DR control regression, it deepened it: hard `att_norm ss_error` nearly doubles again from B2's 0.6975 to 1.3198, a +0.6223 deg move against a 0.1 deg floor, and it is the only DR level whose change clears that floor.

[EVIDENCE: `summary.json */att_norm/ss_error` in `static_260803_220328` vs `static_260803_233436`; floor from `summary.json decision_floors.ss_error`]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_student/student_distill_eint/trpo_sdeint_b2wide_gru256_s30_260803_231320/analysis/diagnose-20260803-235022/report.md
