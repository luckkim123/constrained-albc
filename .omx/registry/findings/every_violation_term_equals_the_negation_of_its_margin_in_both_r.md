---
title: "Every violation term equals the negation of its margin in both runs, i.e. all te"
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

# Every violation term equals the negation of its margin in both runs, i.e. all te

Every violation term equals the negation of its margin in both runs, i.e. all ten constraints sit in the slack regime with none violated at end of training.

[EVIDENCE: `analyze_training.py` [TIER 2] `viol` column: `Constraint/viol/thruster_util` -4.41 / -3.90, `Constraint/viol/rp_vel_settling` -9.54 / -9.71, `Constraint/viol/rp_rate` -6.33 / -6.63, `Constraint/viol/arm_torque` -7.38 / -7.67, `Constraint/viol/yaw_rate` -9.45 / -9.24, `Constraint/viol/arm_joint_vel` -1.98 / -1.88, `Constraint/viol/manipulability` -4.99 / -4.96, `Constraint/viol/attitude` -1.00 / -1.00, `Constraint/viol/joint1_pos` -1.00 / -1.00, `Constraint/viol/cumul_yaw` -1.00 / -1.00 (E-ftc1 / Arm A)]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
