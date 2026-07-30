---
title: "thruster_util remains the binding constraint in both runs and its binding intens"
tags: ["auto-captured", "trpo_b0cmaxthrust_s30_260724_024326", "trpo_ftc1sevinit_s30_260729_105510"]
created: 2026-07-27T06:42:48.885806
updated: 2026-07-30T03:54:24.726456
sources: ["experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md", "experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md", "/workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md"]
links: []
category: session-log
confidence: low
schemaVersion: 1
qualityScore: 90
qualityReasons: ["generic-only-tags"]
---

# thruster_util remains the binding constraint in both runs and its binding intens

thruster_util remains the binding constraint in both runs and its binding intensity RISES with the band, JC/dk 0.805 -> 0.853 (+6%), while staying satisfied (viol -5.89) — the direction H1 predicted (weaker-ceiling envs must command a higher fraction of full throttle), at a magnitude far below violation. | constraint | anchor JC/dk | B0c JC/dk | B0c margin | B0c viol | |---|---|---|---|---| | Constraint/margin/thruster_util / Constraint/viol/thruster_util | 0.805 | 0.853 | 5.89 | -5.89 | | Constraint/margin/rp_vel_settling / Constraint/viol/rp_vel_settling | 0.550 | 0.542 | 9.15 | -9.15 | | Constraint/margin/rp_rate / Constraint/viol/rp_rate | 0.395 | 0.391 | 6.09 | -6.09 | | Constraint/margin/arm_torque / Constraint/viol/arm_torque | 0.237 | 0.216 | 6.27 | -6.27 | | Constraint/margin/manipulability / Constraint/viol/manipulability | 0.118 | 0.113 | 4.43 | -4.43 | | Constraint/margin/arm_joint_vel / Constraint/viol/arm_joint_vel | 0.042 | 0.041 | 1.92 | -1.92 | | Constraint/margin/yaw_rate / Constraint/viol/yaw_rate | 0.030 | 0.038 | 9.62 | -9.62 | | Constraint/margin/attitude / Constraint/viol/attitude | -0.000 | 0.019 | 0.98 | -0.98 | | Constraint/margin/joint1_pos / Constraint/viol/joint1_pos | -0.000 | 0.001 | 1.00 | -1.00 | | Constraint/margin/cumul_yaw / Constraint/viol/cumul_yaw | -0.000 | -0.000 | 1.00 | -1.00 |

[EVIDENCE: engine TIER 2 Constraints, b0c_engine.txt and anchor_engine.txt (all 10 rows each); barrier_penalty last=-0.1226, 0 spikes > 0.01]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Update (2026-07-27T10:30:03.859588)

thruster_util remains the binding constraint in both runs and its binding intensity RISES with the band, JC/dk 0.805 -> 0.853 (+6%), while staying satisfied (viol -5.89) — the direction H1 predicted (weaker-ceiling envs must command a higher fraction of full throttle), at a magnitude far below violation. | constraint | anchor JC/dk | B0c JC/dk | B0c margin | B0c viol | |---|---|---|---|---| | Constraint/margin/thruster_util / Constraint/viol/thruster_util | 0.805 | 0.853 | 5.89 | -5.89 | | Constraint/margin/rp_vel_settling / Constraint/viol/rp_vel_settling | 0.550 | 0.542 | 9.15 | -9.15 | | Constraint/margin/rp_rate / Constraint/viol/rp_rate | 0.395 | 0.391 | 6.09 | -6.09 | | Constraint/margin/arm_torque / Constraint/viol/arm_torque | 0.237 | 0.216 | 6.27 | -6.27 | | Constraint/margin/manipulability / Constraint/viol/manipulability | 0.118 | 0.113 | 4.43 | -4.43 | | Constraint/margin/arm_joint_vel / Constraint/viol/arm_joint_vel | 0.042 | 0.041 | 1.92 | -1.92 | | Constraint/margin/yaw_rate / Constraint/viol/yaw_rate | 0.030 | 0.038 | 9.62 | -9.62 | | Constraint/margin/attitude / Constraint/viol/attitude | -0.000 | 0.019 | 0.98 | -0.98 | | Constraint/margin/joint1_pos / Constraint/viol/joint1_pos | -0.000 | 0.001 | 1.00 | -1.00 | | Constraint/margin/cumul_yaw / Constraint/viol/cumul_yaw | -0.000 | -0.000 | 1.00 | -1.00 |

