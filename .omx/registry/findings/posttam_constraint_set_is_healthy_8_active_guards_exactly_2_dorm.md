---
title: "Posttam constraint set is healthy: 8 active guards + exactly 2 dormant (rp_vel_settling, manipulability)"
tags: ["constraint", "slack", "rp_vel_settling", "manipulability", "p-d1", "p-d2", "jc-dk", "normalization", "correction", "albc"]
created: 2026-07-15T05:05:55.023871
updated: 2026-07-22T01:58:00.458681
sources: ["trpo_baseline_260714_192020", "diagnose-20260722-103723"]
links: ["constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli.md"]
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

---

## Update (2026-07-22T01:58:00.458681)

CORRECTION (2026-07-22, from A5 budgetslack analysis diagnose-20260722-103723): the '2 dormant = rp_vel_settling + manipulability' claim is HALF wrong under normalization. Ranked by raw min-margin, rp_vel_settling looks dormant (margin ~8.6, stays >8 whole run). But ranked by the CORRECT normalized J_C/d_k (d_k = budget/(1-gamma) = 0.20/0.01 = 20.0), rp_vel_settling in the anchor trpo_biasema_260715_142543 is J_C/d_k=0.549 -- the 2ND-MOST-ACTIVE guard, above rp_rate 0.409, behind only thruster_util 0.846. Only manipulability is genuinely dormant (0.034). This is the recurring raw-vs-normalized trap (see [[constraint_margin_must_be_normalized_j_c_d_k_absolute_margin_fli]]): normalization by the small d_k is what surfaces rp_vel_settling as active. Consequence for budget tuning: relaxing rp_vel_settling's budget x100 (A5) is NOT a no-op -- it releases a moderately-active barrier, and A5 measured a none-level roll-for-pitch tracking trade as a result (contingent on seed floor).
