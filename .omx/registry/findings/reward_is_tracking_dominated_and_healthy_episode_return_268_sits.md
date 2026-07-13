---
title: "Reward is tracking-dominated and healthy; episode return 268 sits ABOVE performa"
tags: ["auto-captured", "trpo_e2_biasobs_260713_173456"]
created: 2026-07-13T13:47:17.958008
updated: 2026-07-13T13:47:17.958008
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Reward is tracking-dominated and healthy; episode return 268 sits ABOVE performa

Reward is tracking-dominated and healthy; episode return 268 sits ABOVE performance_lb 250, so the curriculum stays feasible (the mechanism that failed in e1 is absent here).

[EVIDENCE: analyze_training.py TIER 1 reward=268.27, ep_len=1419; TIER 3 Reward att_rp 7.05 + yaw_vel 2.04 vs penalties |x|<=0.04, total 8.98; bias term -0.01 (the penalized bias_ema, now observable); [TRENDS] plateau-since-5%, cv=0.010]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e2_biasobs_260713_173456/analysis/diagnose-20260713-223534/report.md
