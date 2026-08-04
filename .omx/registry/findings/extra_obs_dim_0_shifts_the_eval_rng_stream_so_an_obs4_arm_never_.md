---
title: "extra_obs_dim>0 shifts the eval RNG stream so an obs4 arm never shares env draws with a pre-obs4 run, but a dim=0 control on the same commit is byte-identical to one"
tags: ["obs4", "extra-obs", "pairing", "eval", "rng", "depth-noise", "student"]
created: 2026-08-03T13:53:44.575649
updated: 2026-08-04T06:38:08.159827
sources: ["diagnose-20260803-223517"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 70
qualityReasons: ["no-source-marker", "generic-only-tags"]
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

---

## Update (2026-08-04T06:38:08.159827)

CORRECTION 2026-08-04 (eval.py 9eac3a8): the "never paired" consequence is SUPERSEDED for the per-env DR draws. The measurement above was taken on pre-fix eval.py, where TWO mechanisms desynchronised the stream at once and could not be told apart: (1) per-step depth_noise_std consumption, described here, and (2) policy-build weight-init consumption, which differs whenever the compared runs build different policies (72D vs 76D actor, student GRU vs teacher MLP). Mechanism (2) was the dominant one for the dr_* arrays and is now removed by a per-level torch.manual_seed(seed + level_index) in run_static, placed AFTER the policy build and immediately BEFORE the level rollout.

Because the per-env DR values are drawn at the level reset - right after that reseed and before any per-step sensor noise is consumed - they are now identical across runs regardless of obs4 state. Verified on five evals spanning exactly the boundary this page says cannot be crossed: E-int teacher (no extra channels) / obs76 teacher (use_extra_policy_obs, depth noise drawing) / C3 student / Phase E gen-2 student / X1 tail-split student, all at seed 42 with the same --doraemon-dr-from: 24/24 dr and fault arrays elementwise identical at none, soft, medium AND hard.

What REMAINS true: mechanism (1) is real - depth_noise_std=0.01 still consumes RNG from step 1 on, so the per-step noise SEQUENCES differ between an obs4-active and an obs4-inactive run, and two policies visit different states anyway. Pairing here means the 64 environment INSTANCES are the same, which is what the paired decision floors require; it never meant identical trajectories.

PRACTICAL EFFECT: the 0.0533 half-split difference sd and the "distribution-level, never paired" rule no longer apply to obs4 comparisons run on eval.py at or after 9eac3a8 with the same seed and --doraemon-dr-from. The registered PAIRED floors (ss_error 0.10 deg, ss_error_std 0.60 deg, survival 1.6 pp, n_gt20 15 envs) apply instead. The X1-tailsplit proposal anticipated this in its own validity gate ("if draws unexpectedly match, paired floors apply instead") and was analysed under the paired floors. Any comparison whose evals PRE-DATE the fix is still unpaired and must be re-run, not re-graded.
