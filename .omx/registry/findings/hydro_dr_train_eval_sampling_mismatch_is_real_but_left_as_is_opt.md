---
title: "hydro DR train/eval sampling mismatch is REAL but left as-is (option C): train scalar->6-axis broadcast, eval 6-axis independent"
tags: ["hydro", "domain-randomization", "doraemon", "eval", "train-eval-mismatch", "variance-analysis", "added_mass", "damping"]
created: 2026-07-07T07:55:02.624957
updated: 2026-07-07T07:55:02.624957
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# hydro DR train/eval sampling mismatch is REAL but left as-is (option C): train scalar->6-axis broadcast, eval 6-axis independent

DECISION (2026-07-07, user-approved option C): the hydro DR train/eval sampling mismatch is REAL and confirmed in code, but LEFT AS-IS (no code change). eval keeps its stricter axis-independent OOD; the mismatch is documented here so eval variance analysis can discount hydro-driven env-spread as a sampling artifact rather than mis-attributing it to policy sensitivity.

## The mismatch (code-confirmed)

For the three hydro scales `added_mass_scale`, `linear_damping_scale`, `quadratic_damping_scale`:

- TRAIN (DORAEMON on): a SINGLE scalar per env is sampled from the learned Beta distribution and broadcast to all 6 axes -- `val.unsqueeze(-1).expand(-1, 6)`. Every env sees "all 6 axes scaled by the same factor". Path: `albc_env.py:1386-1398` fills `sampled` dict -> `events.py:57-58` (`_sample_or_uniform`, broadcast_dim=6) -> `events.py:198/205/211`.
- EVAL (`eval.py static`): DORAEMON is disabled (`eval.py:904-905` sets `env_cfg.doraemon.enable=False` -> `albc_env.py:435` `self._doraemon=None`), so `sampled` stays None at reset (`albc_env.py:1386`) and the fallback `_rand_uniform_range((n,6), ...)` samples all 6 AXES INDEPENDENTLY -- `events.py:60`. mid-episode eval path also passes `sampled=None` explicitly (`eval.py:362-364`).

Result: eval feeds the policy 6-axis-decorrelated hydro tensors that NEVER appear in the training distribution. Same range, different axis-correlation structure. eval is structurally harder + axis-decorrelated on these three scales.

## Two overlapping layers

1. Axis-correlation mismatch (the structural one): train = single scalar broadcast to 6; eval = 6 independent draws.
2. Distribution-shape mismatch: train draws from the learned Beta (curriculum moves mean/std); eval draws uniform from the fixed cfg tuple range. `--doraemon-dr` only re-sets the hard-level tuple range to DORAEMON mean+-2std but still samples uniform 6-axis-independent -- it does NOT restore the Beta shape or the scalar-broadcast structure.

## Why this is NOT a simple bug (do not "just fix" it)

DORAEMON maps each `_PARAM_DEFS` entry (`doraemon.py:41-62`) to ONE Beta dimension. The three hydro scales are 3 scalar dims total. Making train 6-axis-independent (prompt option A) means expanding DORAEMON from 3 dims to 18 dims (3 scales x 6 axes) -- a curriculum redesign requiring a from-scratch retrain, functionally identical to the "per-axis independent hydro DR experiment". So train-broadcast is the FORCED consequence of DORAEMON's scalar-dimension design, not an oversight.

## Not affected

- yaw-specific quadratic damping (index 5) is uniform in BOTH train and eval (`events.py:214`, `dr.get` ignores `sampled`).
- deterministic-dr eval collapses ranges to midpoint so all 6 axes take the same fixed value (`eval.py:992-994`).

## How to apply

When reading eval variance (per-env CV, heavy-tail vs sample-mean divergence per `.claude/rules/03`): part of the env-to-env spread on runs sensitive to added_mass/linear/quadratic damping is a SAMPLING ARTIFACT of this train(scalar-broadcast) vs eval(6-axis-independent) mismatch, NOT a policy property. Do not conclude "policy is sensitive to hydro" from eval env-spread alone on these three channels without accounting for this. Options B (make eval scalar-broadcast too, simple, but breaks byte-comparability with past evals) and A (18-dim DORAEMON, retrain) remain available if this artifact ever needs elimination rather than discounting.

## Related

Overlaps with the "per-axis independent hydro DR experiment" prompt (option A = that experiment) and the added_mass-comment-correction prompt. This diagnosis was the gate: option C chosen means the per-axis experiment is NOT triggered by this finding.

