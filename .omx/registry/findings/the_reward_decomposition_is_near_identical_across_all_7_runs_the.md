---
title: "The reward decomposition is near-identical across all 7 runs; the plant fix did "
tags: ["auto-captured", "trpo_buoyanchor_s30_260722_134743"]
created: 2026-07-23T04:54:21.766685
updated: 2026-07-23T04:54:21.766685
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The reward decomposition is near-identical across all 7 runs; the plant fix did 

The reward decomposition is near-identical across all 7 runs; the plant fix did not change what the policy optimises, only the plant it optimises against. | run | att_rp | yaw_vel | bias | smoothness | thruster | torque | total | |:--|--:|--:|--:|--:|--:|--:|--:| | anchor s30 | 6.69 | 2.12 | -0.01 | -0.02 | -0.02 | -0.07 | 8.69 | | anchor s31 | 6.96 | 2.05 | -0.01 | -0.02 | -0.03 | -0.06 | 8.89 | | anchor s32 | 6.81 | 1.99 | -0.01 | -0.02 | -0.03 | -0.05 | 8.70 | | Arm N 8192 | 6.92 | 1.92 | -0.01 | -0.02 | -0.03 | -0.04 | 8.75 | | dgxseed30 | 7.12 | 1.76 | -0.00 | -0.02 | -0.03 | -0.04 | 8.78 | | dgxseed31 | 7.09 | 1.90 | -0.00 | -0.02 | -0.03 | -0.04 | 8.90 | | dgxseed32 | 7.09 | 2.09 | -0.01 | -0.02 | -0.03 | -0.04 | 9.09 | The four penalty terms (`bias`, `smoothness`, `thruster`, `torque`) sum to -0.12 against a total of ~8.8 — about 1.4% of the reward. This is the quantitative basis for deferring the `penalty_vs_objective` probe: there is no penalty mass to rebalance.

[EVIDENCE: `analyze_training.py --tier 3 --deep`, final-window means]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_buoyanchor_s30_260722_134743/analysis/diagnose-20260723-134359/report.md
