---
title: "All 10 constraints active with healthy complementary slackness (one binding, mos"
tags: ["auto-captured", "trpo_e1_latdr_260713_124923"]
created: 2026-07-13T10:08:21.544030
updated: 2026-07-13T10:08:21.544030
sources: ["experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# All 10 constraints active with healthy complementary slackness (one binding, mos

All 10 constraints active with healthy complementary slackness (one binding, most deeply slack); thruster_util is the binding constraint, matching the baseline's constraint ordering — the constraint layer is not the problem.

[EVIDENCE: analyze_training.py TIER 2 Constraint/margin thruster_util binding JC/dk 0.726, rp_vel_settling 0.522; Constraint/viol all negative; barrier_penalty -0.129 = ~2% of Reward/total]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/p7_tail/trpo_e1_latdr_260713_124923/analysis/diagnose-20260713-184751/report.md
