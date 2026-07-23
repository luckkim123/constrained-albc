---
title: "Adding a DR axis is half a change: dr_config's _DR_TUPLE_FIELDS / _TRUE_NOMINAL_PHYSICS must both register it or the none level silently keeps the training band"
tags: ["domain-randomization", "dr_config", "eval-protocol", "none-level", "silent-failure", "checklist", "B0c", "max_thrust"]
created: 2026-07-23T11:15:10.115662
updated: 2026-07-23T11:15:10.115662
sources: ["dr_config.py:309-314", "dr_config.py:341-343", "B0c-implementation-260723"]
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Adding a DR axis is half a change: dr_config's _DR_TUPLE_FIELDS / _TRUE_NOMINAL_PHYSICS must both register it or the none level silently keeps the training band

Adding a DR axis to `DomainRandomizationCfg` is only HALF the change. The eval side keeps
its own two explicit registries in `constrained_albc/analysis/dr_config.py`, and a field
missing from them is silently mis-graded rather than erroring.

MECHANISM (verified 2026-07-23 while implementing campaign B0c's max_thrust band):
- `build_dr_config(scale)` short-circuits at `scale <= 0.0` and returns `_make_nominal_dr()`
  verbatim (`dr_config.py:341-343`). That IS the `none` eval level.
- `_make_nominal_dr()` starts from a fresh `DomainRandomizationCfg()` (`:309`) -- i.e. the
  TRAINING defaults -- and then overwrites ONLY the fields listed in `_DR_TUPLE_FIELDS`,
  using the value from `_TRUE_NOMINAL_PHYSICS` when present (`:311-314`).
- Consequence: a cfg field absent from `_DR_TUPLE_FIELDS` is never touched at ANY level. It
  keeps its full training range even at `none`.

WHY THAT IS WORSE THAN IT SOUNDS: `none` is the level every cross-run verdict is read at
(campaign rule: verdicts are none-only). A new-axis policy graded with its band still live,
against a baseline graded at the fixed nominal, is a DIFFERENT-EXAM comparison wearing the
costume of a paired one. It produces a plausible number with no error message.

NO GUARD EXISTS. `tests/test_dr_config.py` asserts per-axis (`test_payload_cog_offset_xy_u_
range_sweeps_with_dr_level`, `test_obs_noise_scale_range_sweeps_with_dr_level`) -- one
hand-written test per axis, added by whoever remembered. Nothing asserts that the two
registries cover the cfg's tuple fields, so the failure mode is available to every future
axis. A single completeness test over `DomainRandomizationCfg`'s tuple fields would close
the class instead of the instance; flagged, not implemented (2026-07-23).

CHECKLIST when adding a DR axis (all four, or the eval is wrong):
1. field on `DomainRandomizationCfg` (`envs/main/config.py`)
2. applied in the env/actuator path -- and at EVERY call site (albc_env.py has TWO
   `randomize_parameters` calls, reset and mid-episode; fixing one desyncs them)
3. `_DR_TUPLE_FIELDS` in `dr_config.py`
4. `_TRUE_NOMINAL_PHYSICS` in `dr_config.py` with the physics-true nominal (scale fields
   -> 1.0, offset fields -> 0.0)

SIDE EFFECT ON OLD POLICIES, distinct from the above: `load_doraemon_dr` starts
non-DORAEMON (thruster/joint) parameters from the class-default cfg so that "the eval
matches the physics ranges actually seen during training". Once a NEW axis has a non-identity
class default, that promise breaks for every PRE-existing policy: re-evaluating an older
checkpoint at soft/medium/hard applies a band it never trained on, so its numbers will not
reproduce its original eval. `none` is unaffected (the band collapses), which is why the
none-only verdict rule contains the damage. A proper fix would source each axis's band from
the run's own saved `params/env.yaml` instead of the class default.

RELATED: this is the same failure family as the eval-path obs-width bug found by C0.4 on
2026-07-23 (`eval.py` routed non-encoder arms to a runner with no obs-width sync) -- in both
cases the TRAINING side was correct and the EVAL side silently disagreed with it. When adding
anything to the training config, ask what the eval path does with it.

