---
title: "teacher: cross-axis correlation collapses none->hard (axis decorrelation)"
tags: ["cross-axis", "correlation", "decorrelation", "sample-mean-divergence", "hard-DR"]
created: 2026-06-05T10:09:41.192115
updated: 2026-06-05T10:09:41.192115
sources: ["20260605-190606-diagnose"]
links: []
category: pattern
confidence: high
schemaVersion: 1
---

# teacher: cross-axis correlation collapses none->hard (axis decorrelation)

Teacher cross-axis env-level corr collapses ~1.0(none)->~0.3(hard): att_lv -0.994->+0.358, roll_yaw 0.999->0.081, vx_vy 1.000->0.538 (heavy_tail.json corr via eval_adapter). Consequence: median-att env stops being typical on other axes (medium sample_idx=25 roll rank 28.6% vs vx rank 90.5%) -> the sample-vs-mean gap visible in traj_attitude.png is axis decorrelation, NOT a bug. This is the 'sample line diverges from mean' diagnostic from rule 03, quantified. See analysis 20260605-190606-diagnose.
