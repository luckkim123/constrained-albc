---
title: "TAM columns must match robot firmware ESC channel order (reorder + retrain, not a mixer permutation)"
tags: []
created: 2026-07-03T07:26:21.665355
updated: 2026-07-03T07:26:21.665355
sources: []
links: ["thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban.md", "actuator_hardware_identification_arm_xw540_t260_board_measured_p.md"]
category: convention
confidence: high
schemaVersion: 1
---

# TAM columns must match robot firmware ESC channel order (reorder + retrain, not a mixer permutation)

Scope: envs/main + envs/full_dof thruster allocation matrix (TAM) column ordering, sim-to-real channel matching. Firmware-confirmed bug fix landed on main 2026-07-03 (commit 238932c), NOT an A/B experiment. Companion to the thruster-curve card [[thruster_nonlinear_curve_t200_sim_to_real_off_by_default_deadban]] and the hardware-identification card [[actuator_hardware_identification_arm_xw540_t260_board_measured_p]].

CONVENTION. The sim TAM COLUMN order MUST match the physical robot firmware's ESC channel order. They diverged: sim had heave on thruster columns T4,T5 (Fz row = (0,0,0,0,1,1)); the robot firmware (agent-jetson pid.cpp) wires m0,m3 = vertical (heave/depth, driven by PID_control_depth) and m1,m2,m4,m5 = horizontal (driven by PID_control_yaw). The canonical fix is to REORDER THE TAM COLUMNS to firmware ESC order in sim (so sim thruster order == firmware channel order and the deploy-side mixer permutation becomes identity) and RETRAIN -- not to keep a permanent permutation adapter in the deploy mixer (that makes "temporary" permanent, a hidden sim-real adapter that rots).

THE FIX (238932c). Permutation _ESC_CHANNEL_ORDER = (4,0,1,5,2,3): new column j = original sim column ORDER[j], i.e. new order = old [T4,T0,T1,T5,T2,T3]. Implemented parameterized in BOTH envs/main/config.py and envs/full_dof/config.py (duplicated per the independent-config convention): the original literal is preserved as module-level _BASE_ALLOCATION_MATRIX (sim T0-T5 order, for physical audit), and allocation_matrix = _reorder_columns(_BASE_ALLOCATION_MATRIX, _ESC_CHANNEL_ORDER) so the permutation is the single source of truth (numbers are NOT hand-typed). The horizontal-4 individual mapping (m1<-T0, m2<-T1, m4<-T2, m5<-T3) is PROVISIONAL, pending B1 watertank measurement -- to update it, edit ONLY the _ESC_CHANNEL_ORDER tuple. The vertical pair (m0<-T4, m3<-T5) and "which channels are vertical" are CONFIRMED.

WHY COLUMN-ONLY + RETRAIN IS SUFFICIENT (verified, do not re-derive). The whole thruster chain shares ONE abstract slot index j: policy action[:, 2+j] -> apply_dynamics commands[:, j] -> ThrusterModel._state[:, j] -> thrust_magnitude[:, j] * _thruster_health[:, j] -> einsum("ij,nj->ni", TAM, thrust) column j. There is NO separate "physical thruster" binding anywhere -- slot j's physical meaning is defined ENTIRELY by TAM column j. So reordering TAM columns redefines slot meaning and command/state/health/observation all follow the same slot j automatically (self-consistent). Retraining teaches the policy the new slot->meaning map. The "state applied to wrong thruster" failure only happens if you reorder the command vector WITHOUT the TAM (or vice versa) -- which nobody does here (only config.py TAM changes).

WHAT DOES NOT NEED TO CHANGE (verified). (a) USD assets: in envs/main the thruster is NOT a USD prim/joint -- it is an analytical TAM model; compute_wrench() produces a 6D body wrench injected as an external force on the body (albc_env.py). USD has only the 2 arm joints. actuators.xacro is reference-only, not used in force computation. So a column reorder needs NO USD edit. (b) marinelab/core/thruster.py: _state/_thruster_health/commands are all shape (N, num_thrusters) and auto-reorder with the TAM slot index -- untouched. (c) rewards.py thruster util (mean) and constraints.py thruster_utilization_cost (max) are order-invariant reductions -- untouched. (d) tdc teacher PD (thruster_pd.py): _tam_pinv = pinv(reordered TAM) auto-produces row-permuted per-thruster forces in the same new slot order (new_pinv = P^T @ old_pinv), normalized by a SCALAR thrust_coefficient, fed to apply_dynamics that re-multiplies by the same reordered TAM (round-trip consistent) -- inherits cfg.thrusters.allocation_matrix, untouched. (e) TAM ROWS (Fx..Mz body-frame axes) must NEVER be reordered -- only columns.

PHYSICS INVARIANCE (arithmetically verified). A column permutation is a right-multiply by a permutation matrix P (new = old @ P). Singular values of old vs new TAM are identical, and eig(TAM @ TAM.T) identical -> rank and achievable-wrench space are UNCHANGED. The reordered result was checked element-wise against ground truth: heave row now nonzero exactly at m0,m3. So there is no "performance regressed, revert" path -- this is a relabeling, not a design knob; it is not an A/B experiment.

CHECKPOINT / RETRAIN CONSEQUENCE. Old checkpoints were trained on the old column order -> DO NOT load them under the new TAM. Retrain from scratch. This fix is for the NEXT baseline retrain (fold in with other confirmed pre-retrain fixes -- see the sim-to-real audit umbrella).

PROCESS NOTE. This did NOT use an exp/ branch: comparison-experiment isolation applies to "adopt/discard-by-result experiments"; a firmware-confirmed bug fix with no discard path (and same class as other confirmed pre-retrain fixes) goes straight to main. Only a baseline tag (baseline-260703-tam-channel-reorder) was kept as a fixed reference point.

VERIFICATION LEDGER. 3 independent adversarial verifiers (ultracode workflow, code-reviewer/opus, distinct lenses) all PASS: arithmetic (derived matrix == ground truth element-wise, both files byte-identical reorder block), order-coupling (no surviving old-order hardcoded index; thruster.py/rewards/constraints/action-slices untouched), completeness (all index-based comments T0-T5 -> ESC m0-m5 in config.py Layout + source docstring + observations.py thruster block, both main and full_dof; parameterization satisfied). Pyright diagnostics on the files are all the known @configclass reportCallIssue / reportMissingImports false positives (rules/04), zero real defects from this change.

