---
title: "engine-gap: eval npz saves no raw obs/std/privileged — blocks exact per-env std reconstruction"
tags: ["engine-gap", "eval", "adaptivity", "state_dependent_std", "npz", "debugging"]
created: 2026-06-09T04:03:28.206032
updated: 2026-07-14T15:31:09.018426
sources: ["diagnose-20260609-125556", "constrained-albc@8c07584"]
links: ["state_dependent_std_robustness_vs_nominal_trade_off_not_difficul.md"]
category: decision
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
status: resolved
---

# engine-gap: eval npz saves no raw obs/std/privileged — blocks exact per-env std reconstruction

[ENGINE-GAP] The static-eval npz (data_<level>.npz) saves trajectories (error_roll/pitch, yaw_rate, action_magnitude, terminated) + per-env DR params (dr_* , 23 keys) but NOT the raw 69D policy obs, NOT the 27D privileged vector, and NOT the per-step action std. So a state_dependent_std adaptivity probe CANNOT feed the std head the exact obs that produced each eval env's std — the policy-obs leg must be held at the normalizer mean and only the encoder (DR) leg can be driven by real data. This caps the adaptivity-probe at HIGH-for-the-difficulty-null but MED-for-absolute-std-magnitudes. [WHERE] constrained_albc/analysis/eval.py np.savez_compressed (~line 1576) — the per-level data pack. Also latent_<level>.npz (~line 1144) saves l_hat/l_true but not obs/std. [SPEC] add an optional --save-policy-obs / --save-action-std flag that also stores the realized 69D policy obs and the per-step action_std (already computed inside the policy as distribution.stddev) into the npz, so a later adaptivity probe can feed the std head the REAL realized obs per env instead of a held-mean. [EVIDENCE] Phase-2 state_std deepening (analysis diagnose-20260609-125556): wanted per-env std vs realized difficulty but could only reconstruct the DR/encoder leg; corr stayed a directional null (-0.03), defensible but the exact realized-obs std was unreconstructable. [STATUS] proposed

---

## Update (2026-07-14T15:31:09.018426)

[STATUS] proposed -> IMPLEMENTED (2026-07-15, commit constrained-albc 8c07584).

Delivered exactly the [SPEC]: two opt-in static-eval flags added to constrained_albc/analysis/eval.py:
- `--save-policy-obs` stores the realized 69D policy obs (obs["policy"], raw pre-normalization actor
  input) into data_<level>.npz as key `policy_obs`, shape (T, num_envs, policy_obs_dim).
- `--save-action-std` stores the per-step action std as key `action_std`, shape (T, num_envs, action_dim).

Implementation is purely ADDITIVE and verified by opus code-review (8/8 adversarial checks PASS):
non-sampling (reuses the deterministic act_inference action; reads .action_std after
_update_distribution(mean) which only builds Normal(mean, exp(log_std)) -- never .act()/.sample());
detached-cpu-numpy so the arrays survive write_eval_npz's isinstance(np.ndarray) filter (NOT silent
no-ops); byte-identical default output when both flags are off.

CAVEAT for the state_dependent_std retry (the consumer this unblocks): action_std here is exact ONLY
because THIS baseline uses a GLOBAL log_std (state-independent). A future state-dependent-std head
computes std from obs, so its per-state std must be reconstructed OFFLINE from the stored raw
`policy_obs` (which is why logging the raw obs, not just action_std, was the load-bearing half) --
do NOT trust the stored `action_std` for a state-dependent head. See
[[state_dependent_std_robustness_vs_nominal_trade_off_not_difficul]].

