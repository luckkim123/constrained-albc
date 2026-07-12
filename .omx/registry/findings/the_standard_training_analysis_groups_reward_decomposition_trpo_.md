---
title: "The standard training-analysis groups (reward decomposition, TRPO line-search/en"
tags: ["auto-captured", "trpo_main_teacher_260525_232805"]
created: 2026-07-12T18:26:43.465984
updated: 2026-07-12T18:26:43.465984
sources: ["experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The standard training-analysis groups (reward decomposition, TRPO line-search/en

The standard training-analysis groups (reward decomposition, TRPO line-search/entropy, critic loss, encoder z-sweep, DORAEMON curriculum) are not applicable — this is a flat-target eval of a fixed checkpoint, not a training run, so no training curve exists to diagnose.

[EVIDENCE: this is an eval (eval.py static), which writes data_<level>.npz not TB training logs; the profile's analyze_training.py engine operates on training curves that this run does not produce]
[CONFIDENCE: HIGH]

source report: experiments/legacy/rsl_rl/albc_trpo_teacher/dr_harder_e1e4_campaign/trpo_main_teacher_260525_232805/analysis/diagnose-20260713-031533/report.md
