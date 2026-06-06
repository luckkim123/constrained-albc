---
title: "dr-harder: reward decomposition confirms eval trades on the training side"
tags: ["dr-harder", "reward-decomposition", "att_rp", "training-dynamics", "kl_ub", "entropy-collapse"]
created: 2026-06-06T08:49:39.135536
updated: 2026-06-06T08:49:39.135536
sources: ["diagnose-20260606-173330"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# dr-harder: reward decomposition confirms eval trades on the training side

When diagnosing a dr-harder treatment, the Reward/* decomposition (metrics.yaml vocabulary) confirms the eval attitude-vs-translation trade ON THE TRAINING SIDE, independent of eval summary.json. Verified 3-way (analysis diagnose-20260606-173330, group rsl_rl/albc_trpo_teacher/dr_harder): teacher att_rp=5.38 lin_vel=1.87; E1(kl_ub 0.12) att_rp DROPPED to 4.50 (-16%) + lin_vel up 1.92 = the kl_ub att-for-trans trade visible in training reward, not just eval; E2(ocean nominal 0.3) att_rp KEPT 5.36 + lin_vel HIGHEST 2.29 but Policy/entropy COLLAPSED -0.633 (teacher 0.289) at the HIGHEST total reward 8.55 = overfit. RULE for this workspace: att_rp drop => attitude regression is real (E1); att_rp kept + entropy collapse + highest reward => overfit to narrowed dist (E2). All TRPO/critic/constraint health stayed in band across all 3 (line_search 1.0, kl 0.005, cost_value converged 0.98-1.19, all 4 constraint margins satisfied/inert) -> DR is the only live lever, constraints cannot fix attitude. ess_ratio discriminates the two knobs: E1 0.640 (kl_ub 2x lowers sample efficiency) vs E2 0.872 (center-shift keeps it, teacher 0.875).
