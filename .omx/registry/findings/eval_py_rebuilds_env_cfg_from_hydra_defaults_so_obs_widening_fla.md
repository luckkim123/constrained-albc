---
title: "eval.py rebuilds env cfg from Hydra defaults, so obs-widening flags must be re-passed at eval time"
tags: ["eval", "trap", "hydra", "observation-space", "koopman"]
created: 2026-08-04T16:32:10.561739
updated: 2026-08-04T16:32:10.561739
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 80
qualityReasons: ["no-source-marker"]
status: resolved
---

# eval.py rebuilds env cfg from Hydra defaults, so obs-widening flags must be re-passed at eval time

eval.py restores agent.yaml from the run directory but builds the ENV config from Hydra
defaults plus the CLI. It does NOT restore the run's params/env.yaml. So any env flag that
widened the observation during training must be re-passed on the eval command line, or the
env is built at the wrong width and the checkpoint fails to load.

Measured instance, 2026-08-05 01:28. Evaluating the Koopman arm B checkpoint
(trpo_koopmanB_260804_202709, trained with use_marine_feature_obs=True, obs 72 -> 79) without
re-passing the flag died in 16 seconds:

    RuntimeError: Error(s) in loading state_dict for ActorCriticEncoder:
      size mismatch for actor.0.weight: checkpoint torch.Size([256, 88]) vs model [256, 81]
      size mismatch for critic.0.weight: checkpoint torch.Size([512, 116]) vs model [512, 109]

Both gaps are exactly 7 = MARINE_FEATURE_DIM. The arithmetic confirms the diagnosis rather
than just suggesting it: actor input is policy_obs + encoder latent (79 + 9 = 88 vs 72 + 9 =
81) and critic input is policy_obs + privileged + latent (79 + 28 + 9 = 116 vs 72 + 28 + 9 =
109).

Fix: append the flag to the eval command, e.g. env.use_marine_feature_obs=True.

This is the SAME CLASS of trap as env.fault.enable=True on a resumed training launch, and it
is worth naming as a class rather than as two separate facts: **a config-derived plant or
observation setting is not carried by a checkpoint. Anything the run set via CLI at train time
must be set again at eval time and at resume time.** The fault-flag version of this trap voided
a 4.9 hour run because it fails SILENTLY -- a fault-disabled plant trains perfectly happily.
The obs-width version fails loudly with a size mismatch, which is the one mercy: it cannot
produce a wrong result, only no result.

Practical rule when writing an eval command for any run: diff the run's params/env.yaml against
the task defaults, and re-pass every difference that is not log_dir.

