---
title: "Arm velocity_limit_sim 6.28->3.1 ripple: dead-constraint trap + delta_scale runaway (retrain item, not one-line)"
tags: ["albc", "envs-main", "arm", "actuator", "velocity-limit", "sim-to-real", "retrain-campaign", "constraint-trap", "delta-scale"]
created: 2026-07-06T07:33:23.049208
updated: 2026-07-06T07:33:23.049208
sources: []
links: ["onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7.md", "next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba.md", "encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har.md"]
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Arm velocity_limit_sim 6.28->3.1 ripple: dead-constraint trap + delta_scale runaway (retrain item, not one-line)

Scope: envs/main arm actuator. Records the DR/config ripple analysis for lowering the sim arm joint velocity cap, so the fix does not ship as a naive one-line change. Companion to the measurement that motivated it [[onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7]] and the roster it belongs to [[next_from_scratch_retrain_manifest_what_rides_on_the_post_tam_ba]].

## THE FIX (motivated, not yet applied)
Onboard 2026-07-06 raw velocity plateau shows the real XW540-T260 arm saturates at ~3.1 rad/s (= ~30 rpm no-load spec), but sim `velocity_limit_sim=6.28` (albc.py:201) lets the sim arm rotate TWICE as fast. So the sim arm out-runs the real arm on any large delta. Fix = lower `velocity_limit_sim` 6.28 -> ~3.1 rad/s. User AGREES in principle (measurement + real-robot safety). NOT applied yet -- rides the next from-scratch retrain (not byte-identical, invalidates checkpoints). Keep Kp/Kd unchanged (measured zeta~0.7 already matches).

## WHY IT IS NOT A ONE-LINE CHANGE -- three coexisting "velocity limit" layers
There is no single velocity limit. Three independent mechanisms at different layers, and lowering one shifts its RELATIVE relationship to the others:
1. **PhysX hard cap** `velocity_limit_sim` (albc.py:201) = 6.28 rad/s. Physically un-exceedable.
2. **Soft RL constraint** `velocity_limit_cost` (config.py:59, `limit_rad_per_s=4.189` ~= 4pi/3 ~= 240 deg/s, budget 0.02). Penalizes joint_vel > limit in the reward/Lagrangian. Impl: constraints.py:111 `I(max|q_dot_j| > limit_rad_per_s)`.
3. **Delta parameterization** (albc_env.py:578 `_joint_pos_targets += delta_scale * a_t`, delta_scale=0.10). Arm action is NOT a velocity command -- it is a delta-POSITION accumulator. So action space is unchanged by the cap.

## RIPPLE 1 (MUST fix together) -- soft constraint becomes a DEAD CONSTRAINT
Currently 4.189 (soft) < 6.28 (hard): the soft constraint bites first (intended -- soft inside hard). Lower the hard cap to 3.1 and the order INVERTS: 4.189 > 3.1, so PhysX clips joint_vel at 3.1 and it can NEVER reach 4.189 -> `velocity_limit_cost` is ALWAYS 0 -> a dead constraint. It still occupies budget 0.02 and a dual variable but supplies zero gradient; the policy treats it as free. FIX: when lowering velocity_limit_sim to 3.1, ALSO lower `velocity_limit_cost.limit_rad_per_s` to inside the new cap (e.g. ~2.5-2.8) so the soft constraint stays alive. This is the easy-to-miss trap (a name-vs-implementation / silent-death trap, DR-doc section 9 flavor): "just lower velocity_limit_sim" silently kills a constraint.

## RIPPLE 2 (review before retrain) -- delta_scale vs reachable speed (target runaway)
Sustained action=+1 demands target speed = delta_scale/step_dt = 0.10 / 0.02s = 5.0 rad/s (control_decimation=1, 50 Hz). Current hard cap 6.28 > 5.0 -> reachable. Lower to 3.1 < 5.0 -> the max delta command EXCEEDS the cap -> the arm cannot keep up, `_joint_pos_targets` (unbounded accumulator, no saturation) runs ahead of actual angle -> target-vs-actual gap accumulates. This matches the measurement (big-step is already velocity-saturated on the real robot too). Risk: sim target running ahead of reality teaches a distorted command strategy. Candidate mitigations: lower delta_scale (e.g. 0.10 -> ~0.06 to keep max demand under 3.1) OR saturate the target accumulator. DO NOT decide from numbers alone -- resolve with the delta-command sysid (`arm_delta_sysid.py`, unbuilt) that reproduces the real 50 Hz deploy operating point (the big-step data is a saturation anchor, not the deploy point).

## RIPPLE 3 (unrelated, name-collision only) -- body max_angular_velocity
`config.max_angular_velocity` (=pi, config.py:453) and asset `max_angular_velocity` (=720 deg/s=4pi, albc.py:181) are the ROBOT BODY (root/link) angular velocity, NOT the arm joint. They do NOT interact with velocity_limit_sim. Named similarly -> do not conflate when editing.

## SECONDARY -- observation normalization
joint_vel enters the 69D obs (arm 5D block includes joint_vel 2D). Lowering the cap shrinks joint_vel's upper support -> check the priv-obs normalization bound picks this up. Bounds are DR-derived (`priv_obs_bounds.py`, [[encoder_priv_obs_normalization_bounds_must_be_dr_derived_not_har]]) so it MAY auto-adjust, but velocity_limit_sim is not a DR param -- verify it is reflected.

## CHECKLIST for the retrain
- [ ] velocity_limit_sim 6.28 -> ~3.1 (albc.py:201) [measured]
- [ ] velocity_limit_cost.limit_rad_per_s 4.189 -> inside 3.1 (config.py:59) [MUST, else dead constraint]
- [ ] delta_scale (0.10) vs 3.1 reachability -- confirm via delta sysid, adjust or saturate accumulator if runaway [review]
- [ ] obs norm bound reflects lower joint_vel support [verify]
- [ ] keep Kp/Kd (zeta~0.7 matches) -- do NOT retune small-signal gains

