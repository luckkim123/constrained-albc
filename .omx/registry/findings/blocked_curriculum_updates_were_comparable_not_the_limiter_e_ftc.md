---
title: "Blocked curriculum updates were comparable, not the limiter — E-ftc1 lost 3 of 2"
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

# Blocked curriculum updates were comparable, not the limiter — E-ftc1 lost 3 of 2

Blocked curriculum updates were comparable, not the limiter — E-ftc1 lost 3 of 20 against Arm A's 2 of 20, and one of the three is a structural block both runs share.

[EVIDENCE: `curriculum_trajectory.json` consecutive-identical `(a, b)` detection; E-ftc1 blocked at iters 250, 2000, 2250; Arm A at iters 250, 4500; `grep -c 'Entropy opt rejected'` on E-ftc1 stdout returns 2, matching the two mid-run blocks (13:14:10 and 13:31:48), while the iter-250 block appears in both runs and is therefore structural]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
