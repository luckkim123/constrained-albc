---
title: "The surrogate-loss doubling is not a health flag: att_rp/total reward are flat ("
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

# The surrogate-loss doubling is not a health flag: att_rp/total reward are flat (

The surrogate-loss doubling is not a health flag: att_rp/total reward are flat (+0.5/+0.6%), line-search success is 1.0 and KL matches, so the more-negative surrogate reflects the released rp_vel_settling barrier reshaping the advantage landscape at the margin, not a failing update -- and at |0.20| it is a small-base move like clip_fraction.

[EVIDENCE: TB Policy/surrogate_loss -0.2005 vs -0.1002 against Reward/total +0.6%, line_search_success 1.0, Loss/kl within 0.3%]
[CONFIDENCE: MED]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_budgetslack_260721_181133/analysis/diagnose-20260722-103723/report.md
