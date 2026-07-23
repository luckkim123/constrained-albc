---
title: "The DR curriculum was IDENTICAL in the two runs — 18 updates at iters 500..4750 "
tags: ["auto-captured"]
created: 2026-07-21T10:26:11.609658
updated: 2026-07-21T10:26:11.609658
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The DR curriculum was IDENTICAL in the two runs — 18 updates at iters 500..4750 

The DR curriculum was IDENTICAL in the two runs — 18 updates at iters 500..4750 in steps of 250, every one taking exactly the 0.12 KL cap, ending at numerically identical Beta parameters (max elementwise difference 5.0e-06 on `dist_a`, 4.7e-05 on `dist_b`).

[EVIDENCE: `doraemon_state.pt` dist_a/dist_b compared elementwise with np.allclose = True; TB DORAEMON/kl_step nonzero at 18 identical iterations with value 0.12 in both runs]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_minstdthr008_260721_064149/analysis/diagnose-20260721-164331/report.md
