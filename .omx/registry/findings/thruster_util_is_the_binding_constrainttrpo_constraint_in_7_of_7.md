---
title: "thruster_util is the binding ConstraintTRPO constraint in 7 of 7 runs -- A5 loosened non-binding ones"
tags: ["constraint", "ipo", "thruster_util", "slack"]
created: 2026-07-23T04:54:56.975932
updated: 2026-07-23T04:54:56.975932
sources: ["diagnose-20260723-134359"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# thruster_util is the binding ConstraintTRPO constraint in 7 of 7 runs -- A5 loosened non-binding ones

FINDING: across 7 training runs spanning BOTH plants (pre/post buoyancy recentre), BOTH machines (workstation/DGX) and BOTH scales (4096/8192 envs), the binding ConstraintTRPO constraint is always thruster_util. EVIDENCE (engine .omx/profile/analyze_training.py --tier 3 --deep, JC/dk = fraction of budget consumed, final window): thruster_util 0.805 (buoyanchor s30) / 0.943 (s31) / 0.920 (s32) / 0.887 (ArmN 8192) / 0.853 (dgxseed30) / 0.852 (dgxseed31) / 0.865 (dgxseed32) -- 7/7 agreement. Runner-up on s30: rp_vel_settling 0.550, then rp_rate 0.395, arm_torque 0.237, manipulability 0.118, arm_joint_vel 0.042, yaw_rate 0.030; attitude/cumul_yaw/joint1_pos sit at -0.000 (fully dormant). CONSEQUENCE: A5 (trpo_budgetslack_260721_181133) raised budgets x100 on rp_vel_settling (0.550) and manipulability (0.118) -- neither is the binding term. This is a MECHANISM for A5's null result that does NOT depend on the seed floor, and it means any future constraint-slack probe should target thruster_util. Re-visit: analysis diagnose-20260723-134359 section 'constraint'.
