---
title: "All 10 constraints are satisfied (viol<0, margin>0); the active set is thruster_"
tags: ["auto-captured", "trpo_baseline_260714_192020"]
created: 2026-07-14T16:41:28.339995
updated: 2026-07-14T16:41:28.339995
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# All 10 constraints are satisfied (viol<0, margin>0); the active set is thruster_

All 10 constraints are satisfied (viol<0, margin>0); the active set is thruster_util (binding) then rp_vel_settling, with 6 constraints in deep slack. The IPO barrier is smooth (no spikes), so constraint advantages are well-behaved.

[EVIDENCE: engine TIER 2 Constraints J_C/d_k: thruster_util 0.778, rp_vel_settling 0.485, rp_rate 0.399, arm_torque 0.237, yaw_rate 0.090, arm_joint_vel 0.019, joint1_pos 0.001, attitude/cumul_yaw/manipulability ~0]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_posttam/trpo_baseline_260714_192020/analysis/diagnose-20260715-011113/report.md
