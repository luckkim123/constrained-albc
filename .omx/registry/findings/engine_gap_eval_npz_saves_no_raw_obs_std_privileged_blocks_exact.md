---
title: "engine-gap: eval npz saves no raw obs/std/privileged — blocks exact per-env std reconstruction"
tags: ["engine-gap", "eval", "adaptivity", "state_dependent_std", "npz", "debugging"]
created: 2026-06-09T04:03:28.206032
updated: 2026-06-09T04:03:28.206032
sources: ["diagnose-20260609-125556"]
links: []
category: decision
confidence: high
schemaVersion: 1
---

# engine-gap: eval npz saves no raw obs/std/privileged — blocks exact per-env std reconstruction

[ENGINE-GAP] The static-eval npz (data_<level>.npz) saves trajectories (error_roll/pitch, yaw_rate, action_magnitude, terminated) + per-env DR params (dr_* , 23 keys) but NOT the raw 69D policy obs, NOT the 27D privileged vector, and NOT the per-step action std. So a state_dependent_std adaptivity probe CANNOT feed the std head the exact obs that produced each eval env's std — the policy-obs leg must be held at the normalizer mean and only the encoder (DR) leg can be driven by real data. This caps the adaptivity-probe at HIGH-for-the-difficulty-null but MED-for-absolute-std-magnitudes. [WHERE] constrained_albc/analysis/eval.py np.savez_compressed (~line 1576) — the per-level data pack. Also latent_<level>.npz (~line 1144) saves l_hat/l_true but not obs/std. [SPEC] add an optional --save-policy-obs / --save-action-std flag that also stores the realized 69D policy obs and the per-step action_std (already computed inside the policy as distribution.stddev) into the npz, so a later adaptivity probe can feed the std head the REAL realized obs per env instead of a held-mean. [EVIDENCE] Phase-2 state_std deepening (analysis diagnose-20260609-125556): wanted per-env std vs realized difficulty but could only reconstruct the DR/encoder leg; corr stayed a directional null (-0.03), defensible but the exact realized-obs std was unreconstructable. [STATUS] proposed
