---
title: "EE-action redesign meets joint1 drift goal at constraint level"
tags: ["ee-action", "joint1-drift", "constraint"]
created: 2026-06-27T09:03:56.761023
updated: 2026-06-27T09:03:56.761023
sources: ["diagnose-20260627-175826"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# EE-action redesign meets joint1 drift goal at constraint level

EE-delta action (EE-space integrate + Pade workspace clamp + differentiable 2-link IK, replacing joint-delta integrator; ee_action_enable=true k_anchor=-0.5 obs 69->71D) achieves attitude parity AND fixes joint1 drift. Evidence (analyze_training.py TIER 2, JC/dk normalized): joint1_pos JC/dk=0.024 (deep slack), manipulability JC/dk=0.002 (~no binding) => arm stayed in-workspace, joint1 did not drift. Attitude SS error <1deg every axis every DR level, survival 100% incl OOD. EE-anchor reward=-0.028 (soft restoring, ~0.4% of total). Run trpo_ee_action_260627_094127, analysis diagnose-20260627-175826 (constraint section). Decision: redesign meets its goal, adoptable.
