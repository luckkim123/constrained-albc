---
title: "`eval.py static --doraemon-dr` anchors each DR level to the RUN'S OWN learned cu"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `eval.py static --doraemon-dr` anchors each DR level to the RUN'S OWN learned cu

`eval.py static --doraemon-dr` anchors each DR level to the RUN'S OWN learned curriculum, and e1's learned distribution is far narrower than the baseline's, so e1's hard/ood exams are milder — cross-run soft/medium/hard/ood numbers are not apples-to-apples.

[EVIDENCE: code eval.py:1074-1078 load_doraemon_dr(run_dir); constrained_albc/analysis/dr_config.py:206 "hard = mean +/- 2*std from run TB"; inertia_scale Beta-std end-of-run (curriculum_trajectory.json iter=4750) e1 0.111 vs baseline 0.268 (2.4x narrower)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
