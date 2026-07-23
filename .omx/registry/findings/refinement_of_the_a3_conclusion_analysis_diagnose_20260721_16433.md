---
title: "REFINEMENT of the A3 conclusion (analysis diagnose-20260721-164331): expansion S"
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

# REFINEMENT of the A3 conclusion (analysis diagnose-20260721-164331): expansion S

REFINEMENT of the A3 conclusion (analysis diagnose-20260721-164331): expansion STEP SIZE is cap-bound (every update in every run so far lands exactly on kl_ub=0.12), but the NUMBER of expansions is success-GATED. A3 and its anchor happened to gate identically (18/18), which made their boxes identical; A4 shows the gate can and does diverge. "Schedule-bound, not success-bound" is therefore true of the step size only, and must not be read as a guarantee that two runs share a DR box.

[EVIDENCE: A3 18 updates / anchor 18 updates / A4 19 updates, all at 0.12; A4 DORAEMON/success_rate final 0.6947 vs anchor 0.8773]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_privslim24d_260721_114717/analysis/diagnose-20260721-190151/report.md
