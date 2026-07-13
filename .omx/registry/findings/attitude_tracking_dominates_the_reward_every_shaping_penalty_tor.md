---
title: "Attitude tracking dominates the reward; every shaping penalty (torque/thruster/s"
tags: ["auto-captured", "trpo_baseline_260713_031325"]
created: 2026-07-12T23:48:37.357434
updated: 2026-07-13T03:07:41.018520
sources: ["experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# Attitude tracking dominates the reward; every shaping penalty (torque/thruster/s

Attitude tracking dominates the reward; every shaping penalty (torque/thruster/smoothness/bias) is ~1% of total, so no penalty term fights the objective. (7 terms, not 8: no lin_vel — attitude-only task.)

[EVIDENCE: TB Reward/* final-200 — att_rp 6.22 + yaw_vel 1.64 vs each penalty |x|<=0.042; Reward/total 7.74]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md

---

## Update (2026-07-13T03:07:41.018520)

Attitude tracking dominates the reward; every shaping penalty (torque/thruster/smoothness/bias) is ~1% of total, so no penalty term fights the objective. (7 terms, not 8: no lin_vel — attitude-only task.)

[EVIDENCE: TB Reward/* final-200 — att_rp 6.22 + yaw_vel 1.64 vs each penalty |x|<=0.042; Reward/total 7.74]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/baseline/trpo_baseline_260713_031325/analysis/diagnose-20260713-081707/report.md
