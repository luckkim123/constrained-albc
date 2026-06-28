---
title: "EE-action joint1 drift gone DIRECTLY via flat-target, but settle position is bimodal"
tags: ["ee-action", "joint1-drift", "flat-target", "station-keeping"]
created: 2026-06-27T10:34:45.584166
updated: 2026-06-27T10:34:45.584166
sources: ["diagnose-20260627-192853"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# EE-action joint1 drift gone DIRECTLY via flat-target, but settle position is bimodal

Direct flat-target (static --flat-target, all commands zeroed) eval on EE-action checkpoint trpo_ee_action_260627_094127 confirms the joint1 monotonic drift is ELIMINATED, not just inferred from constraint slack. data_<level>.npz joint1_target (T=7750 x 64 envs): settles in 4.7-7.8s then FLAT for remaining ~125s. drift-after-settle <= 0.086 rad (none) / <= 0.008 rad (soft/medium/hard); monotonicity 0.53 (random walk, not a ramp's ~1.0); survival 100% all 4 levels. BUT the direct eval reveals what JC/dk=0.024 slack cannot: the settle POSITION is bimodal -- 40-56% of envs park at |final|>1 rad (~57-160deg), rest near nominal; violin two-lobed at every level (joint1_drift_flat.png). Cause: the soft EE-anchor (k_anchor=-0.5, reward -0.028) stops drift without centering. Lesson: constraint-slack proves no-violation but cannot reveal WHERE the free DOF parks -- a flat-target station-keeping eval is the direct measurement. To run it on an EE-action ckpt: eval.py static --flat-target env.ee_action_enable=true env.ee_delta_scale=0.02 (needs the obs-dim auto-sync, eval.py run_static).
