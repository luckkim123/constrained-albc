---
title: "added_mass_scale upper half is ATTENUATED, not inert: the 0.95*I clamp ceiling is co-sampled with inertia_scale DR; still do not widen hydro DR up"
tags: ["hydro", "DR", "added-mass", "clamp", "inertia-scale"]
created: 2026-07-23T07:56:32.108870
updated: 2026-07-23T07:56:32.108870
sources: ["wiki-curation-2026-07-23"]
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# added_mass_scale upper half is ATTENUATED, not inert: the 0.95*I clamp ceiling is co-sampled with inertia_scale DR; still do not widen hydro DR up

DORAEMON's added_mass_scale=(0.5,1.5) upper half is heavily ATTENUATED but not dead: a per-reset clamp caps added mass at 0.95 * rigid-body inertia (envs/main/mdp/events.py:260-271, an explicit-integration stability device), and because inertia_scale=(0.4,2.0) is itself DR'd, the ceiling is a RANDOM VARIABLE co-sampled with the added_mass draw. At the Beta(1,1) uniform endpoint ~35-50% of scale>1 draws are clamped on rotational axes (~76% surge/sway); mean realized scale ~0.87; the high tail survives when a large inertia_scale is co-sampled (committed docstring e1b3bca). Load-bearing conclusion: raising added_mass_scale's upper bound ALONE has diminishing effect (a real widening requires raising base rigid-body inertia = vehicle-model change); the low tail (0.5-1.0) is fully exercised — so do not widen hydro added_mass up. Damping scales (0.4,1.7) are NOT clamp-limited and stay as-is. See [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] and [[hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt]]. Retitle note: this page supersedes the page formerly at slug added_mass_scale_upper_half_is_inert_post_dr_0_95_i_clamp_caps_i.md, whose title asserted the retracted absolute claim (INERT / eff bound ~1.01 at nominal inertia only); that page's full history is merged below.
