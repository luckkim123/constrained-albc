---
title: "Eval decision floors are the binding standard for student-arm comparisons (0.1 deg / 15 envs)"
tags: ["eval", "decision-floor", "screening", "student", "distillation", "albc", "methodology"]
created: 2026-07-29T07:25:58.151005
updated: 2026-07-29T07:25:58.151005
sources: ["diagnose-20260729-161459"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Eval decision floors are the binding standard for student-arm comparisons (0.1 deg / 15 envs)

Every static eval summary.json carries `decision_floors` = {ss_error: 0.1, os_env_mean: 10.0, n_gt20: 15.0} with `decision_floors_protocol` = 'screening n=1 paired same-machine; |delta| below floor = noise'. Apply it BEFORE reading any inter-arm delta as an effect.

Measured consequence in campaign student_distill_eint (analysis diagnose-20260729-161459 on trpo_sdeint_b4b_beta05_s30_260729_153436, section 'tracking'):
- B4b vs A0 att_norm ss_error deltas = 0.0245 / 0.0316 / 0.0570 / 0.0776 deg (none/soft/medium/hard). ALL below the 0.1 deg floor -> the arm is a null result at eval level, despite a 10.5% relative 'win' at hard.
- A0g vs A0 deltas = 0.1384 / 0.1233 / 0.0929 / 0.0916 deg. Only none and soft clear the floor, so the recorded 'GRU better at all four levels' is decision-grade at TWO of four.
- roll n_gt20 spans 0.00-7.00 envs across all four runs against a 15-env floor. At 64 envs this metric detects catastrophe only, never degradation, so the recorded A0g 'tail regression' (7.00 vs A0's 5.67) is sub-floor and must not be cited as a real cost.

Practical rule: a relative percentage on a sub-0.1-deg absolute difference is not evidence. Convert to the axis unit and compare against the floor first (repo rule: sign consistency is not magnitude). No floor is declared for ss_error_std / CV, so dispersion differences cannot be adjudicated at n=1 under the current protocol -- that gap is itself worth closing.