[EVIDENCE: engine TIER 2 Constraints, b0c_engine.txt and anchor_engine.txt (all 10 rows each); barrier_penalty last=-0.1226, 0 spikes > 0.01]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_b0cmaxthrust_s30_260724_024326/analysis/diagnose-20260727-151917/report.md

---

## Merged from thruster_util_remains_the_binding_constraint_and_every_constrain.md (2026-07-30T03:54:24.726456)

# `thruster_util` remains the binding constraint and every constraint stayed insid

`thruster_util` remains the binding constraint and every constraint stayed inside budget, so the composition did not push any constraint to violation — the H2 prediction of a newly binding actuation budget does not appear.

[EVIDENCE: engine [TIER 2] Constraints — binding (max J_C/d_k) is `thruster_util` at 0.821 with deepest slack `attitude`; per-constraint J_C/d_k rp_vel_settling 0.542, rp_rate 0.349, manipulability 0.146, arm_torque 0.091, arm_joint_vel 0.066, yaw_rate 0.038, attitude/cumul_yaw/joint1_pos ~ -0.000; all margins positive in the table above]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/teacher_baseline_buoyfix/trpo_eint_s30_rs2350_260727_195102/analysis/diagnose-20260728-004710/report.md


---

## Merged from thruster_util_remains_the_single_binding_constraint_in_all_three.md (2026-07-30T03:54:24.726456)

# `thruster_util` remains the single binding constraint in all three runs — this i

`thruster_util` remains the single binding constraint in all three runs — this is now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) ->]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-132857/report.md

---

## Update (2026-07-27T05:49:10.587769)

`thruster_util` remains the single binding constraint in all three runs — now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine reports `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) -> **0.902** (Arm A) -> 0.798 (Arm B), against a next-highest `rp_vel_settling` at 0.514-0.576]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-134730/report.md

---

## Update (2026-07-27T05:49:10.587769)

`thruster_util` remains the single binding constraint in all three runs — now 8 of 8 runs on this workspace — and fault-DR TIGHTENS it on the fault-agnostic arm specifically.

[EVIDENCE: engine reports `-> binding (max JC/dk): thruster_util` for all three; JC/dk 0.805 (anchor) -> **0.902** (Arm A) -> 0.798 (Arm B), against a next-highest `rp_vel_settling` at 0.514-0.576]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_faultdr_agnostic_s30_260725_183121/analysis/diagnose-20260727-140324/report.md


---

## Merged from thruster_util_remains_the_binding_constraint_in_both_runs_but_e_.md (2026-07-30T03:54:24.726456)

# `thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS 

`thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS budget-stressed than Arm A, so the proposal's stated hazard (severity pushing an already-elevated budget into binding) did not materialize.

[EVIDENCE: `analyze_training.py` [TIER 2] Constraints, J_C/d_k; `-> binding (max JC/dk): thruster_util (0.890)` for E-ftc1 and `(0.902)` for Arm A]
[CONFIDENCE: HIGH]

source report: experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md

---

## Update (2026-07-29T12:20:47.836515)

`thruster_util` remains the binding constraint in both runs, but E-ftc1 is LESS budget-stressed than Arm A, so the proposal's stated hazard (severity pushing an already-elevated budget into binding) did not materialize.

[EVIDENCE: `analyze_training.py` [TIER 2] Constraints, J_C/d_k; `-> binding (max JC/dk): thruster_util (0.890)` for E-ftc1 and `(0.902)` for Arm A]
[CONFIDENCE: HIGH]

source report: /workspace/constrained-albc/experiments/rsl_rl/albc_trpo_teacher/fault_dr/trpo_ftc1sevinit_s30_260729_105510/analysis/diagnose-20260729-171553/report.md
