---
title: "Stonefish yaw-gap claim review: main-body hydro yaw torque structurally zero (symmetric added mass kills Munk); PhysX DOES model arm reaction; real gaps = buoy added-mass ~10x under, no arm-link hydro, no yaw-torque DR axis"
tags: ["sim-to-real", "stonefish", "yaw", "hydrodynamics", "munk-moment", "added-mass", "domain-randomization", "arm-reaction"]
created: 2026-07-16T12:56:49.986664
updated: 2026-07-16T12:56:49.986664
sources: []
links: ["sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md", "teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia.md", "buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy.md", "yaw_command_is_rate_not_angle_inherited_design_defensible_only_i.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 100
qualityReasons: []
status: needs-experiment
blocked-on: "P1 cross-sim joint1 swing + P2 eval yaw-torque injection sweep before any training-code change"
---

# Stonefish yaw-gap claim review: main-body hydro yaw torque structurally zero (symmetric added mass kills Munk); PhysX DOES model arm reaction; real gaps = buoy added-mass ~10x under, no arm-link hydro, no yaw-torque DR axis

Code-verified review (2026-07-16) of the Stonefish-transfer claim: "Stonefish has a yaw disturbance Isaac never modeled (arm-swing reaction torque + paddling drag + rotational drag asymmetry), so the policy never learned to fight strong yaw disturbances." Verdict: the CONCLUSION is directionally right, but half the mechanism story is wrong.

CLAIM-BY-CLAIM VERDICT (all against envs/main + marinelab code):
1. "Isaac hydro = per-axis constant damping" -- PARTIALLY RIGHT. Damping is diagonal (hydrodynamics.py:396-398, damping_cross_coupling=None for albc), but the model also computes C_A Coriolis, added-mass force, buoyancy restoring, and applies to TWO bodies: base + buoy/link3 (albc_env.py:255-270).
2. "No geometric coupling -> no yaw disturbance from hydro" -- EXACTLY RIGHT for the main body, by computation: Munk yaw moment = -cross(M_A*v, v)_z = 8.0*u*v - 8.0*v*u = 0 because surge/sway added mass are EQUAL (albc.py:52: (8.0, 8.0, 1.0, 0.09, 0.09, 0.035)). Roll/pitch Munk survives (heave 1.0 != sway 8.0); yaw alone is killed by parameter symmetry. Buoyancy moment z-component is also structurally 0 (r_cb on z-axis). Diagonal damping only opposes yaw rate. So the main-body hydro model CANNOT produce a yaw disturbance torque.
3. "Arm-swing reaction torque (angular momentum conservation) absent in training" -- WRONG. Isaac is a PhysX articulation sim; joint1 (z-axis, agent.urdf:92) drive reaction on the base is modeled exactly. Arm+buoy yaw inertia about joint1 ~ 0.93 kg x (0.3 m)^2 ~ 0.09 kg m^2 ~ 2.4x base Izz (0.0372). The policy trained against this reaction the whole time.
4. "Arm/buoy paddling drag absent" -- PARTIALLY RIGHT. The buoy (link3) has its own hydro model fed with the BUOY LINK's velocity (albc_env.py:959-962), so buoy sweep drag IS modeled at roughly the analytical magnitude (quad 10 vs cylinder estimate ~11.7). What IS missing: (a) link1/link2 have no hydro at all (slender, small), (b) buoy added mass is effectively ~10x UNDER: theory 2.67 kg -> stability cap 0.7 (albc.py:110) -> added_mass_stability_factor 0.4 (albc.py:143) -> effective ~0.28 kg. Two individually-legitimate stability guards multiply into a large model distortion.
5. "Rotational drag asymmetry absent" -- RIGHT. Diagonal damping + axisymmetric constants mean appendage asymmetry (gripper, thrusters, cable) produces zero yaw coupling in sim.
6. "Policy held yaw with weak Mz" -- SUPPORTED quantitatively. Training-world steady yaw disturbance tops out ~1.4 N m (current drag on buoy at max offset 0.47 m: (0.8*0.5 + 10*0.25) N * 0.47 m), ~0 with arm centered. Mz authority ~29 N m (4 horizontal thrusters x 0.144 m arm x 50 N, config.py:96,139). Disturbance <5% of authority. Consistent with prior wiki evidence: yaw_rate constraint slack 8.68/10, in-distribution yaw ss_error <= 0.007, yet yaw = the extreme heavy-tail axis under hard DR.

TRAINING YAW-DISTURBANCE CHANNEL INVENTORY (what the policy DID see):
- PhysX arm reaction torque (transient, large, exact).
- Buoy sweep drag at horizontal offset (real yaw moment about system CoM).
- Ocean-current drag on offset buoy (steady, <= ~1.4 N m; current is linear-only, albc_env.py:896-897, so it cannot torque the main body directly).

ABSENT CHANNELS (verified):
- Hull yaw drag asymmetry / D-matrix off-diagonals (damping_cross_coupling=None; infra EXISTS in hydrodynamics.py:391-394 with a (1,5) sway-yaw example in the docstring -- an unused knob).
- Yaw Munk moment (killed by symmetric added mass; note: for a z-axisymmetric bare hull this is physically correct -- the REAL asymmetry comes from appendages).
- Arm-link (link1/link2) hydro; ~90% of buoy added mass.
- Any external push/torque DR event (events.py has none: hydro/current/joint/payload/mass/friction only).
- Per-thruster asymmetry: thrust_coefficient DR is per-env shared (thruster.py:77), fault injection enable=False default (config.py:331), TAM/max_thrust has no DR at all (see sim_hydro page). A "yaw torque disturbance" axis does not exist in the DR space.

CAVEAT: Stonefish is ALSO an approximation (per-link geometry-based added mass/drag coefficients, not CFD). Its per-link application naturally creates geometric coupling, but its yaw-disturbance MAGNITUDE is not ground truth -- Isaac may under-model and Stonefish may over-model. The arbiter is the real vehicle (tank test), not either simulator.

OPEN PROBES (measurement BEFORE any training-code change):
P1. Cross-sim arm-swing response: same checkpoint, joint1 step/sine in Isaac and Stonefish, log yaw rate + Mz. Directly quantifies the reaction+paddle torque gap. No training-code change.
P2. Eval-side yaw-torque injection sweep (0.5-5 N m constant external torque during eval) -> measure where yaw tracking breaks = the policy's actual rejection ceiling. Small eval-only code addition; plant untouched; no retrain.
Only if P1/P2 show ceiling < Stonefish demand does a training intervention become justified (candidates, one variable at a time: yaw-torque DR channel; enable damping_cross_coupling; revisit buoy added-mass cap). Related blocking lead: TAM/max_thrust DR band (sim_hydro page, needs-apply-before-retrain).

Cross-links: [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]] (analytical nominals, TAM no-DR), [[teacher_dr_harder_yaw_is_the_only_heavy_tail_axis_roll_is_dc_bia]] (yaw = extreme tail), [[buoyancy_gravity_restoring_apply_separately_to_main_body_vs_buoy]] (two-body hydro split), [[yaw_command_is_rate_not_angle_inherited_design_defensible_only_i]] (yaw is rate-tracked).

