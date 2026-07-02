---
title: "Thruster nonlinear curve (T200 sim-to-real): off-by-default deadband + signed-square toggle (d34debc)"
tags: []
created: 2026-07-01T10:05:27.006437
updated: 2026-07-02T06:42:32.542076
sources: []
links: ["actuator_hardware_identification_arm_xw540_t260_board_measured_p.md", "sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an.md"]
category: reference
confidence: high
schemaVersion: 1
---

# Thruster nonlinear curve (T200 sim-to-real): off-by-default deadband + signed-square toggle (d34debc)

Thruster nonlinear curve (BlueROV T200 sim-to-real): off-by-default deadband + signed-square toggle. marinelab exp/thruster-curve commit d34debc, UNPUSHED 2026-07-01.

WHAT: The sim thruster used a purely LINEAR map (thrust = normalized_state * thrust_coefficient(40N)). A 4-way research sweep + adversarial verification identified TWO STRUCTURAL nonlinearities of the real T200 that Domain Randomization (a multiplicative scale on thrust_coefficient) can NEVER reproduce, so they must be modeled as structure, not randomized: (1) a zero-thrust DEADBAND around neutral (DR scaling of a coefficient can't create a zero region), (2) a QUADRATIC propeller law T ~ command^2 (half command = 1/4 force; DR scaling can't bend a line into a parabola).

IMPLEMENTATION (3 files, +80 lines): marinelab/marinelab/assets/uuv_cfg.py adds ThrusterCfg.enable_thrust_curve: bool = False and thrust_deadband: float = 0.075. marinelab/marinelab/core/thruster.py adds ThrusterModel._thrust_command() and reroutes compute_wrench through it. tests/test_thruster.py adds 4 tests (off=linear-identity, signed-square, deadband-zeroes, sign-and-bounds). 8 thruster tests pass; 28 albc-side tests pass, 0 regressions.

OFF-BY-DEFAULT + BYTE-IDENTICAL: enable_thrust_curve defaults False. _thrust_command() early-returns self._state via getattr(self.cfg, "enable_thrust_curve", False) -- so mock configs and every existing run/checkpoint are byte-identical to the prior linear model (same convention as enable_fault). When True, in normalized command space [-1,1]: (a) |state| < thrust_deadband(0.075) -> 0, (b) outside deadband, command = sign(state) * state^2. Output stays in [-1,1] (|state|<=1 => state^2<=1), so the downstream * thrust_coefficient scaling range is unchanged.

WHY THESE TWO ONLY (differential design): deadband = a zero region multiplicative DR can't synthesize. signed-square = the real quadratic propeller law. The tau asymmetry (up 0.1 / down 0.05) and the forward/reverse force asymmetry (~0.78) are NOT modeled here because existing DR (time_constant_scale, thrust_coefficient_scale 0.7-1.3) already covers those magnitude effects. COEFFICIENTS ARE SHAPE-ONLY, not another robot's fit copied verbatim: the signed-square is the generic quadratic shape; magnitude stays with the existing DR range, deliberately NOT hardcoding EasyUUV/MarineGym exact coefficients (safe default until real T200 bench data exists).

VERIFIED NUMBERS (survived adversarial verification): T200 @16V forward 51.5N / reverse 40.2N = 0.78 asymmetry (Blue Robotics product page). Deadband ~+/-25us PWM over +/-400us half-range = normalized ~0.0625; empirical fit 0.075-0.08 (workspace marinegym/actuators/t200.py local reference uses 0.075; EasyUUV arXiv:2510.22126 uses 0.08). KEY: workspace marinegym/actuators/t200.py is ALREADY an in-tree reference implementation (deadband 0.075 + quadratic RPM fit + fwd/rev asymmetry) -- reuse the local verified impl over external sources.

FILTERED (adversarial verification REJECTED these; do NOT cite): 5 fabricated citations recurring across 2 research rounds -- Aras 2013 (custom thruster != T200), arXiv:1807.04109 (T100 != T200), arXiv:2312.09981 (drone motor), ResearchGate 373891538 (does not exist), a misread Dactyl deadband. One arithmetic error: research claimed "mid-range curvature 14%", actual is 57% at s=0.5. The workflow synthesize agent (architect) returned only placeholders ("test"/"0.08") and was discarded -- the spec was synthesized by the controller directly from the research + verification results.

NEXT / CONSEQUENCE: (1) push is user-gated (d34debc UNPUSHED). (2) Enabling the curve is NOT byte-identical -> triggers a from-scratch retrain; fold it into the sim-to-real audit retrain batch (docs/plans/2026-06-29-sim-to-real-audit-before-baseline-retrain.md), do not enable piecemeal. (3) If real T200 bench data arrives, reconsider adopting EasyUUV/marinegym exact coefficients over the generic signed-square shape.

---

## Update (2026-07-02T06:42:32.542076)

ADDENDUM 2026-07-02 (deploy analysis -> KEEP OFF until bench-measured). Decision: leave enable_thrust_curve=False (the default; main has no curve) UNTIL a real command->thrust curve is bench-measured. WHY the curve is different from fault (the key asymmetry): fault/health is a DR-style training PERTURBATION -- an approximate model is still a net win and is irrelevant at deploy (no fault at deploy). The curve is a PLANT MODEL (command->force map): the policy learns a command strategy that PRESUMES this force response, so at deploy the real thruster must reproduce the SAME curve or the policy is optimized for the WRONG plant. Consequence: an INACCURATE curve can be WORSE than the linear default -- the linear default is a KNOWN gap, a wrong curve MANUFACTURES a new gap. Since signed-square+deadband(0.075) has no measured/literature backing (provenance unverified per this card), curve-ON pays off ONLY IF it actually approximates the real T200, which is unverified -> stay OFF. DEPLOY question answered: "just deploy as before (linear passthrough)?" is correct ONLY while curve is OFF; if a curve-trained policy is ever deployed, either the real thruster must naturally realize that curve (path A) or the deploy code must re-apply the same _thrust_command (path B) -- "as before" is NOT automatically safe for a curve-trained policy. RE-ENABLE PATH: bench-measure real command->thrust -> confirm or replace the shape in _thrust_command -> then train curve-ON (only then does the curve REDUCE the gap). Same conclusion as the arm-PD side: sim-to-real gap body = hardware dynamic response, must be measured. cf [[actuator_hardware_identification_arm_xw540_t260_board_measured_p]] [[sim_hydro_nominal_is_analytical_not_measured_imu_pressure_can_an]].
