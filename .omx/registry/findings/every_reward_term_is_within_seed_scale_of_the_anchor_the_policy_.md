---
title: "Every reward term is within seed-scale of the anchor -- the policy is being paid"
tags: ["auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:58:11.799085
updated: 2026-07-22T01:58:11.799085
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Every reward term is within seed-scale of the anchor -- the policy is being paid

Every reward term is within seed-scale of the anchor -- the policy is being paid essentially the same for essentially the same behaviour, so nothing in the reward accounting explains the `none` roll move. | term       | A5      | anchor  | delta% | |------------|---------|---------|--------| | att_rp     | 7.0986  | 7.0624  | +0.5%  | | total      | 9.1162  | 9.0654  | +0.6%  | | yaw_vel    | 2.1063  | 2.0927  | +0.6%  | | thruster   | -0.0302 | -0.0282 | -6.8%  | | smoothness | -0.0158 | -0.0154 | -2.9%  | | torque     | -0.0383 | -0.0414 | +7.6%  | | bias       | -0.0045 | -0.0048 | +5.9%  |

[EVIDENCE: TB last-200-iter means, all 7 Reward/* tags present]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
