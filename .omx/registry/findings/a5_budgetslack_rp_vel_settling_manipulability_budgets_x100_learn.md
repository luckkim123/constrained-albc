---
title: "A5 budgetslack (rp_vel_settling + manipulability budgets x100): learner is anchor's twin, verdict CONTINGENT on seed floor"
tags: ["budgetslack", "constraint", "ipo", "seed-floor", "none-band", "albc", "teacher", "auto-captured", "trpo_budgetslack_260721_181133"]
created: 2026-07-22T01:57:47.552177
updated: 2026-07-23T07:32:14.143051
sources: ["diagnose-20260722-103723", "experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md"]
links: []
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# A5 budgetslack (rp_vel_settling + manipulability budgets x100): learner is anchor's twin, verdict CONTINGENT on seed floor

A5 `trpo_budgetslack_260721_181133` (branch exp/budget-slack-x100) multiplied two IPO budgets x100 (rp_vel_settling 0.20->20.0, manipulability 0.05->5.0), other 8 terms untouched. Anchor trpo_biasema_260715_142543 eval static_260715_192701.

RESULT: the learner is a near-perfect twin of the anchor on EVERY training-side axis -- Reward/att_rp +0.5%, Reward/total +0.6%, entropy +2.8%, Loss/value_function -9.0% (better), encoder healthy, DORAEMON 19 vs 18 expansions. But none-level tracking MOVED beyond the +/-5% band: roll ss_error 0.2509 vs 0.2149 = +16.8% (worse), pitch 0.1724 vs 0.1946 = -11.4% (better), yaw -56% (better), roll os_env_mean 26.35 vs 17.02 = +54.8%. A directional roll-for-pitch TRADE consistent with releasing the rp_vel_settling barrier.

VERDICT: CONTINGENT on the seed floor (seeds 30/31/32, seed_floor_dgx group). At single-seed resolution a +16.8% roll swing cannot be called signal vs noise -- that is exactly what the concurrent seed-floor measurement bounds. If floor >= ~15%, this move is inside seed noise => NULL (the release changed the constraint accounting but not the deployed policy). If floor < 5%, the release caused a real trade. The band's CONSTRAINT clause IS met (both relaxed guards deep-slack, binding stays thruster_util 0.843); the tracking clause is un-adjudicable at n=1. DO NOT close before the floor lands. (analysis diagnose-20260722-103723 report.md verdict; eval static_260721_230512)

---

## Merged from the_intervention_did_what_it_was_designed_to_do_and_more_than_th.md (2026-07-23T07:32:14.143051)

# The intervention did what it was designed to do AND more than the "both dormant"

The intervention did what it was designed to do AND more than the "both dormant" premise assumed: `manipulability` was already dormant (J_C/d_k 0.034) but `rp_vel_settling` was the 2nd-MOST-ACTIVE guard in the anchor (0.549, above rp_rate 0.409). The x100 budgets pushed both to deep slack, so one active + one dormant barrier were released. The divergence from the prior "both dormant" wiki claim is a metric mismatch, not a contradiction: that page ranked by RAW min-margin threshold, whereas J_C/d_k normalizes by the discounted budget d_k -- normalization is what surfaces rp_vel_settling as active (the workspace's own `constraint_margin_must_be_normalized` rule). | constraint      | anchor J_C/d_k | A5 J_C/d_k | note                    | |-----------------|----------------|------------|-------------------------| | thruster_util   | 0.846          | 0.843      | binding, unchanged      | | rp_vel_settling | 0.549          | -98.410    | released (was 2nd-most active) | | rp_rate         | 0.409          | 0.456      | untouched budget        | | arm_torque      | --             | 0.082      | untouched, slack        | | yaw_rate        | --             | 0.023      | untouched, slack        | | arm_joint_vel   | --             | 0.007      | untouched, slack        | | attitude        | --             | -0.000     | gated-inactive          | | cumul_yaw       | --             | -0.000     | gated-inactive          | | joint1_pos      | --             | -0.000     | gated-inactive          | | manipulability  | 0.034          | -98.716    | released (was dormant)  |

[EVIDENCE: engine TIER 2 J_C/d_k, anchor vs A5]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

The intervention did what it was designed to do AND more than the "both dormant" premise assumed: `manipulability` was already dormant (J_C/d_k 0.034) but `rp_vel_settling` was the 2nd-MOST-ACTIVE guard in the anchor (0.549, above rp_rate 0.409). The x100 budgets pushed both to deep slack, so one active + one dormant barrier were released. The divergence from the prior "both dormant" wiki claim is a metric mismatch, not a contradiction: that page ranked by RAW min-margin threshold, whereas J_C/d_k normalizes by the discounted budget d_k -- normalization is what surfaces rp_vel_settling as active (the workspace's own `constraint_margin_must_be_normalized` rule). | constraint      | anchor J_C/d_k | A5 J_C/d_k | note                    | |-----------------|----------------|------------|-------------------------| | thruster_util   | 0.846          | 0.843      | binding, unchanged      | | rp_vel_settling | 0.549          | -98.410    | released (was 2nd-most active) | | rp_rate         | 0.409          | 0.456      | untouched budget        | | arm_torque      | --             | 0.082      | untouched, slack        | | yaw_rate        | --             | 0.023      | untouched, slack        | | arm_joint_vel   | --             | 0.007      | untouched, slack        | | attitude        | --             | -0.000     | gated-inactive          | | cumul_yaw       | --             | -0.000     | gated-inactive          | | joint1_pos      | --             | -0.000     | gated-inactive          | | manipulability  | 0.034          | -98.716    | released (was dormant)  |

[EVIDENCE: engine TIER 2 J_C/d_k, anchor vs A5]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md


---

## Merged from the_move_is_a_directional_trade_not_a_uniform_regression_roll_st.md (2026-07-23T07:32:14.143051)

# The move is a directional TRADE, not a uniform regression: roll steady-state deg

The move is a directional TRADE, not a uniform regression: roll steady-state degrades while pitch and yaw steady-state improve -- the signature of releasing a roll/pitch-coupled settling barrier, not of a globally worse policy.

[EVIDENCE: table above -- roll ss +16.8% against pitch -11.4% / yaw -56.0%]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md

---

## Update (2026-07-23T02:21:27.244561)

The move is a directional TRADE, not a uniform regression: roll steady-state degrades while pitch and yaw steady-state improve -- the signature of releasing a roll/pitch-coupled settling barrier, not of a globally worse policy.

[EVIDENCE: table above -- roll ss +16.8% against pitch -11.4% / yaw -56.0%]
[CONFIDENCE: MED]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
