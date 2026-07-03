---
title: "sim hydro nominal is analytical (not measured); IMU+pressure can anchor rotation/heave but not surge/sway/TAM"
tags: ["measurement", "system-id", "domain-randomization", "sim-to-real", "damping", "free-decay", "TAM", "sensors", "fault-tolerant-control", "thruster", "load-cell", "arm-step-response"]
created: 2026-06-14T07:38:12.841674
updated: 2026-07-02T08:51:07.153669
sources: []
links: []
category: reference
confidence: high
schemaVersion: 1
---

# sim hydro nominal is analytical (not measured); IMU+pressure can anchor rotation/heave but not surge/sway/TAM

The sim hydrodynamic nominal values are ANALYTICAL ESTIMATES, not measurements. Source comments in marinelab/marinelab/assets/albc/albc.py:36-93 say so explicitly: "Cylinder formulas (Fossen, 2021) with URDF dimensions", linear damping = "ITTC-1957 with x2.2 roughness correction", quadratic = "Cd_cross=1.17, Cd_axial=1.0". So the baseline-report heavy-tail story "low-damping envs are hard" rests on a nominal that may itself be mis-anchored -- consistent with the report CAVEAT (report.ko.md:44) where the low-damping causal sign flips between hard and ood (attribution MED, not HIGH).
HARD SENSOR CONSTRAINT (real robot): IMU + pressure ONLY. No DVL.
- IMU: angular rate p,q,r direct; attitude phi,theta direct (yaw drifts); linear accel (integrates to drifting velocity).
- Pressure: depth z direct; heave velocity w = z_dot by differentiation.
=> Rotational DOFs (roll/pitch/yaw) and heave are observable. Horizontal linear velocity (surge/sway u,v) is NOT (no DVL). Lucky alignment: the main task is attitude-only, so surge/sway velocity is not in the policy obs -- the unmeasurable axis is the irrelevant axis, and the measurable axis (rotation) is exactly where the heavy-tail blows up.
MEASURABLE from operating data (add on-robot estimation, then measure -- robot+tank available):
- Rotational damping roll/pitch/yaw (linear_damping[3:6], quadratic_damping[3:6]): IMU gyro direct, no integration drift. Method = free-decay (roll/pitch), spin-down (yaw).
- Metacentric restoring GM (center_of_gravity z = -0.05): IMU attitude; free-decay oscillation FREQUENCY gives GM, amplitude-decay ENVELOPE gives damping (exponential=linear, amplitude-proportional=quadratic).
- Heave damping (index 2): pressure differentiation.
- Net buoyancy/weight: unforced vertical drift z(t), pressure only -- simplest.
Honest boundary: free-decay does NOT fully separate added-mass from GM (both enter oscillation freq as I+I_a and GM). Damping comes out clean regardless; GM absolute needs added-mass theory value or a static tilt test.
NOT measurable from operating data -> widen DR to a physically-defensible bound instead:
- TAM (allocation_matrix, roll moment arm 0.007 m): individual thruster forces can't be separated when 6 fire together -> needs single-thruster bench. CRITICAL: TAM has NO DR AT ALL (absent from envs/main/mdp/events.py, which randomizes added_mass/lin+quad damping/yaw_damping/volume/water_density/cob-cog offset/inertia/body_mass/payload/thruster coeff+time_constant -- but NOT allocation_matrix or max_thrust). A wrong TAM is a systematic bias hitting ALL envs identically with no DR to absorb it. THE IRONY: the most dangerous param to mis-estimate (TAM) is the one operating data cannot measure. Strategy B must prioritize giving TAM/max_thrust a DR band.
- thrust_coefficient absolute scale / max_thrust: needs a load cell; operating data gives only damping-coupled relative value.
- surge/sway damping: no DVL. Has (0.4,1.7) DR; leave (not attitude-relevant) unless full-DOF.
- added mass: collinear with accel, noisy; keep its (0.5,1.5) DR, don't chase measurement.
TWO-STRATEGY PLAN (deferred, recorded at docs/plans/2026-06-14-sim-param-measurement-and-dr-anchoring.md):
A) measurable -> add free-decay logging mode to robot, run tank protocol, offline LSQ/EKF fit, anchor sim nominal (or recenter DR) to measured value.
B) un-measurable-but-important (TAM, max_thrust) -> widen DR to physically-defensible range (per-thruster gain/voltage/mounting variation; size from spec/literature, not a round number), re-train as a comparison experiment (baseline tag + exp branch per rule02), check heavy-tail/OOD don't regress.
FTC connection: this anchoring is a prerequisite for fault-tolerant-control work -- the sim domain must demonstrably COVER the real domain before fault robustness is meaningful, and faults must later be recorded per-env like DR (blocked today by eval-npz-saves-no-raw-obs).

