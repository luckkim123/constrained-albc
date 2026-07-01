---
title: "ee_leak=0 + k_anchor=0 does NOT blow up joint1 settle (Pade/IK clamp bounds it); settle still bimodal"
tags: ["ee-action", "joint1-drift", "leak-removal", "settle-position", "bimodal"]
created: 2026-06-30T06:56:42.704673
updated: 2026-06-30T06:56:42.704673
sources: ["diagnose-20260629-234023"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# ee_leak=0 + k_anchor=0 does NOT blow up joint1 settle (Pade/IK clamp bounds it); settle still bimodal

Removing BOTH soft mechanisms (ee_leak 0.02->0.0, k_anchor->0.0; Reward/anchor=0.000 confirmed) did NOT cause a settle-position blow-up -- the design open-blind-spot verification PASSES. flat-target: cumulative joint1 settles in ~2s then flat for ~150s, drift-after-settle <=0.013rad, final |theta_cum| mean 2.0-2.4rad~0.35rev (nowhere near disk boundary). The Pade workspace clamp + IK radial clamp bound the EE target alone, as the dr-config review predicted (50k-step adversarial NaN=False). BUT settle POSITION is still bimodal: 43.8-57.8% of envs park at |final joint1_target|>1rad (~57deg+), two-lobed violin at every DR level (plots/joint1_settle_position.png). This MATCHES the prior anchored ee-action run trpo_ee_action_260627 (k_anchor=-0.5: 40-56% >1rad, bimodal) -- so bimodality is an ee-action property, NOT caused by the constraint or leak removal. Net-rotation capping is orthogonal to centering; centering remains unsolved. P4 task perf preserved: pitch ss 0.28-0.35deg sub-degree all 4 DR, survival 100%.
