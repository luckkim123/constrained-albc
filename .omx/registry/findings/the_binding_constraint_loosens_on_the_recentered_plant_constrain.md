---
title: "The binding constraint LOOSENS on the recentered plant: Constraint/margin/thrust"
tags: ["auto-captured"]
created: 2026-07-28T05:32:19.957559
updated: 2026-07-28T05:32:19.957559
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# The binding constraint LOOSENS on the recentered plant: Constraint/margin/thrust

The binding constraint LOOSENS on the recentered plant: Constraint/margin/thruster_util 8.08 vs 7.06 (Constraint/viol/thruster_util -8.08 vs -7.06), and the engine J_C/d_k ladder puts HydroRC at 0.805 — back at the anchor level (anchor 0.805 / B0c 0.853 / ArmA 0.902 / E-int 0.821). thruster_util remains the binding constraint (max J_C/d_k) in both runs. | margin tag (final-window) | HydroRC | E-int | |:--|--:|--:| | Constraint/margin/attitude | 0.980 | 0.994 | | Constraint/margin/arm_torque | 6.541 | 7.465 | | Constraint/margin/arm_joint_vel | 1.917 | 1.889 | | Constraint/margin/joint1_pos | 0.999 | 0.982 | | Constraint/margin/cumul_yaw | 0.998 | 0.995 | | Constraint/margin/rp_rate | 6.314 | 6.512 | | Constraint/margin/yaw_rate | 9.561 | 9.660 | | Constraint/margin/rp_vel_settling | 9.487 | 9.387 | | Constraint/margin/manipulability | 4.892 | 4.214 | | Constraint/margin/thruster_util | 8.077 | 7.057 |

[EVIDENCE: tb_final.py final-window means for all ten Constraint/margin/* tags (Constraint/viol/* are their mirrors: viol = -margin for every tag, e.g. Constraint/viol/attitude -0.980, Constraint/viol/arm_torque -6.541, Constraint/viol/arm_joint_vel -1.917, Constraint/viol/joint1_pos -0.999, Constraint/viol/cumul_yaw -0.998, Constraint/viol/rp_rate -6.314, Constraint/viol/yaw_rate -9.561, Constraint/viol/rp_vel_settling -9.487, Constraint/viol/manipulability -4.892); J_C/d_k ladder from analyze_training.py tier-2 constraints table on this run plus the E-int ledger kept-event ladder]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081212/report.md

---

## Update (2026-07-28T05:32:19.957559)

The binding constraint LOOSENS on the recentered plant: Constraint/margin/thruster_util 8.08 vs 7.06 (Constraint/viol/thruster_util -8.08 vs -7.06), and the engine J_C/d_k ladder puts HydroRC at 0.805 — back at the anchor level (anchor 0.805 / B0c 0.853 / ArmA 0.902 / E-int 0.821). thruster_util remains the binding constraint (max J_C/d_k) in both runs. | margin tag (final-window) | HydroRC | E-int | |:--|--:|--:| | Constraint/margin/attitude | 0.980 | 0.994 | | Constraint/margin/arm_torque | 6.541 | 7.465 | | Constraint/margin/arm_joint_vel | 1.917 | 1.889 | | Constraint/margin/joint1_pos | 0.999 | 0.982 | | Constraint/margin/cumul_yaw | 0.998 | 0.995 | | Constraint/margin/rp_rate | 6.314 | 6.512 | | Constraint/margin/yaw_rate | 9.561 | 9.660 | | Constraint/margin/rp_vel_settling | 9.487 | 9.387 | | Constraint/margin/manipulability | 4.892 | 4.214 | | Constraint/margin/thruster_util | 8.077 | 7.057 |

[EVIDENCE: tb_final.py final-window means for all ten Constraint/margin/* tags (Constraint/viol/* are their mirrors: viol = -margin for every tag, e.g. Constraint/viol/attitude -0.980, Constraint/viol/arm_torque -6.541, Constraint/viol/arm_joint_vel -1.917, Constraint/viol/joint1_pos -0.999, Constraint/viol/cumul_yaw -0.998, Constraint/viol/rp_rate -6.314, Constraint/viol/yaw_rate -9.561, Constraint/viol/rp_vel_settling -9.487, Constraint/viol/manipulability -4.892); J_C/d_k ladder from analyze_training.py tier-2 constraints table on this run plus the E-int ledger kept-event ladder]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081242/report.md

---

## Update (2026-07-28T05:32:19.957559)

The binding constraint LOOSENS on the recentered plant: Constraint/margin/thruster_util 8.08 vs 7.06 (Constraint/viol/thruster_util -8.08 vs -7.06), and the engine J_C/d_k ladder puts HydroRC at 0.805 — back at the anchor level (anchor 0.805 / B0c 0.853 / ArmA 0.902 / E-int 0.821). thruster_util remains the binding constraint (max J_C/d_k) in both runs. | margin tag (final-window) | HydroRC | E-int | |:--|--:|--:| | Constraint/margin/attitude | 0.980 | 0.994 | | Constraint/margin/arm_torque | 6.541 | 7.465 | | Constraint/margin/arm_joint_vel | 1.917 | 1.889 | | Constraint/margin/joint1_pos | 0.999 | 0.982 | | Constraint/margin/cumul_yaw | 0.998 | 0.995 | | Constraint/margin/rp_rate | 6.314 | 6.512 | | Constraint/margin/yaw_rate | 9.561 | 9.660 | | Constraint/margin/rp_vel_settling | 9.487 | 9.387 | | Constraint/margin/manipulability | 4.892 | 4.214 | | Constraint/margin/thruster_util | 8.077 | 7.057 |

[EVIDENCE: tb_final.py final-window means for all ten Constraint/margin/* tags (Constraint/viol/* are their mirrors: viol = -margin for every tag, e.g. Constraint/viol/attitude -0.980, Constraint/viol/arm_torque -6.541, Constraint/viol/arm_joint_vel -1.917, Constraint/viol/joint1_pos -0.999, Constraint/viol/cumul_yaw -0.998, Constraint/viol/rp_rate -6.314, Constraint/viol/yaw_rate -9.561, Constraint/viol/rp_vel_settling -9.487, Constraint/viol/manipulability -4.892); J_C/d_k ladder from analyze_training.py tier-2 constraints table on this run plus the E-int ledger kept-event ladder]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136/analysis/diagnose-20260728-081953/report.md
