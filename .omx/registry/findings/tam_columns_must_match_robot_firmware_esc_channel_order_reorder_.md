---
title: "TAM columns must match robot firmware ESC channel order (reorder + retrain, not a mixer permutation)"
tags: []
created: 2026-07-03T07:26:21.665355
updated: 2026-07-05T15:41:21
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


## MEASUREMENT CHECKPOINT 2026-07-05 (session 3, B1 partial)

이 카드의 핵심 전제("column reorder + retrain으로 충분, columns only never rows")가 **부분 반증됨**. B1 실측 결과 순열(_ESC_CHANNEL_ORDER 튜플)만으로는 부족하고, _BASE_ALLOCATION_MATRIX의 **값(행) 재작성도 필요**하다고 판명. 이유 2가지:

(1) 수직 m0·m3 = 같은 모터 1개(실측). 이 카드가 CONFIRMED라 명시한 "vertical pair m0<-T4, m3<-T5"는 채널 위치(어느 슬롯이 수직인지)는 맞으나, sim이 T4·T5를 **독립 2채널(Fz=1.0 각각 + My=±0.145 pitch 커플링)**로 모델링한 것 자체가 물리적으로 틀렸다. 실제로는 dual-ESC 배선된 단일 모터라 독립 heave 2슬롯이 아니다 (상세: [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]]). Fz/My 행 재작성 대상.

(2) 수평 sign-pattern 불일치: sim 수평 4채널의 Mz 성분이 전부 +0.144(CCW 동부호)인데, 실측 m1=CW(음수). 열 순열은 부호를 보존하는 연산이라(값 자체는 재배열될 뿐 바뀌지 않음), **부호가 틀린 문제는 순열로 고칠 수 없다**. Mz 행(그리고 아직 미측정인 Fx/Fy 병진 성분) 재작성이 필요하다.

**수평 실측 위치·부호표** (wasd 프레임 = launch-agent w=전진 기준, 위에서 내려다봄 CCW=+Mz/CW=-Mz 규약):

| 채널 | 위치 | yaw 부호 |
|:---|:---|:---|
| m1 | 뒤좌 | CW (−), 실측 |
| m2 | 앞좌 | CCW (+), 실측 |
| m4 | 앞우 | CW (−) [유추, 대각선 대칭; HW 고장으로 미측정] |
| m5 | 뒤우 | CCW (+), 실측 |

**아직 열린 것**: surge/sway 병진 부호(B1 병진측정 미완), m4 실측(HW 고장으로 대기), FLU/NED 좌표계 확정(3DM-GX5 datasheet 필요, 상세: [[imu_45deg_offset_pitch_negation_sim_uncompensated_2026_07_05]]).

관련: [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]], [[imu_45deg_offset_pitch_negation_sim_uncompensated_2026_07_05]]


## PERMUTATION + VALUE REWRITE VERDICT 2026-07-06 (B1 회전실측 기하계산 완결)

이 카드 핵심전제 "column reorder+retrain 충분, columns only never rows, 순열은 물리불변"이 **완전 반증됨**. 근거: 수평 B1 회전실측을 xacro 기하와 대조한 계산 (session 3 이후 세션에서 element-wise 대조로 확정).

(a) **순열 자체가 3채널 오배정**. 실측 위치(앞뒤좌우)+회전(CW/CCW)로 xacro T0~T3와 대조하면 올바른 매핑은 m1←T1, m2←T3, m4←T2, m5←T0이다. 기존 `_ESC_CHANNEL_ORDER=(4,0,1,5,2,3)`의 수평부(m1←T0, m2←T1, m4←T2, m5←T3)는 m4를 제외한 3채널이 틀렸다 (m4←T2만 우연히 맞음).

(b) **순열 고쳐도 값 자체가 불일치**. sim `_BASE_ALLOCATION_MATRIX`의 Mz행은 수평 4채널 전부 +0.144(동부호, CCW 가정)인데, 실측은 **2-2분할**(m1·m4=−0.144, m2·m5=+0.144, 대각선쌍마다 반대회전). 열 순열은 부호를 보존하는 연산이라 4채널 동부호 배열은 아무리 재배열해도 2-2분할이 될 수 없다 -- 원리적으로 불가능. 따라서 **`_BASE_ALLOCATION_MATRIX` 값(행) 재작성이 필수**다. 물리적 의미: sim은 "수평 4채널이 전부 같은 방향(yaw)으로 기여"한다고 모델링했으나, 실기는 프롭 CW/CCW 표준 벡터드 배치라 대각선쌍마다 반대 회전 -- sim TAM이 물리적으로 틀린 모델이었다.

확정된 실측 수평 TAM 3행 (재작성에 넣을 값; 병진(Fx/Fy)은 회전실측+위치+a/d 규약(a=왼쪽 실측 → +y=왼쪽, REP-103 정합)으로 유일결정되므로 별도 병진측정 불필요):

| 채널 | Fx(surge) | Fy(sway) | Mz(yaw) |
|:--|:--:|:--:|:--:|
| m1 | +0.707 | +0.707 | −0.144 |
| m2 | −0.707 | +0.707 | +0.144 |
| m4 | −0.707 | −0.707 | −0.144 (m4 회전은 유추 -- HW 고장으로 실측 불가, 대각선 대칭 근거) |
| m5 | +0.707 | −0.707 | +0.144 |

아직 열린 것: 수직 행(Fz/Mx/My) 재설계(좌우 1모터 구조, sim의 앞뒤2채널 가정 자체가 틀림 -- [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]] 참조), m4 실측(HW 고장 대기), FLU/NED 좌표계 확정(3DM-GX5 datasheet 필요).

결론 한줄: **이건 순열(238932c) 문제가 아니라 sim TAM이 물리적으로 틀린 행렬이었다. 수평 3행 값 + 순열 둘 다 실측으로 재작성해야 한다.**

관련: [[tam_vertical_single_motor_dual_esc_measured_2026_07_05]], [[imu_45deg_offset_pitch_negation_sim_uncompensated_2026_07_05]]
