---
title: "A5 budgetslack (rp_vel_settling + manipulability budgets x100): learner is anchor's twin, verdict CONTINGENT on seed floor"
tags: ["budgetslack", "constraint", "ipo", "seed-floor", "none-band", "albc", "teacher"]
created: 2026-07-22T01:57:47.552177
updated: 2026-07-22T01:57:47.552177
sources: ["diagnose-20260722-103723"]
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
