---
title: "joint1 cumulative-rotation constraint never binds: policy parks at ~0.36 rev, +-4pi is a dead-zone rail"
tags: ["joint1-drift", "cumulative-rotation", "constraint", "dead-zone", "flat-target"]
created: 2026-06-30T06:56:43.078781
updated: 2026-06-30T06:56:43.078781
sources: ["diagnose-20260629-234023"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# joint1 cumulative-rotation constraint never binds: policy parks at ~0.36 rev, +-4pi is a dead-zone rail

Run trpo_joint1_cumul_rot_260629_183545 (task-space 71D ee-action, infinite-physics USD, k_anchor=0 + ee_leak=0, new 11th probabilistic constraint I(|theta_cum|>4pi)<=0.01). The +-4pi (2 rev) constraint NEVER bound: three independent sources agree the policy naturally parks at ~0.36 rev. (1) Episode/cumul_joint1_deg=128deg=0.356rev (training TB). (2) Constraint/viol/joint1_cumul_rot final -1.0 mean200 -0.99967 = full budget headroom every iter (deepest-slack constraint alongside attitude/joint1_pos). (3) flat-target peak |theta_cum| max 1.22rev(none)..1.09rev(hard), 0/64 env >4pi at all 4 DR levels. Differential diagnosis: hypothesis 'constraint pushed drift down' predicts viol near budget + peak pressing 4pi; hypothesis 'task settles below cap, +-4pi is dead-zone guard' predicts deep slack + peak far below -- evidence is exactly the latter. Confirms design 2026-06-29-joint1-graduated...md sec.5.5 gray-result prediction (pre-run measured drift 1.14rev < 2rev limit). To make it bind: much tighter limit, or a drift-inducing task (moving yaw cmd / longer horizon). flat-target station-keeping does NOT provoke multi-rev drift.
