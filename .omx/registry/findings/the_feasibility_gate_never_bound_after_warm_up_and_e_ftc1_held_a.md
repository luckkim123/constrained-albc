---
title: "The feasibility gate never bound after warm-up, and E-ftc1 held a HIGHER success"
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

# The feasibility gate never bound after warm-up, and E-ftc1 held a HIGHER success

The feasibility gate never bound after warm-up, and E-ftc1 held a HIGHER success rate than Arm A while training at 2.5x the severity — so the H2 secondary trigger (success falling to the alpha floor with mode at -2) did not fire.

[EVIDENCE: `DORAEMON/success_rate` and `DORAEMON/mode` per-update series]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
