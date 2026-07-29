---
title: "The within-run m4-dead penalty is 2.9x-5.5x larger for E-ftc1 at every DR level,"
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

# The within-run m4-dead penalty is 2.9x-5.5x larger for E-ftc1 at every DR level,

The within-run m4-dead penalty is 2.9x-5.5x larger for E-ftc1 at every DR level, and every cell clears the decision floor in both runs — the severity head start made fault rejection worse, not better.

[EVIDENCE: `compare.py paired` with `--bite fault_thruster_4`, delta = m4-dead minus healthy, att_norm `ss_error` (deg)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
