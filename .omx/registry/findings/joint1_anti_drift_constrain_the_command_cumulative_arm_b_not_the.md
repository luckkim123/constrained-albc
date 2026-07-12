---
title: "joint1 anti-drift: constrain the COMMAND (cumulative, Arm B) not the MEASUREMENT (wrap, Arm A) to preserve attitude"
tags: ["joint1", "drift", "constraint", "IPO", "pitch-trim", "attitude", "correction"]
created: 2026-06-27T19:33:37.006409
updated: 2026-07-12T14:17:28.437628
sources: ["diagnose-20260628-042815", "wiki-curation-2026-07-12"]
links: ["arm_a_measured_angle_joint1_constraint_recovers_not_diverges_the.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# joint1 anti-drift: constrain the COMMAND (cumulative, Arm B) not the MEASUREMENT (wrap, Arm A) to preserve attitude

Arm B (joint1_cumulative_cost = |_joint_pos_targets[:,0] - nominal|, the COMMANDED unwrapped integrator) suppresses joint1 drift to ~0 (drift_slope 1e-4 rad/s, final_abs p95 0.117 rad@hard < budget 0.224) with k_joint1_center=0 (reward OFF), AND preserves attitude (pitch ss median 0.30-0.48 deg none->hard, survival 100%). Arm A (joint1_centering_cost = wrap(theta1)^2 on the MEASURED angle) instead diverged on pitch. MECHANISM (constraints.py:245-293): penalizing the measured pose lets the IPO ratchet fold the physical arm to nominal, removing the theta2 pitch-trim DOF; penalizing the command never touches the measured pose, so trim survives. RULE: for a free continuous DOF, constrain the commanded integrator, not the measured/wrapped angle. The binary joint1_pos indicator stays inert (J_C/d_k=0.001) because it gives no shaping gradient inside +-4pi; joint1_cumulative is the live restoring pressure (J_C/d_k=0.659, BINDING). Evidence: report diagnose-20260628-042815 (run trpo_cumul_constraint_260627_231709), summary.json + drift_metrics.json + TB Constraint/{margin,viol}/joint1_cumulative.

---

## Update (2026-07-12T14:17:28.437628)

Update (2026-07-12, wiki curation): correction — the Arm A verdict above is stale. Arm A (measured-angle joint1_centering_cost) does NOT diverge: the earlier divergence verdict was an early-stop artifact; on the full run Arm A RECOVERS, at the cost of a persistent pitch-bias trade-off. See [[arm_a_measured_angle_joint1_constraint_recovers_not_diverges_the]]. The design rule stands unchanged (constrain the commanded integrator, Arm B — no attitude bias at all), but the reason Arm A loses is the pitch-bias trade-off, not divergence.

