---
title: "sim hydro nominal is analytical (not measured); IMU+pressure can anchor rotation/heave but not surge/sway/TAM"
tags: ["measurement", "system-id", "domain-randomization", "sim-to-real", "damping", "free-decay", "TAM", "sensors", "fault-tolerant-control"]
created: 2026-06-14T07:38:12.841674
updated: 2026-06-14T07:38:12.841674
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
