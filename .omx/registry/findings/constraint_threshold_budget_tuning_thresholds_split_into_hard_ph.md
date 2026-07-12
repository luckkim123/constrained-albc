---
title: "Constraint threshold/budget tuning: thresholds split into hard physical rails (soft-inside-hard vs PhysX cap) vs soft shaping thresholds; budgets mostly no-op (9/10 slack); co-tune one at a time"
tags: ["constraint", "threshold", "budget", "actuator", "effort-limit", "velocity-limit", "dead-constraint-trap", "ipo", "tuning", "cumul-yaw", "soft-inside-hard"]
created: 2026-07-12T08:24:56.841241
updated: 2026-07-12T08:24:56.841241
sources: []
links: ["constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Constraint threshold/budget tuning: thresholds split into hard physical rails (soft-inside-hard vs PhysX cap) vs soft shaping thresholds; budgets mostly no-op (9/10 slack); co-tune one at a time

How to think about the constraint VALUES (per-constraint thresholds AND budgets) in
envs/main, settled during the 2026-07-12 constraint deep-dive. The user's question was:
should each constraint's threshold and budget be experimentally tuned? Answer: yes, but the
thresholds split into two groups with OPPOSITE tuning rules, and most budget tuning is a no-op.

## Thresholds are NOT one uniform knob — two groups

1. HARD SAFETY RAILS (physically grounded, tune only toward the true physical value):
   `attitude` (80deg tilt), `arm_torque` (limit_nm=9.5 = arm motor STALL torque),
   `arm_joint_vel` (4.189 rad/s), `joint1_pos` (4*pi cable-wrap rail), `cumul_yaw` (8*pi
   tether-wrap rail). Tuning these toward reward trades away safety and can trigger the
   dead-constraint trap below. Change them only measurement/sysid-driven.
2. SOFT SHAPING THRESHOLDS (judgment-chosen behavior/comfort envelopes, legitimate RL/experiment
   tuning targets): `rp_rate` (0.5), `yaw_rate` (0.55), `rp_vel_settling` (0.087),
   `manipulability` (0.3). These set WHERE a graded hinge penalty begins.

## Actuator hard-cap layering: soft-inside-hard is the invariant

The two arm soft constraints sit INSIDE the asset's PhysX hard caps
(`marinelab/marinelab/assets/albc/albc.py:200-201`):
- effort_limit_sim = 13.0 Nm  (hard) > arm_torque limit_nm = 9.5 (soft)  -> 9.5 < 13.0
- velocity_limit_sim = 6.28 rad/s (2*pi, hard) > arm_joint_vel = 4.189 (soft) -> 4.189 < 6.28
So the soft IPO constraint bites BEFORE the PhysX clamp (intended), and the constraint stays
alive because there is a live band above the threshold where the indicator can fire (matches
§9: arm_torque J_C/d_k = 0.407 fires; arm_joint_vel 0.031 deep slack).
INVARIANT: the soft threshold must stay inside the hard cap. Inverting it silently kills the
constraint. The planned velocity_limit_sim 6.28 -> 3.1 retrain (to match the real XW540 arm)
would make 3.1 < 4.189, so PhysX clips at 3.1 and velocity_limit_cost can NEVER fire = a dead
constraint still occupying a budget + a cost head. Fix (lower limit_rad_per_s inside the new
cap together, plus delta_scale runaway ripple) is documented in
`arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md`. Same layering logic on
the torque side (13.0 > 9.5), no current conflict there. torque_limit_cost also reads
applied_torque (POST-clamp), so it inherently sees <= 13 and fires in the (9.5, 13] band.

## Budget tuning is mostly a no-op; co-tune (threshold, budget), one constraint at a time

Threshold sets WHERE cost starts; budget D_k sets HOW MUCH is tolerated -> they are coupled.
Tuning a budget alone on a constraint whose threshold sits far from the operating point does
nothing. §9 shows 9/10 constraints slack, so most (threshold OR budget) tuning changes nothing
until the change pushes the constraint toward binding. Only thruster_util binds, and E6 showed
tightening it (all budgets x0.5) causes authority starvation (reward -54%, entropy collapse)
[[constraint_budget_x0_5_binds_only_thruster_util_authority_starva]]. So on a 1-GPU sequential
rig: co-tune (threshold, budget) for the ONE constraint you want to shape, minimum-change,
measure vs baseline. Do NOT joint-grid-sweep a mostly-flat response surface with one cliff.

## avg constraints use max_i INSIDE the per-step cost — theoretically fine

thruster_util (max_i |s_i|) and rp_rate (max(|p|,|q|)) reduce with a spatial max inside c_k.
The "average" of an average constraint is the temporal/stochastic expectation E[sum gamma^t c_k];
max only shapes the per-step signal. So max-inside-average bounds a TIME-AVERAGED PEAK (a soft
peak that tolerates brief spikes) = E[max_i], NOT max_i E[], and NOT a hard "never exceed at any
step" bound (that needs a probabilistic indicator). rp_vel_settling uses mean, yaw_rate /
manipulability are single-quantity, so max appears only for multi-component reductions.

## cumul_yaw headroom (recorded, low priority, user intent = cosmetic)

cumul_yaw limit = 8*pi (4 rev) is ~3.3x the observed operating peak (~1.22 rev; §9 fully inert,
J_C/d_k = 0.000). A cosmetic trim to 6*pi (3 rev) STAYS INERT — a behavioral no-op (the cost
signal is bit-identical since the indicator never fires either way), safe to ride any future
config touch; no separate experiment needed. A bind-intended value would need <= ~2.5*pi and
should weigh whether it fights normal yaw maneuvering. User intent 2026-07-12 = cosmetic (a),
so no functional change queued.

Doc: docs/reference/constraints.md §3.2 (max soft-peak) + §3.4 (threshold provenance / layering).

