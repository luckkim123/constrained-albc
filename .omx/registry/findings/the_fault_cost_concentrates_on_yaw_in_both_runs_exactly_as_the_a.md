---
title: "The fault cost concentrates on yaw in both runs, exactly as the authority analys"
tags: ["auto-captured", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-29T08:24:32.720137
updated: 2026-07-29T12:20:47.836515
sources: ["experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The fault cost concentrates on yaw in both runs, exactly as the authority analys

The fault cost concentrates on yaw in both runs, exactly as the authority analysis predicts, and E-ftc1 is the only run whose yaw `n_gt20` delta clears the floor.

[EVIDENCE: `compare.py paired` yaw deltas; wiki `ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti` (m4 dead halves the pure-yaw ceiling 23.0 -> 11.5 N.m, per-thruster peak utilization x2.00)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

The fault cost concentrates on yaw in both runs, exactly as the authority analysis predicts, and E-ftc1 is the only run whose yaw `n_gt20` delta clears the floor.

[EVIDENCE: `compare.py paired` yaw deltas; wiki `ftc_investigation_2026_07_25_m4_loss_halves_pure_yaw_ceiling_uti` (m4 dead halves the pure-yaw ceiling 23.0 -> 11.5 N.m, per-thruster peak utilization x2.00)]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
