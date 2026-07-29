---
title: "E-ftc1's noise floor sits exactly on `min_std`, so exploration is floor-clamped "
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

# E-ftc1's noise floor sits exactly on `min_std`, so exploration is floor-clamped 

E-ftc1's noise floor sits exactly on `min_std`, so exploration is floor-clamped rather than freely chosen — the same engine [DIAGNOSIS] item 1 fires on both runs and is a family-level property, not a treatment effect.

[EVIDENCE: `Noise/std_min` 0.05000 (E-ftc1) vs 0.05555 (Arm A) against `min_std=0.05` from engine [CONFIG]; [DIAGNOSIS] 1 "Entropy collapse + low noise -> exploration dead" present in both]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
