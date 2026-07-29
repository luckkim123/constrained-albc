---
title: "`thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS "
tags: ["auto-captured", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-29T08:24:32.720137
updated: 2026-07-29T08:24:32.720137
sources: ["experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# `thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS 

`thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS budget-stressed than Arm A, so the proposal's stated hazard (severity pushing an already-elevated budget into binding) did not materialize.

[EVIDENCE: `analyze_training.py` [TIER 2] Constraints, J_C/d_k; `-> binding (max JC/dk): thruster_util (0.890)` for E-ftc1 and `(0.902)` for Arm A]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
