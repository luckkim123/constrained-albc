---
title: "The pacing diagnosis holds: the trust region, not feasibility, set the expansion"
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

# The pacing diagnosis holds: the trust region, not feasibility, set the expansion

The pacing diagnosis holds: the trust region, not feasibility, set the expansion rate — every executed update spent the full KL budget.

[EVIDENCE: `DORAEMON/kl_step` nonzero series, E-ftc1 16/16 executed updates at the 0.12 cap, Arm A 17/17; the three values reading 0.11999000608921051 (iters 500/750/1000) are bit-identical in BOTH runs, i.e. a float32 artifact, not a treatment effect]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
