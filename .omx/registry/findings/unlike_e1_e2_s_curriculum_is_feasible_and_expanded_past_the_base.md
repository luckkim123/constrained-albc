---
title: "Unlike e1, e2's curriculum is FEASIBLE and expanded past the baseline: mode 0 (n"
tags: ["auto-captured", "trpo_e2_biasobs_260713_173456"]
created: 2026-07-13T13:47:17.958008
updated: 2026-07-13T13:47:17.958008
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Unlike e1, e2's curriculum is FEASIBLE and expanded past the baseline: mode 0 (n

Unlike e1, e2's curriculum is FEASIBLE and expanded past the baseline: mode 0 (normal-widen), success 0.86 well above alpha 0.5, and it reached a wider inertia_scale distribution than baseline — this run trained (and was evaluated) on a harder DR than baseline.

[EVIDENCE: analyze_training.py TIER 2 DORAEMON doraemon_success_rate=0.86, DORAEMON/ess_ratio=0.77, mode=0.00 (vs e1 mode=-2 success=0.09); DORAEMON/kl_step accepting moves + DORAEMON/entropy_before rising (curriculum widening); curriculum_trajectory.json inertia_scale Beta-std 0.396 vs baseline 0.268]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
