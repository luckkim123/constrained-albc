---
title: "added_mass_scale upper half is INERT: post-DR 0.95*I clamp caps it (yaw eff bound ~1.01), so hydro DR cannot be widened up"
tags: []
created: 2026-07-07T08:10:49.201758
updated: 2026-07-07T18:41:50.848338
sources: []
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# added_mass_scale upper half is INERT: post-DR 0.95*I clamp caps it (yaw eff bound ~1.01), so hydro DR cannot be widened up

DORAEMON's `added_mass_scale=(0.5,1.5)` looks like a free +-50% band but the UPPER HALF is largely INERT: a post-DR per-axis clamp caps added mass at `0.95 * generalized_inertia` (`constrained_albc/envs/main/mdp/events.py:260-271`), and nominal added mass is already pressed against the rigid-body inertia ceiling on this small vehicle. This is the single most important fact for any "widen hydro DR" decision.

## The clamp arithmetic (per axis, main body)

Base added_mass (marinelab `assets/albc/albc.py:52`) and rigid_body_inertia give the effective ceiling `0.95 * I`, so the max usable scale is `0.95*I / base_added_mass`:

| axis | base M_a | I_rigid | ceiling 0.95*I | max effective scale |
|:---|---:|---:|---:|---:|
| yaw | 0.035 | 0.0372 | 0.0353 | ~1.01 |
| roll/pitch | 0.09 | 0.0994 | 0.0944 | ~1.05 |
| surge/sway | 8.0 | 9.18 (body_mass) | 8.72 | ~1.09 |

So on the rotational axes ANY `added_mass_scale > ~1.01-1.05` is silently clamped away. The policy effectively trains against added_mass in roughly `[0.5, ~1.05]`, NOT `[0.5, 1.5]`. The base yaw added_mass is already 94% of yaw inertia (`albc.py` comment "yaw M_a/I=0.94"; surge "capped from theory 8.25->8.0").

## Why this blocks the "widen for robustness" intuition

The clamp is an EXPLICIT-INTEGRATION STABILITY device, not conservatism: forward-Euler diverges when added mass exceeds rigid-body inertia, so `M_a[i] < I_rigid[i]` is validated at init (`marinelab/core/hydrodynamics.py:189-227`) and enforced per-reset (`events.py:260-271`). Widening `added_mass_scale` UP is physically meaningless (clamped) and cannot be done without first raising base rigid-body inertia -- a vehicle-model change. The LOW tail (0.5-1.0) is meaningful and fully exercised. Verdict (2026-07-07 architect review): KEEP the range; the `config.py:142-145` comment claiming a free +-50% is MISLEADING and should note the clamp-limited effective upper bound (prompt: PROMPT_added_mass_clamp_comment_fix.md).

## Contrast: damping ranges ARE well-justified

`linear_damping_scale`/`quadratic_damping_scale=(0.4,1.7)` are NOT clamp-limited and sit inside credible UUV damping identification uncertainty (damping is the least-reliably-identified hydro term; quadratic/form drag the most). architect verdict: KEEP both, do NOT widen. No hydro scale has evidence supporting a widening. See [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] (nominal is Fossen-analytical, not measured) and [[hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt]].

---

## Update (2026-07-07T08:12:42.891840)

CORRECTION (2026-07-07, reconciled with committed DR doc e1b3bca): the clamp ceiling `0.95 * I` is NOT a fixed constant, because `inertia_scale=(0.4,2.0)` is ITSELF domain-randomized (`_PARAM_DEFS` index 12). So `I` (hence the ceiling) is a RANDOM VARIABLE co-sampled each reset. My earlier "yaw effective bound ~1.01, upper half INERT/dead" is too absolute -- correct that to ATTENUATED, not eliminated.

Accurate statement (from committed `config.py` comment, envs/main + full_dof, e1b3bca): at the curriculum-saturated Beta(1,1)=UNIFORM endpoint, ~35-50% of scale>1 draws are clamped on ROTATIONAL axes (~76% on surge/sway); mean realized added_mass_scale is ~0.87. The high tail SURVIVES when a large `inertia_scale` is co-sampled -- so the upper tail of `added_mass_scale` is ATTENUATED, NOT eliminated. The "~1.01/~1.05/~1.09 effective ceiling" figures in the table above are the ceilings at NOMINAL inertia only (inertia_scale=1.0); with inertia_scale up to 2.0 the ceiling roughly doubles, letting some high-scale draws through.

The load-bearing conclusion is unchanged: (1) the clamp is a real explicit-integration stability device, (2) you still cannot freely "widen added_mass up for robustness" -- the up-side is heavily attenuated and coupled to inertia_scale, not a free parameter -- but (3) it is NOT a hard dead-zone; the attenuation is probabilistic and inertia-dependent. The `PROMPT_added_mass_clamp_comment_fix.md` prompt is now SUPERSEDED: commit e1b3bca already added this (more accurate) clarification to both configs. Do not re-run that prompt.

---

## Update (2026-07-07T18:41:50.848338)

## CORRECTION (2026-07-08): the clamp ceiling is a RANDOM VARIABLE, not a constant — "attenuated", not "dead/inert"

The "yaw eff bound ~1.01", "INERT upper half", and the fixed-ceiling table above are computed at
`inertia_scale = 1.0` and OVERSTATE the effect. `inertia_scale` is itself DR'd over `(0.4, 2.0)`
(config.py `DomainRandomizationCfg`), and the clamp is `0.95 * (DR-randomized) rigid-body inertia`
(events.py:260-271). So the effective ceiling is a **random variable co-sampled with the added_mass
draw**, not the constant this card's table implies.

Corrected characterization (matches committed code doc `e1b3bca` on the DomainRandomizationCfg docstring):
- At the curriculum-saturated Beta(1,1)=UNIFORM endpoint, ~35-50% of `scale>1` draws are clamped on the
  ROTATIONAL axes (~76% on surge/sway), and the mean *realized* `added_mass_scale` is ~0.87.
- The high tail (scale ~1.5) SURVIVES when a large `inertia_scale` is co-sampled — so the upper half is
  **ATTENUATED, not eliminated**. Saying it is "dead/inert" is the over-assertion (rules/03 "No Premature
  Assertions"); the original error was treating the `inertia_scale=1` ceiling as fixed.

The load-bearing conclusion is UNCHANGED: raising `added_mass_scale`'s upper bound ALONE has diminishing
effect (you'd also have to raise base rigid-body inertia = a vehicle-model change), and the low tail
(0.5-1.0) is fully exercised. So "don't widen hydro added_mass up" still holds — just for the accurate
reason (attenuated tail + co-sampled ceiling), not "the upper half is dead".

