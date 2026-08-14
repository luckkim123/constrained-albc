---
title: "Proving a run on a divergent branch is still on the reference plant"
tags: ["plant-parity", "branch-hygiene", "config-audit", "teacher"]
created: 2026-08-09T07:32:36.478252
updated: 2026-08-09T07:32:36.478252
sources: []
links: []
category: convention
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Proving a run on a divergent branch is still on the reference plant

A run launched from a feature branch can be uncomparable to the incumbent without anything in
the launch command saying so. Arm W (`trpo_rampw_kl006_s30_260809_161913`) was launched from
`exp/koopman-marine-obs`, which is +45,849 lines over `main` and touches the teacher env files
directly (`envs/main/config.py` +168, `albc_env.py` +192, `mdp/observations.py` +119, new
`mdp/koopman.py`). The G1 flag check (obs 72, `use_extra_policy_obs: false`) does not settle it:
it only covers the flags you thought to look at.

Two checks settle it, and both are cheap.

**Config parity.** Flat-compare the run's dumped `params/env.yaml` against the incumbent run's
`config/env.yaml`, key by key, after dropping pickled buffers (stringify, then skip values over
~120 chars) and the knobs you meant to change. Arm W vs
`teacher_iter_budget/trpo_iterbudget_s30_260805_012813`: 367 keys, 1 difference —
`koopman_module_path`, absent in the incumbent and empty in the new run. A new field defaulting
to off. Script: `/workspace/constrained-albc/scripts/plantdiff.py <ref-glob> <run-glob>`. Note the values include torch
tensors, so compare their `str()`, not the objects (`Boolean value of Tensor with more than one
value is ambiguous`).

**Code parity.** Identical config does not mean identical code — a changed line inside an
always-on function is invisible to a config diff. `git diff --numstat <base> <head> -- envs/`
and read every file with a non-zero delete count. For this branch, every teacher-path file was
a pure addition except `albc_env.py` (3 deletions), and all three were cosmetic: two imports
rewritten as parenthesized multi-line, one f-string in a `ValueError` message.

Pick the reference run by what the decision compares against — the incumbent — not by
whichever run is most recent. `teacher_baseline_buoyfix/trpo_hydrorc_s30_260728_013136` looks
like the natural reference and is wrong: it predates the 2026-07-30 retraction and still
carries `added_mass` heave `8.0`, since reverted to `1.0`. Diffing against it reports a plant
difference that does not exist, and the false alarm costs more than the check.
