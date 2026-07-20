---
title: "Safety-rail constraints fire hard at init, go quiet, and RE-FIRE as DORAEMON widens DR -- 0% at the final window is working insurance, not dead weight; thruster_util is the one trending into binding (93.2% at extend8k)"
tags: ["constraint", "safety-rail", "dead-constraint-trap", "doraemon", "dr-harder", "thruster-util", "binding", "diagnosis", "envs-main"]
created: 2026-07-20T03:27:41.707105
updated: 2026-07-20T03:27:41.707105
sources: []
links: ["constraint_threshold_budget_tuning_thresholds_split_into_hard_ph.md", "constraint_budget_x0_5_binds_only_thruster_util_authority_starva.md", "e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Safety-rail constraints fire hard at init, go quiet, and RE-FIRE as DORAEMON widens DR -- 0% at the final window is working insurance, not dead weight; thruster_util is the one trending into binding (93.2% at extend8k)

A safety-rail constraint reading ~0% utilization at the END of training is NOT a dead constraint. Measured
across 5 runs: the rails fire HARD in the first ~1000 iters, get suppressed, and RE-FIRE once DORAEMON
widens DR far enough. The final-window snapshot alone cannot tell "inactive" from "dead".

## Measurement

`J_C/d_k` (%) reconstructed from TB `Constraint/viol/*` (`J_C = viol + d_k`, `d_k = D_k*100`), sampled
across training. `DRent` = `DORAEMON/entropy_before` (rises = DR distribution widening).

Phase 1 -- the rails BITE at init (iter 0, every run):
- `cumul_yaw` 139.7% / 140.2% (VIOLATED), `yaw_rate` 201.7% / 149.3% / 130.7% (VIOLATED),
  `arm_joint_vel` 97.2-97.3%, `arm_torque` 29-36%.
- These are the same constraints that read 0.0% at the end. The untrained policy walked straight into the
  tether-wrap and yaw-rate rails and the barrier pushed it out.

Phase 2 -- suppressed by iter ~1000: attitude / joint1_pos / cumul_yaw / arm_joint_vel all ~0%.

Phase 3 -- they RE-FIRE as DR widens (this is the load-bearing observation):
- `trpo_biasema_extend8k_260716_162849` @7999 (DRent -18.2): `attitude` 9.5%, `cumul_yaw` 11.6%.
- `trpo_perflb200_260715_023744` @3000/@4999 (DRent -30.8/-21.7): `joint1_pos` 10.5% / 17.0%.
- The same constraints sit at 0.0% in the 5000-iter baseline `trpo_baseline_260713_031325` (DRent -30.1).

CONCLUSION: attitude / joint1_pos / cumul_yaw are working insurance, not dead weight. Do NOT delete them
and do NOT tighten them to "make them matter" -- they already mattered, early, and they wake up again
when the environment gets hard enough. `joint1_pos` in particular guards a MEASURED failure mode (Stage-1
gate: 31-48/64 envs exceeded 2pi, one env reached -743 rad on unlimited physics).

## Dead vs inactive -- the test that actually matters

An inactive constraint CAN fire and currently does not. A DEAD constraint CANNOT fire because its soft
threshold sits outside the PhysX hard cap, so it burns a cost head and a budget slot for nothing (the
dead-constraint trap in [[constraint_threshold_budget_tuning_thresholds_split_into_hard_ph]]).
Verified current state -- no dead constraints:
- `arm_torque` soft 9.5 Nm < hard `effort_limit_sim` 13.0 -> live band (9.5, 13].
- `arm_joint_vel` soft 2.8 rad/s < hard `velocity_limit_sim` 3.1 -> live band (2.8, 3.1].
  The trap the earlier page warned about (cap 6.28 -> 3.1 would strand the old soft 4.189 ABOVE the cap)
  was avoided by lowering the soft threshold to 2.8 in the same change (XW540-T260 measurement 2026-07-06).
  WATCH: a 0.3 rad/s live band is thin -- the next actuator-cap change can kill this constraint silently.

## GUARD: thruster_util is the one trending INTO binding

Opposite risk to the user intuition "the constraints should bite more". `thruster_util` rises monotonically
with DR width and is approaching the 95% binding threshold:
`trpo_baseline_260713` @4999 79.7% -> `trpo_perflb200` @4999 89.1% -> `perflb200-moreiters` @7999 89.4%
-> `trpo_biasema_extend8k` @7999 **93.2%**.
E6 already measured what happens past that line: budgets x0.5 pushed thruster_util into binding and caused
authority starvation -- reward -54%, entropy collapse
([[constraint_budget_x0_5_binds_only_thruster_util_authority_starva]]).
So before the DGX scale-up (see [[e3_s_5000_iter_budget_verdict_is_scope_limited_not_a_cap_max_ite]]),
watch `Constraint/viol/thruster_util`, not just `DORAEMON/success_rate`: a longer/wider run is being driven
straight at the one constraint that is genuinely close to binding. This is a launch-time guard, not a
separate experiment.

## Reusable procedure

To judge any constraint, do not read the final-window margin. Reconstruct `J_C/d_k` over the WHOLE run and
plot it against `DORAEMON/entropy_before`. Three signatures: (a) fires early then flat 0 with DR rising =
healthy rail, far away; (b) flat 0 from iter 0 with DR rising = suspect, check the soft-vs-hard-cap layering
for the dead-constraint trap; (c) monotonically rising with DR = heading for binding, guard it.
Needs no new training -- TB scalars are enough.

