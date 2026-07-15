---
title: "Posttam constraint set is healthy: 8 active guards + exactly 2 dormant (rp_vel_settling, manipulability)"
tags: ["constraint", "slack", "rp_vel_settling", "manipulability", "p-d1", "p-d2"]
created: 2026-07-15T05:05:55.023871
updated: 2026-07-15T05:05:55.023871
sources: ["trpo_baseline_260714_192020"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# Posttam constraint set is healthy: 8 active guards + exactly 2 dormant (rp_vel_settling, manipulability)

P-D1 constraint A/B/C classification from posttam baseline TB Constraint/margin/* time-series (min-margin + early-vs-late trend over the run). Of 10 constraints:
- DORMANT (never approach binding): rp_vel_settling (min margin 8.6, stays >8 whole run), manipulability (min 4.08, flat) — EXACTLY the doc's 'inert-2'. Confirmed via time-series, not just final value.
- ACTIVE guards (reach small min margin 0.05-0.5 = shape training): attitude (min 0.05), cumul_yaw (0.05), joint1_pos (0.24), arm_torque (0.40), arm_joint_vel (0.10), rp_rate (0.50), yaw_rate (0.50, relaxes late), thruster_util (top binding by cost-gradient JC/dk 0.778, margin>=2 but highest cost pressure).
CONCLUSION: constraint set is HEALTHY (8 active + 2 dormant); the 2 dormant slacks are complementary-slackness health, not a defect. => P-D2 (loosening rp_vel_settling+manipulability budgets x100) is SAFE but LOW value — no rebalance is warranted by the data. Gates the P-D2 launch decision to 'only if a free GPU window exists', matching the doc's LOW priority.
