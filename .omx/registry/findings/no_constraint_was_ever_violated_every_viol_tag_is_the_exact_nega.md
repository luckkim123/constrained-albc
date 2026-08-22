---
title: "No constraint was ever violated. Every `viol` tag is the exact negation of its m"
tags: ["auto-captured"]
created: 2026-08-14T08:13:07.299190
updated: 2026-08-14T08:13:07.299190
sources: ["/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# No constraint was ever violated. Every `viol` tag is the exact negation of its m

No constraint was ever violated. Every `viol` tag is the exact negation of its margin at every sampled window — `Constraint/viol/attitude` -0.9866 -> -0.9933, `Constraint/viol/thruster_util` -4.869 -> -4.541, `Constraint/viol/rp_vel_settling` -9.154 -> -8.338, `Constraint/viol/manipulability` -4.507 -> -4.556, and likewise `Constraint/viol/arm_torque`, `Constraint/viol/arm_joint_vel`, `Constraint/viol/joint1_pos`, `Constraint/viol/cumul_yaw`, `Constraint/viol/rp_rate`, `Constraint/viol/yaw_rate`. A sign-mirrored pair carries no information the margin does not, so the `viol` family is redundant on a run that never binds.

[EVIDENCE: `~/groups.py` window dump, all 21 constraint tags]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md
