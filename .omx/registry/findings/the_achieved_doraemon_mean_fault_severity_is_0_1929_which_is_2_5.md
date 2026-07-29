---
title: "The achieved `DORAEMON/mean/fault_severity` is 0.1929, which is 2.50x Arm A's 0."
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

# The achieved `DORAEMON/mean/fault_severity` is 0.1929, which is 2.50x Arm A's 0.

The achieved `DORAEMON/mean/fault_severity` is 0.1929, which is 2.50x Arm A's 0.0771 and clears the pre-registered 2x bite threshold of 0.1542 — the manipulation bit, so downstream metrics are readable as fault-exposure effects.

[EVIDENCE: `tb_final.py --window 200` `DORAEMON/mean/fault_severity` 0.19290 (E-ftc1) / 0.07710 (Arm A); engine [TIER 2] DORAEMON param table 0.1929 (19.3% of range) / 0.0771 (7.7%); `curriculum_trajectory.json` final update iter 4750 `Beta(1.2102, 5.0634)`]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
