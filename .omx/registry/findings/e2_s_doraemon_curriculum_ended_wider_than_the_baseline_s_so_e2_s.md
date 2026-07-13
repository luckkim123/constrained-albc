---
title: "e2's DORAEMON curriculum ended WIDER than the baseline's, so e2's `--doraemon-dr"
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

# e2's DORAEMON curriculum ended WIDER than the baseline's, so e2's `--doraemon-dr

e2's DORAEMON curriculum ended WIDER than the baseline's, so e2's `--doraemon-dr` hard/soft/medium exams are HARDER than the baseline's same-labelled exams; any equal-or-better e2 metric at those levels understates the true gain.

[EVIDENCE: curriculum_trajectory.json iter=4750 inertia_scale Beta-std e2 0.396 (a=1.555,b=1.530, near-uniform) vs baseline 0.268 (a=3.943,b=3.940); bounds [0.4,2.0]; eval.py:1074-1078 load_doraemon_dr makes each level run-relative]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
