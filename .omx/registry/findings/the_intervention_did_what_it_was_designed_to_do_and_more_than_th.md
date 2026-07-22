---
title: "The intervention did what it was designed to do AND more than the \"both dormant\""
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

# The intervention did what it was designed to do AND more than the "both dormant"

The intervention did what it was designed to do AND more than the "both dormant" premise assumed: `manipulability` was already dormant (J_C/d_k 0.034) but `rp_vel_settling` was the 2nd-MOST-ACTIVE guard in the anchor (0.549, above rp_rate 0.409). The x100 budgets pushed both to deep slack, so one active + one dormant barrier were released. The divergence from the prior "both dormant" wiki claim is a metric mismatch, not a contradiction: that page ranked by RAW min-margin threshold, whereas J_C/d_k normalizes by the discounted budget d_k -- normalization is what surfaces rp_vel_settling as active (the workspace's own `constraint_margin_must_be_normalized` rule). | constraint      | anchor J_C/d_k | A5 J_C/d_k | note                    | |-----------------|----------------|------------|-------------------------| | thruster_util   | 0.846          | 0.843      | binding, unchanged      | | rp_vel_settling | 0.549          | -98.410    | released (was 2nd-most active) | | rp_rate         | 0.409          | 0.456      | untouched budget        | | arm_torque      | --             | 0.082      | untouched, slack        | | yaw_rate        | --             | 0.023      | untouched, slack        | | arm_joint_vel   | --             | 0.007      | untouched, slack        | | attitude        | --             | -0.000     | gated-inactive          | | cumul_yaw       | --             | -0.000     | gated-inactive          | | joint1_pos      | --             | -0.000     | gated-inactive          | | manipulability  | 0.034          | -98.716    | released (was dormant)  |

[EVIDENCE: engine TIER 2 J_C/d_k, anchor vs A5]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
