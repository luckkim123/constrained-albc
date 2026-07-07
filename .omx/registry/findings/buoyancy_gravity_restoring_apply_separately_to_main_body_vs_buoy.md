---
title: "buoyancy/gravity/restoring apply SEPARATELY to main body vs buoy(link3); gravity HAS DR (body_mass_scale+payload_mass); DR is body-shared not independent"
tags: []
created: 2026-07-07T08:11:25.359795
updated: 2026-07-07T08:11:25.359795
sources: []
links: ["hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt.md", "uniform_only_dr_full_roster_9_params_doraemon_bypassing_payload.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# buoyancy/gravity/restoring apply SEPARATELY to main body vs buoy(link3); gravity HAS DR (body_mass_scale+payload_mass); DR is body-shared not independent

The ALBC vehicle runs TWO independent hydrodynamics models -- main body (`env._hydro`, `ALBCHydrodynamicsCfg`, body="base") and the buoyancy float (`env._buoy_hydro`, `ALBCBuoyHydrodynamicsCfg`, body="link3"/ABPC). Buoyancy, weight, and restoring moment are computed and applied SEPARATELY per body, each onto its own rigid link. Wiring: `albc_env.py:213-229`, cfg at `config.py:376-377`.

## Buoyancy: per-body, DR-shared

Each body computes `F_b = rho*g*V` from its OWN volume/density (main V=0.009, buoy V=0.00268; both rho=998; `albc.py:64,74,120,130`). Forces set independently: main -> "base" (`albc_env.py:822-841`), buoy -> "link3" (`albc_env.py:843-854`). DR: `_randomize_hydro_model` is called for BOTH bodies with the SAME `sampled` dict (`events.py:280-283`), so DORAEMON params (volume_scale, water_density, cob/cog offsets) are SHARED -- one env's "main volume x1.1" forces "buoy volume x1.1" too. Same scale, different base -> different absolute buoyancy. Non-DORAEMON params (e.g. yaw_damping_scale via `dr.get`) are independently sampled per body.

## Gravity (weight) HAS DR -- two channels, asymmetric

Weight is randomized (question "does gravity/mass have DR?" -> YES):
- `body_mass_scale` (DORAEMON, `_PARAM_DEFS` doraemon.py:55; config (0.75,1.25)): scales the actual PhysX rigid-body mass via `get_masses()* scale -> set_masses()` (`events.py:537-544`), broadcast to ALL bodies (main + buoy). PhysX applies gravity to that mass (`disable_gravity=False`, `albc.py:175`), so weight changes. Hydro cfg `body_mass` (main 9.18, buoy 0.93) is only for CoG-correction torque + damping clamp, NOT the weight itself.
- `payload_mass` (DORAEMON, doraemon.py:42; config (0,3) kg): NOT a PhysX mass change -- applied as an external weight wrench on the GRIPPER body only (`albc_env.py:864-876`, `payload_mass * gravity_vec`). Independent channel, not on main/buoy.
- Gravity CONSTANT g and the gravity vector are NOT randomized: `self._gravity=9.81` hardcoded (`hydrodynamics.py:159`); sim gravity is read-only (`albc_env.py:208`). water_density affects buoyancy ONLY, never weight.

## Restoring moment: per-body CoB/CoG, role-split

Each body makes its own restoring moment from its own CoB/CoG (`hydrodynamics.py:501` `cross(r_cb, F_b)` + `:507-510` CoG-offset correction torque). Nominal:
- main: CoB=(0,0,0), CoG=(0,0,-0.05) -- DELIBERATELY offset -> this is what generates the static righting moment (`albc.py:69,72`).
- buoy: CoB=CoG=(0,0,0.059) -- SAME point (symmetric short cylinder) -> ZERO self-restoring; the buoy's job is NET POSITIVE BUOYANCY (26.2 N buoyancy vs 9.1 N weight, `albc.py:104`), not righting.
So restoring is done by the MAIN body, net lift by the BUOY. The 0.059 is verified EXACT against `agent.urdf` (`meshes/agent.urdf:173` collision origin, `:179` inertial origin, both xyz="0 0 0.059"; cylinder radius 0.085/length 0.118 also match albc.py comment) -- comment-vs-URDF drift = none. CoB/CoG offset DR (6 axes, doraemon.py:47-53) applies to BOTH bodies with shared sampled values.

## The decorrelation caveat (open, ungated experiment)

Because both bodies share one DORAEMON scale, real-world INDEPENDENT buoyancy error between the two physically-separate parts (main hull vs float, different waterproofing/tolerance) is NOT representable in training -- the same single-scalar-broadcast limit as the per-axis hydro case. Prompt PROMPT_main_buoy_hydro_dr_decorrelation.md proposes splitting volume_scale into `_main`/`_buoy` (NDIMS +1), keeping water_density shared (same tank=same water). GATED: needs eval evidence of main/buoy buoyancy-mismatch failure or a hardware tolerance argument -- do NOT run on intuition. Same decorrelation family as [[hydro_dr_train_eval_sampling_mismatch_is_real_but_left_as_is_opt]]. See also [[uniform_only_dr_full_roster_9_params_doraemon_bypassing_payload]].

