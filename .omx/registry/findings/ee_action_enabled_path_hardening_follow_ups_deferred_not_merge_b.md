---
title: "EE-action enabled-path hardening follow-ups (deferred, not merge blockers)"
tags: ["ee-action", "hardening", "ik", "follow-up"]
created: 2026-06-27T09:13:14.653866
updated: 2026-06-27T09:13:14.653866
sources: ["diagnose-20260627-175826", "feat/ee-action-review-abe0973"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# EE-action enabled-path hardening follow-ups (deferred, not merge blockers)

Whole-branch code review (opus) of feat/ee-action verdict APPROVE-WITH-NITS, 0 blockers. Toggle-off byte-identical PASS across action/obs/noise/reward. 3 MEDIUM findings are ENABLED-PATH robustness (gated behind ee_action_enable default OFF + k_anchor=0), NOT merge blockers. The 5000-iter toggle-ON training (run trpo_ee_action_260627_094127) had ZERO NaN/Inf in any TB scalar (verified full-run scan) + line_search 100% success, so none of these fired in practice. Deferred follow-ups before the NEXT enabled run: (1) MEDIUM-2: kinematics.py atan2(y,x) is NaN-grad at EE=(0,0); add inner-radius clamp (~0.05m) in EEActionLayer.step before IK -- measure-zero (leak*nom pulls toward (0.233,0.233)) but high blast radius if hit. (2) MEDIUM-1: default ee_leak=0.02 barely bounds drift (eq r=0.4632 vs boundary 0.466); the real bound is the Pade clamp + k_anchor=-0.5 reward, NOT the leak. Test test_biased_action_reaches_finite_equilibrium uses leak=0.05, not the shipped 0.02 default -- add a default-leak bound test. Design doc eq formula q_eq=nom+(ds/eps)*a is wrong in the clamped regime. (3) MEDIUM-3: kinematics.py:210 elbow sign_g2=where(cur_g2>=0,...) jumps ~3.3rad when cur_g2 crosses 0; nominal g2=pi/2 avoids it but DR could cross -- watch for joint2-sign-crossing in sim/eval, add hysteresis if observed. All 3 pre-existing in ALBCKinematics but EE-action is first consumer driving RL-chosen arbitrary EE targets through it.
