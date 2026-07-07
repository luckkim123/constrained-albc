---
title: "hydro DR train/eval sampling mismatch is REAL but left as-is (option C): train scalar->6-axis broadcast, eval 6-axis independent"
tags: ["hydro", "domain-randomization", "doraemon", "eval", "train-eval-mismatch", "variance-analysis", "added_mass", "damping"]
created: 2026-07-07T07:55:02.624957
updated: 2026-07-07T08:21:42.923873
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
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

---

## Update (2026-07-07T08:21:42.923873)

GATE VERDICT (2026-07-07, independent review) on the sibling "per-axis independent hydro DR" experiment (PROMPT_per_axis_hydro_dr_experiment.md, = option A of this mismatch): DORMANT, do NOT run. Unlike the main/buoy volume case (absence of evidence), here the eval evidence actively COUNTER-argues the premise:

- Gate 1 (eval axis-decorrelated hydro failure): UNMET and REFUTED. The `trpo_baseline_260608` report analyzed exactly this axis with the rules/03 method and concluded "NO pathological axis decorrelation (sample rank 56%)". The CV explosion (roll 9%->249%) is real but is a low-damping / cog-shifted-env HEAVY-TAIL, NOT hydro axis-decorrelation (heavy-tail != decorrelation, rules/03). Baseline generalizes gracefully, 100% survival. So baseline already refutes the experiment's premise that axis-decorrelated hydro failure exists.
- Gate 2 (user picked option A in this sibling diagnosis): UNMET -- this mismatch is already option C (keep-as-is), no option-A selection.

Additionally, even if a gate opened, the prompt is NOT executable as written -- 3 code defects to fix first:
1. NDIMS is not uniformly 16: full_dof `_PARAM_DEFS`=17 (main=16). The prompt's "16->18" single value is wrong; recompute per-env from `len(_PARAM_DEFS)`.
2. yaw double-randomization: yaw (index 5) is ALREADY separately randomized via `yaw_damping_scale` (uniform-only, `events.py:214`). Grouping roll/pitch/yaw into a "rot" group double-shakes yaw. The rot group must be roll/pitch only.
3. eval fallback is ALREADY 6-axis-independent (`events.py:60`), so the prompt's "eval byte-identity" step 4 (assuming current axis-sharing) has a false premise -> needs redesign.

DORMANT not discarded: if a future eval shows genuine axis-decorrelated hydro heavy-tail, gate 1 opens -- but only a REDESIGNED spec (3 defects fixed) may run. Lesson: a gated experiment prompt is "judge the run-condition", and the run-condition here is refuted, not merely unproven.

