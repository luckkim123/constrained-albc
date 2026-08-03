---
title: "extra_obs_dim>0 shifts the eval RNG stream so an obs4 arm never shares env draws with a pre-obs4 run, but a dim=0 control on the same commit is byte-identical to one"
tags: ["obs4", "extra-obs", "pairing", "eval", "rng", "depth-noise", "student"]
created: 2026-08-03T13:53:44.575649
updated: 2026-08-03T13:53:44.575649
sources: ["diagnose-20260803-223517"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
---

# extra_obs_dim>0 shifts the eval RNG stream so an obs4 arm never shares env draws with a pre-obs4 run, but a dim=0 control on the same commit is byte-identical to one

Measured 2026-08-03 by comparing all 23 dr_* per-env draw arrays in data_hard.npz across three evals.
Decides which difference sd applies to any obs4 comparison, so settle it BEFORE reading the result --
deciding afterwards is threshold-tuning against the answer.

  B2 (extra_obs_dim 4) vs C3          0 / 23 arrays identical  -> INDEPENDENT draws
  B2 (extra_obs_dim 4) vs dim=0 CTL   0 / 23 arrays identical  -> INDEPENDENT draws
  dim=0 CTL vs C3                    23 / 23 arrays identical  -> IDENTICAL draws (paired)

MECHANISM: depth_noise_std (default 0.01, nonzero) is the ONLY new RNG consumer the obs4 channels
introduce; accel_noise_std defaults to 0.0 so the IMU branch draws nothing. Its draws fire on sensor
sample boundaries AFTER compute_policy_obs inside _get_observations, so step 0 still matches but the
stream shifts from step 1 on and the arms then visit different states at the same seed. At
extra_obs_dim 0 the publish is gated off entirely (the env never calls compute_student_extra_obs),
so no RNG is consumed and a dim=0 run on a LATER commit reproduces an older run's env draws exactly.

CONSEQUENCES:
- An obs4-vs-baseline comparison is DISTRIBUTION-LEVEL, never paired. Do not describe it as "the same
  trajectories plus four channels" in any report.
- The 0.0533 difference sd (400 half-splits of the 64 eval envs) applies as written to that leg.
- A dim=0 control is therefore a genuinely free paired baseline: same env draws, so its difference
  from an older run isolates the CODE STATE alone. That is what proved C3's dirty-tree diff inert.
- env.depth_noise_std=0 would restore pairing at the cost of an unrealistically clean heave channel,
  weakening the deployability claim the channels exist to test. Keeping 0.01 is the adopted choice.

