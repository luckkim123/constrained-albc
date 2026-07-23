---
title: "Attitude-only ablation arms registered; policy_obs_dim sync must cover every encoder-capable runner"
tags: ["ablation", "task-registration", "obs-dim", "runner", "comparison-set"]
created: 2026-07-23T05:41:10.849286
updated: 2026-07-23T05:41:10.849286
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Attitude-only ablation arms registered; policy_obs_dim sync must cover every encoder-capable runner

The attitude-only comparison set is now launchable. `envs/main` registers all four
ablation arms alongside the default:

| task id | arm |
|---|---|
| `Isaac-ConstrainedALBC-TRPO-v0` | default: encoder + ConstraintTRPO + IPO |
| `Isaac-ConstrainedALBC-NoEncoder-v0` | TRPO + IPO, no encoder |
| `Isaac-ConstrainedALBC-PPO-v0` | stock PPO + asymmetric critic |
| `Isaac-ConstrainedALBC-TRPO-NoIPO-v0` | encoder + TRPO, IPO off (empty constraints) |
| `Isaac-ConstrainedALBC-PPO-Enc-v0` | encoder + PPO, IPO off |

Only the `gym.register` blocks had been missing -- the runner cfgs,
`ALBCNoConstraintEnvCfg` and the `paths.py` task-short mapping all already existed, so
this was never a design gap, just an unregistered entry point. Ablations write to
`experiment_name = albc_ablation`, a sibling of `albc_trpo_teacher`, so they do not mix
into the teacher tree.

The trap this surfaced, which will bite any future runner: **`envs/main` is 72D, not the
69D its cfg source declares.** `use_bias_ema_obs` (ON since 458eaaa, 2026-07-16) appends
the 3D bias-EMA at cfg-construction time, and `observation_space = 69` in config.py is
deliberately the PRE-bump width that `apply_bias_ema_obs()` validates. Agent cfgs still
carry `policy_obs_dim = 69`; runners are what reconcile it.

Before 2026-07-23 that reconciliation lived only inside `ConstraintEncoderRunner.__init__`,
so PPO-Enc -- which reaches the same encoder policy through `OnPolicyDoraemonRunner` --
aborted at startup with `Policy obs dim 72 != expected 69`. `sync_policy_obs_dim` now
lives in `_core/runners/__init__.py` and both runners call it before `super().__init__()`.
Any new runner that can carry an encoder policy must call it too.

Two consequences worth knowing when reading run provenance:

- A run's saved `params/agent.yaml` records `policy_obs_dim: 69` even though the network
  was built at 72. The dump happens before the runner mutates the cfg dict. This is true
  of every encoder run including the teacher anchors -- do not read the yaml as the built
  width. Read the checkpoint instead: `actor.0.weight` `in_features` is obs + latent
  (81 = 72 + 9; a stale 69 would give 78).
- The sync logs at `logger.info`, which is filtered at the default level, so its absence
  from a training log is not evidence that it did not fire.

Verified 2026-07-23: all five main tasks smoke-pass at 2 iters x 16 envs; full suite
380 passed / 9 skipped; `omx tree-audit` ok with 0 errors.

