---
title: "thruster_util remains the binding constraint in both runs and its binding intens"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-27T06:42:48.885806
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# thruster_util remains the binding constraint in both runs and its binding intens

thruster_util remains the binding constraint in both runs and its binding intensity RISES with the band, JC/dk 0.805 -> 0.853 (+6%), while staying satisfied (viol -5.89) — the direction H1 predicted (weaker-ceiling envs must command a higher fraction of full throttle), at a magnitude far below violation. | constraint | anchor JC/dk | B0c JC/dk | B0c margin | B0c viol | |---|---|---|---|---| | Constraint/margin/thruster_util / Constraint/viol/thruster_util | 0.805 | 0.853 | 5.89 | -5.89 | | Constraint/margin/rp_vel_settling / Constraint/viol/rp_vel_settling | 0.550 | 0.542 | 9.15 | -9.15 | | Constraint/margin/rp_rate / Constraint/viol/rp_rate | 0.395 | 0.391 | 6.09 | -6.09 | | Constraint/margin/arm_torque / Constraint/viol/arm_torque | 0.237 | 0.216 | 6.27 | -6.27 | | Constraint/margin/manipulability / Constraint/viol/manipulability | 0.118 | 0.113 | 4.43 | -4.43 | | Constraint/margin/arm_joint_vel / Constraint/viol/arm_joint_vel | 0.042 | 0.041 | 1.92 | -1.92 | | Constraint/margin/yaw_rate / Constraint/viol/yaw_rate | 0.030 | 0.038 | 9.62 | -9.62 | | Constraint/margin/attitude / Constraint/viol/attitude | -0.000 | 0.019 | 0.98 | -0.98 | | Constraint/margin/joint1_pos / Constraint/viol/joint1_pos | -0.000 | 0.001 | 1.00 | -1.00 | | Constraint/margin/cumul_yaw / Constraint/viol/cumul_yaw | -0.000 | -0.000 | 1.00 | -1.00 |

[EVIDENCE: engine TIER 2 Constraints, b0c_engine.txt and anchor_engine.txt (all 10 rows each); barrier_penalty last=-0.1226, 0 spikes > 0.01]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md
