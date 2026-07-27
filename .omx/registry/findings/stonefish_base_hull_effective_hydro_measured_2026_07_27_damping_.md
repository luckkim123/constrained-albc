---
title: "Stonefish base-hull effective hydro MEASURED (2026-07-27): damping is the gap axis (yaw ~45-100x, pitch-linear ~10x, translational 3-8x under nominal); effective added inertia already matches; nominals recentered on marinelab exp/hydro-recenter"
tags: ["stonefish", "hydrodynamics", "system-id", "damping", "added-mass", "sim-to-real", "domain-randomization", "decay-test"]
created: 2026-07-27T08:42:33.953196
updated: 2026-07-27T08:42:33.953196
sources: ["vault:krit/simulator/docs/stonefish-hydro-measurement-2026-07-27.md", "marinelab:exp/hydro-recenter@016d1b1", "stonefish_dev:/tmp/hydro"]
links: []
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
---

# Stonefish base-hull effective hydro MEASURED (2026-07-27): damping is the gap axis (yaw ~45-100x, pitch-linear ~10x, translational 3-8x under nominal); effective added inertia already matches; nominals recentered on marinelab exp/hydro-recenter

Base-only system-ID rig in stonefish_dev (deployment hull geometry: cylinder r=0.09 h=0.3105 + gripper stand-off, neutral mass trim 7.886 kg, cg z=+0.05 kept, 60 m depth, freshwater 998). Thruster-step terminal velocity (absolute drag, ThrusterState reported thrust = applied force, no thrust-model assumption) + release decay (effective mass) + static-tilt restoring k + free-decay oscillation (pitch I+A, c1, c2) + spin-down (yaw ratios). Purity via empirically-solved combos (onset-accel B matrix); heave up/down symmetric; fits trim-robust (rotor spin-down tail excluded: means shift <1%).

MEASURED vs ALBCHydrodynamicsCfg nominal (base body):
- yaw: c1 0.0012-0.0026 / c2 0.0094-0.0116 vs nominal 0.15 / 0.5 -> ~45-100x under. c2/I=0.224 consistent over 4 amplitudes.
- pitch: c1 ~0-0.06 (=~0) / c2 1.0-1.2 vs 0.3 / 1.0; measured k 3.06-3.62 N.m/rad (analytic W*BG 4.27, -15~28% seam unresolved).
- surge/sway: c2 ~7.6-11.5 / 4.9-7.4 vs 39 (3-8x under); absolute scale banded on A_surge theory (slender-body 8.25 outside validity at L/D 1.7 -> band [4,10]).
- heave: c1 1.61 / c2 22.7 vs 1.5 / 15 (comparable); A = 15.0+-0.3 kg vs nominal 1.0.
- ADDED-INERTIA KEY CORRECTION: added_mass_stability_factor 0.5 ATTENUATES the applied added-mass force (hydrodynamics.py:361), so Isaac EFFECTIVE inertia = I_rigid + 0.5*A_nominal. Effective-vs-effective: pitch 0.133-0.148 (SF) vs 0.144 (Isaac), yaw 0.042-0.052 vs 0.055, surge band 11.9-17.9 vs 13.2 -> NO gap on rotational/translational added inertia; only heave gaps (22.9 vs 9.68).

APPLIED (marinelab exp/hydro-recenter 016d1b1, stacked on B0c f45d612; DR relative ranges untouched):
linear_damping (2,2,1.5,0.3,0.3,0.15)->(0.5,0.5,1.6,0.03,0.03,0.002); quadratic_damping (39,39,15,1,1,0.5)->(8.0,8.0,22.7,1.2,1.2,0.011); added_mass heave 1.0->8.0 (measured 15.0, hard cap M_a<body_mass 9.18 binds, surge-precedent ratio 0.87). Rotational added mass KEPT (effective match). volume/cg/cob unchanged (engine displaced volume 7901.3 cm3 = cfg 0.00790 exactly).

CAVEATS: (a) recentered yaw band [0.4,1.7]x0.011 excludes the old analytical 0.5 entirely - this is an explicit Stonefish-transfer choice, Stonefish is NOT ground truth (see stonefish_yaw_gap page caveat); real-vehicle anchoring stays the band strategy (sim_hydro page). (b) buoy (link2/ABPC) hydro NOT measured (base-only rig) - the buoy added-mass ~10x-under lead stays open. (c) thruster reported-thrust sign convention seam (m2/m5 negative at +pwm) and odom-frame ambiguity documented in the vault doc. (d) Stonefish long-run degradation: physics stall after ~170 s continuous headless run - restart per family (133-175 s runs clean).

