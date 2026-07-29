---
title: "The frozen actor's sensitivity to latent error is strongly level-dependent: hard crosses the control floor at a 4x smaller perturbation than none/soft/medium"
tags: ["student", "latent", "sensitivity", "frozen-actor", "albc", "dr-level", "hard", "c1-latsens", "targeting"]
created: 2026-07-29T09:41:35.895551
updated: 2026-07-29T09:41:35.895551
sources: ["diagnose-20260729-184021"]
links: []
category: pattern
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# The frozen actor's sensitivity to latent error is strongly level-dependent: hard crosses the control floor at a 4x smaller perturbation than none/soft/medium

Measured directly on 2026-07-29 by probe C1-latsens (proposal next-20260729-180058, analysis
diagnose-20260729-184021) on the campaign's adopted arm A0g (`trpo_sdeint_a0g_gru_s30_260729_151017`).
Zero training: the latent handed to the frozen actor was perturbed by `k * sigma_d * N(0,1)` per
dimension, where sigma_d is that student's OWN measured per-dim in-loop RMSE at that DR level, so k=1
means "double the latent error this student already has, in the shape it already has it".

## The curve (att_norm ss_error, deg; floor 0.1)

| level | k=0 | k=0.5 | k=1 | k=2 | k=4 | first floor crossing |
|:--|--:|--:|--:|--:|--:|:--|
| none | 0.5139 | 0.5228 | 0.5625 | 0.7023 | 1.1378 | k=2 |
| soft | 0.4510 | 0.4997 | 0.5327 | 0.6332 | 1.0192 | k=2 |
| medium | 0.5177 | 0.5263 | 0.5853 | 0.8850 | 1.6058 | k=2 |
| hard | 0.6496 | 1.0728 | 1.0905 | 1.5400 | 2.1736 | **k=0.5** |

Monotone at every level. Survival 100% at every level for every k including k=4 -- the degradation is
steady-state and dispersion, not envs dying (roll n_gt20 does not rise, all far below the 15-env floor).

## Damage per unit of injected perturbation (deg per unit of mean ||delta l_hat||)

| level | k=0.5 | k=1 | k=2 | k=4 |
|:--|--:|--:|--:|--:|
| none | 0.036 | 0.098 | 0.189 | 0.313 |
| soft | 0.214 | 0.179 | 0.200 | 0.312 |
| medium | 0.027 | 0.105 | 0.286 | 0.424 |
| hard | 1.070 | 0.558 | 0.563 | 0.482 |

Normalizing matters: sigma is level-dependent, so hard receives a larger absolute perturbation at the
same k. It is still 5x soft and 30-40x none/medium after normalizing. The asymmetry is a SMALL
perturbation property -- by k=4 all four levels converge to 0.31-0.48 -- and small perturbation is
exactly the regime a real intervention operates in. Hard is concave (steep then saturating); none and
medium are convex (flat then steepening).

## Why this matters: it reframes five sub-floor nulls as a TARGETING failure

The campaign's interventions moved latent error where the actor is least sensitive and barely at all
where it is most sensitive. The lambda bracket is the clearest case -- in-loop latent MSE spread across
lambda 0 / 1 / 4:

| level | spread (max/min) | sensitivity (deg per unit, k=0.5) |
|:--|--:|--:|
| none | 2.56x | 0.036 |
| soft | 1.84x | 0.214 |
| medium | 1.47x | 0.027 |
| hard | 1.04x | 1.070 |

Nothing about A0g / B4b / B1a / B1b was mis-designed. They pushed on the insensitive end, and control
verdicts were read across all four levels, three of which cannot resolve a latent change at realistic
magnitudes. This supplies what the campaign's "no arm is adopted on P1/P2 alone" rule was missing: the
exchange rate between latent fidelity and control, which is a different number at every DR level.

## Target and expected payoff for the next arm

Reduce in-loop latent error AT HARD. Local slope there is 1.070 deg per unit ||delta l_hat|| and A0g's
own hard in-loop error is 0.791 units, so halving it projects to roughly -0.42 deg, about 4x the
decision floor. CAVEAT: that extrapolates the smallest measured segment below k=0 on a concave curve,
so it is an estimate rather than a measurement; even a third of it clears the floor.

## Instrument notes (reusable)

- Perturb AFTER the encoder output is published to `last_l_hat` and before `teacher.actor_forward`
  (`student_policy.py`). Perturbing earlier contaminates the latent diagnostic with the probe's noise.
- Bite check used, and it should be the template: k=0 must reproduce the published eval on every
  summary field (it did -- 376/376, zero differences), AND the realized perturbation norm must scale
  with k (it did -- exactly 0.5/1/2/4x). A flat control result is otherwise indistinguishable from a
  dead injector, which this workspace has been burned by twice.
- Run from a tree that HAS commit 38d979e. On main the eval's latent instrument is still the pre-fix
  version and every student latent number it produces is wrong.

