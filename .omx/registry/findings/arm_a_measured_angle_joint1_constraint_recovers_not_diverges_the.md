---
title: "Arm A (measured-angle joint1 constraint) RECOVERS, not diverges — the earlier divergence verdict was an early-stop artifact"
tags: ["joint1", "drift", "constraint", "IPO", "pitch-trim", "recovery", "early-stop"]
created: 2026-06-28T00:23:53.182300
updated: 2026-06-28T00:23:53.182300
sources: ["diagnose-20260628-091712"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# Arm A (measured-angle joint1 constraint) RECOVERS, not diverges — the earlier divergence verdict was an early-stop artifact

Arm A (joint1_centering_cost=wrap(theta1)^2 on the MEASURED angle, IPO Average, d_A=0.05, reward k_joint1_center=0) does NOT diverge on pitch despite an early trough — it is a LATE-RESOLVED RECOVERY. Trajectory (run trpo_avg_constraint_d05_260628_040906, analysis diagnose-20260628-091712): Train/mean_reward -440(iter150) -> -47(iter1700) -> +75(iter2000) -> +220(plateau ~iter2500+); Reward/att_rp -10.3 -> -2.1(iter1700) -> +5.9(iter4999). Engine (analyze_training.py): PELT changepoint iter1750, HMM state0 mean_reward=-168 vs state1 +225, phase=learning->unstable->warmup->plateau. The prior 'Arm A diverged on pitch' conclusion (wiki joint1_anti_drift_*) came from stopping at the ~iter700 trough — LESSON: a free-DOF constraint can pay a long feasibility-recovery cost before the policy relearns the sacrificed DOF; do not call divergence from a trough slope. OUTCOME: A converges with a PERMANENT pitch ss bias ~1.07-1.28 deg at EVERY DR level (difficulty-invariant; summary.json), vs Arm B's 0.31-0.48 deg. MECHANISM (constraints.py:245-269): penalizing the measured pose lets the IPO ratchet fold the physical arm to nominal (joint1_target ~0 even at hard DR, joint1_target_hard.png), removing theta2 as a pitch-trim DOF. A vs B = complementary trade-off: A wins roll/OOD robustness (roll ood 0.58 vs B 2.48; att_norm ood 1.54 vs B 2.66; drift final_abs p95 ood 0.099 vs B 0.177) but loses pitch precision; B preserves pitch trim but roll goes heavy-tail at OOD (CV 307%). Both suppress drift slope to ~1.3-1.6e-4 rad/s.