---

## Update (2026-07-02T08:51:07.153669)

ADDENDUM (2026-07-02) — measurement feasibility revisited under a HARDER sensor constraint (no load cell), and a correction to the free-decay optimism above.

An audit enumerated 95 sim parameters and adversarially verified which MUST be physically measured on the real UUV. Result: only 3 genuine measurement targets — (a) TAM roll/pitch moment-arm, (b) thruster command->thrust curve (deadband + nonlinearity), (c) arm joint step-response (Dynamixel XW540-T260 discrete-PID vs sim continuous-PD).

CONSTRAINT UPDATE — the real robot has IMU + pressure ONLY, and NO load cell / force-torque sensor either. This tightens the earlier "IMU+pressure only, no DVL" boundary.

CORRECTION to the 2026-06-14 body above — free-decay is MEASURABLE but NON-SEPARABLE, so DOWNGRADE the earlier "measurable -> anchor rotational damping/GM" claim. A tilt-and-release free-decay with IMU is observable, but the oscillation frequency lumps GM, inertia, and added-mass into a single equation: $\omega_n^2 = \rho g V\,GM / (I + A)$ — GM, $I$, $A$ are NOT separable from one measurement. So free-decay is USELESS for parameter ID (it identifies a lumped quantity, not any single sim nominal). The 2026-06-14 optimism that free-decay could anchor rotational damping / GM is retracted; damping-from-envelope still needs an independent GM/added-mass value to be meaningful.

SENSOR REACHABILITY of the 3 targets under IMU + pressure + Dynamixel-bus-telemetry ONLY:
- TAM moment-arm and thrust curve REQUIRE a load cell / force sensor — they measure FORCE, which IMU (an accelerometer) cannot recover: a single thruster's angular accel folds in unknown inertia $I$ + added-mass $A$ via $M = (I + A)\dot\omega$ (underdetermined). NOT measurable with the current suite.
- arm step-response IS measurable — via Dynamixel bus telemetry (PresentPosition / PresentVelocity / PresentCurrent). Uses NEITHER IMU nor pressure. This is the only one of the 3 doable now.
- net buoyancy IS measurable — thrusters off, log depth $z(t)$ with the pressure sensor; the simplest onboard measurement (cheap useful bonus, not one of the 3 gap targets but worth recording).

CORE IRONY / HONEST LIMIT — what is measurable onboard = what does NOT need measuring (arm dynamics + buoyancy, already inside DR); what NEEDS measuring (TAM / thrust) = what onboard sensors CANNOT measure. The single dangerous silent-bias risk (TAM & max_thrust have NO DR band, per the body above) is exactly the axis onboard sensors cannot reach.

PRACTICAL VERDICT (no load cell):
- arm step-response (bus telemetry) = the ONLY real measurement that reduces the gap now -> do it (see the arm step-response protocol / thruster & actuator cards).
- net buoyancy (pressure) = cheap useful bonus -> do it.
- TAM roll/pitch arm + thrust curve = measurement IMPOSSIBLE without a load cell -> handle by ADDING Domain Randomization bands (TAM & max_thrust currently have NO DR band — the silent-bias risk), NOT by chasing a measurement.
- free-decay / IMU-noise -> SKIP (non-separable per the correction above; sim noise std already >= real).

Cross-links: actuator_hardware_identification_arm_xw540_t260_board_measured_p.md (arm XW540-T260 board-measured registers / discrete-PID structural gap), thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban.md (thrust deadband + nonlinear curve, off-by-default).

