---
title: "constraints inert on teacher run: cost achieved (A) + barrier too weak (B)"
tags: ["constraint", "ipo", "barrier", "cmdp", "diagnosis", "teacher-run"]
created: 2026-06-05T02:19:18.309574
updated: 2026-06-05T02:19:18.309574
sources: []
links: []
category: decision
confidence: high
schemaVersion: 1
---

# constraints inert on teacher run: cost achieved (A) + barrier too weak (B)

On run 260525_232805_trpo_main_teacher the 10 ConstraintTRPO constraints effectively did NOT shape learning - the CMDP behaved like a plain MDP. Decisive evidence requires the RIGHT quantity: margin is useless for safety because adaptive_d_k = max(d_k, cost + 0.05*d_k) (constraint_trpo.py:308) floors margin at +0.05*d_k regardless of cost. Judge by cost/d_k instead.

SCALE TRAP (verified in code): config budget D_k is PER-STEP; the algorithm uses self.d_k = D_k / (1 - cost_gamma) = D_k * 100 (gamma=0.99, constraint_trpo.py:146-148). cost (mean_cost_returns) is the discounted sum on the same x100 scale. Logged margin = adaptive_d_k - cost (line 449); logged viol = mean_cost_returns - d_k (line 447). Reconstruct cost = d_k - margin.

Q4 cost/d_k per constraint (d_k = D_k*100): attitude 0.8 pct, cumul_yaw 0.7 pct, joint1_pos 0.5 pct, arm_joint_vel 3.4 pct, manipulability 6.2 pct, yaw_rate 13.8 pct, rp_rate 30.8 pct, arm_torque 43.5 pct, rp_vel_settling 44.8 pct, thruster_util 87.2 pct.

VERDICT: hypothesis A (achieved) dominates for 8/10 - incl. the spin-out-relevant yaw_rate (13.8 pct) and cumul_yaw (0.7 pct); policy genuinely drove cost far below budget after the ~iter35 warmup. thruster_util (87.2 pct) is hypothesis B (loose budget) - cost sits just under d_k, near-inert. The deeper B cause is barrier strength, not budget placement: barrier_penalty ~= 0.05 pct of reward (Axis 4), so even at 87 pct of budget the barrier gradient cannot beat the reward gradient.

CONCLUSION: C-inactivation = A (cost achieved) + B (barrier too weak), with barrier weakness dominant. Tightening budgets alone will NOT activate constraints unless (1) the barrier can actually push back (lower barrier_t / raise effective penalty) AND (2) the env creates states where cost approaches budget. Pure DR-difficulty increase (kl_ub up) only helps via (2): it raises cost toward budget on the hardest axes, but if the barrier stays at 0.05 pct of reward the constraint still cannot win the gradient tug-of-war. So DR-harder is necessary-but-not-sufficient for constraint activation; barrier strength is the gating factor.

