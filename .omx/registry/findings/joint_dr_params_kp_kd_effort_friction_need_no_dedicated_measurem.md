---
title: "Joint DR params (Kp/Kd/effort/friction) need NO dedicated measurement: PD-gain center already measured, effort/friction are DR-bypass by design"
tags: ["albc", "envs-main", "arm", "actuator", "joint-dr", "sim-to-real", "measurement", "friction", "pd-gain", "retrain-campaign"]
created: 2026-07-06T08:41:36.341187
updated: 2026-07-23T07:42:44.326032
sources: []
links: ["onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7.md", "actuator_hardware_identification_arm_xw540_t260_board_measured_p.md", "arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md"]
category: reference
confidence: high
schemaVersion: 1
qualityScore: 40
qualityReasons: ["body-under-120-chars", "no-source-marker", "generic-only-tags"]
status: resolved
---

# Joint DR params (Kp/Kd/effort/friction) need NO dedicated measurement: PD-gain center already measured, effort/friction are DR-bypass by design

Scope: envs/main arm actuator DR (the 5 uniform-only joint params). Records the DECISION that these do NOT need dedicated measurement (mostly), and WHY -- so a future audit does not spend effort re-measuring what DR is designed to bypass. Companion to the measured-arm card [[onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7]], the HW-id card [[actuator_hardware_identification_arm_xw540_t260_board_measured_p]], and the velocity-cap ripple card [[arm_velocity_limit_sim_6_28_3_1_ripple_dead_constraint_trap_delt]].

## THE 5 JOINT DR PARAMS (all uniform-only, DORAEMON never touches them)
| param | SOFT | HARD | sim base | kind |
|:---|:---|:---|:---|:---|
| joint_stiffness_range (Kp) | (40,120) | (30,150) | 100 | absolute gain |
| joint_damping_range (Kd) | (0.5,5.0) | (0.3,7.0) | 3 | absolute gain |
| joint_effort_limit_range | (0.7,1.0) | inherits | 13 Nm | multiplier on torque cap |
| joint_static_friction_range | (0.0,0.03) | inherits | -- | absolute (Coulomb) |
| joint_viscous_friction_range | (0.0,0.2) | inherits | -- | absolute (viscous) |
NOTE yaw_damping_scale has "damping" in the name but is HYDRODYNAMIC (DOF-5 quad damping), not a joint param -- excluded here.

## WHY A DR PARAM NEEDS MEASUREMENT AT ALL (only two reasons)
1. anchor the CENTER -- DR multiplies/offsets a base, so if base is off, the whole range covers the wrong place.
2. confirm the WIDTH covers real uncertainty -- too narrow = sim-to-real gap, too wide = physically-uncontrollable outliers.
A param needs neither reason -> no dedicated measurement; DR's whole point is to bypass unmeasurable/varying params.

## DECISION PER PARAM
### PD gain (stiffness + damping) -- CENTER ALREADY MEASURED, do not re-measure the range
Onboard 2026-07-06 step-response overshoot 2-3% -> zeta~0.74-0.78, matching sim base design (Kp=100/Kd=3, comment w_n=57.7, zeta~0.7). So the small-signal CENTER is measurement-anchored; the DR range stays as-is (its width is a safety margin, not a measured spread). DO NOT re-tune Kp/Kd blindly ([[onboard_measured_2026_07_06_arm_step_response_valid_sim_zeta_0_7]] finding 1).
BUT: the remaining gap is NOT a range problem -- it is a CONTROLLER-STRUCTURE gap that no multiplicative DR can cover: real = discrete PID @1kHz WITH an I-term (I=1, nonzero) + PWM saturation + trapezoidal profile-velocity; sim = continuous PhysX PD, no I-term, no profile. Register gains P800/I1/D40 are firmware PWM units, NOT SI, so they can't be dropped into sim Kp/Kd ([[actuator_hardware_identification_arm_xw540_t260_board_measured_p]]). This gap is closed by step-response TRAJECTORY sysID (a separate track, protocol already in the HW-id card), not by widening/narrowing the DR range.

### effort_limit -- measurement HARD, DR approximation is fine
Torque cap is measurable in principle, but underwater you can't cleanly separate joint torque from fluid reaction/buoyancy (same "forces not separable when things act together" limit as [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]]). effort_limit is a DR-style training perturbation (approximate is a net win, irrelevant at deploy where the real joint just has its real limit), so the current (0.7,1.0) range is fine WITHOUT measurement.

### friction (static + viscous) -- measurement NEAR-IMPOSSIBLE, and that is EXACTLY why DR exists
Breakaway (static) and viscous friction cannot be cleanly separated from inertia/PD/fluid dynamics without precise dynamometer rigs -- effectively impossible on a submerged UUV arm. This "unmeasurable uncertainty" is the reason to randomize. The lower bound of 0 ((0.0,0.03), (0.0,0.2)) encodes the philosophy: don't know the real friction, so cover frictionless->upper so any value is robust. Attempting to measure these is low ROI; DR is the bypass for exactly this.

## BOTTOM LINE
Contrast with velocity_limit_sim (where measurement REFUTED a base constant, 6.28 vs measured 3.1 -> a real fix). For the 5 joint DR params NOTHING is refuted and NOTHING new needs measuring: PD-gain center is already measured (range stays), effort/friction are DR-bypass params (measure-hard-or-impossible, approximate DR is correct by design). The ONLY open joint item is the PD controller-STRUCTURE gap (I-term / PWM / profile), addressed by step-response sysID as a separate track -- not by touching any DR range. So: joint DR ranges ship as-is for the next retrain; no joint-DR measurement campaign is warranted.

---

## Update (2026-07-23T07:42:44.326032)

2026-07-23 curation: status set to resolved -- firm 'no measurement campaign warranted' conclusion reached.
