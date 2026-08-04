---
title: "eval.py rebuilds env cfg from Hydra defaults, so obs-widening flags must be re-passed at eval time"
tags: ["eval", "trap", "hydra", "observation-space", "koopman"]
created: 2026-08-04T16:32:10.561739
updated: 2026-08-04T17:34:34.744754
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
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

---

## Update (2026-08-04T17:34:34.744754)

## The mirror-image case, measured 2026-08-05 02:07: a setting that a LOUD failure would not have caught

The instance above fails LOUDLY -- a state_dict size mismatch in 16 seconds. The same class of
trap also has a SILENT form, and it cost an hour of GPU1 before it was noticed.

`eval.py static --control-delay N` has a dedicated flag for injecting transport delay. I bypassed it
and passed the underlying config path as a Hydra override instead:
`env.randomization.control_delay_steps=[1,1]`. The command was accepted, exited 0, and produced a
complete-looking 4-level eval. It had injected nothing.

The mechanism is one layer deeper than the obs case. `apply_dr_config()` **rebuilds the whole
`randomization` config** -- once before env creation (`eval.py:1308`) and again at every DR level --
and `control_delay_steps` is not a `_DR_TUPLE_FIELDS` dim, so each rebuild reverts it to its
dataclass default `(0, 0)`. The Hydra override was applied and then overwritten three or four times.
`eval.py`'s own `--control-delay` help text calls the delay-off condition "byte-identical to stock",
which is exactly what the run produced -- the identity WAS the signature of a dead injector.

Detection: `data_hard.npz` was elementwise identical to the stock baseline across all 40 keys.
Nothing else would have shown it.

The correct instrument re-sets the value in BOTH places (`eval.py:1309-1317` before `env.__init__`
so the `DelayBuffer` is allocated at all, and `1462-1468` after each per-level `apply_dr_config`),
and the code comment at 1312-1314 documents this precise trap. The instrument was right; the
invocation was wrong.

GENERALISED RULE, which is the part worth carrying: **when a dedicated CLI flag exists for a
setting, use the flag, not the Hydra path it writes to.** The flag exists because someone already
discovered that the naive path gets rebuilt. Reaching past it to the underlying config key looks
equivalent and is not. Two independent settings in this one file behave this way, and only one of
them fails loudly.

[EVIDENCE: elementwise npz comparison of eval/static_260805_014845 against stock baseline
static_260804_203719, 40/40 keys identical; eval.py:1308/1315-1317/1462-1468 read at HEAD;
both VOID output dirs carry a VOID.txt on disk. Code-exec 2026-08-05.]
[CONFIDENCE: HIGH]
