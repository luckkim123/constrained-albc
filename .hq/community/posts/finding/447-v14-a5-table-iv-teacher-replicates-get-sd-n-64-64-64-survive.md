# v14 A5: Table IV teacher replicates get +-SD (n 64, 64/64 survive); the selected teacher DORAEMON saturated all 21 dims at it 7748; all three training segments already carried both plant corrections, so the manuscript from-2350-on sentence is wrong

- id: finding/447 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-09-12 · keywords: v14, A5, F-9, Table IV, teacher selection, replicate, DORAEMON saturation, plant calibration, manuscript correction, iterbudget
- summary: Common-draw Table IV reproduced from summary.json with per-env SD (Hard 0.812+-0.963 / 0.988+-1.208 / 0.856+-1.358, n 64, survival 100). curriculum_trajectory.json: iterbudget 21/21 Beta(1,1) from it 7748, R31 21/21 from 8000, R30 reached at 7750 then receded to 4/21; p3b (anchor B exam box source) never saturated (1/21). Segment 1 trpo_eint_s30_260727_160913 (resume false, 0-2250) env.yaml already has volume 0.0079 and max_thrust_scale (0.85,1.15), as do segments 2-3 and both replicates.

**원고 Table IV(교사 선택·복제)에 붙일 값과, 판독 중 드러난 원고 오기 한 건.** v14 AC 요청 A5(F-9). 새 학습·평가 없음 — 기존 산출 판독만.

## 1. Table IV 보강 — ±(per-env SD), n, Hard 생존

출처는 원고 표를 만든 공통 draw 채점 3건(64 env, seed 42, 고장 주입 없음, DORAEMON 앵커 = 선택 교사 최종 분포):
선택 교사 `teacher_iter_budget/trpo_iterbudget_s30_260805_012813` model_9998 → `eval/static_260814_234643/summary.json`,
Replicate A = `teacher_final_replicate/trpo_replicate_s30_260810_140415` model_9999 → `eval/static_260814_232725`,
Replicate B = `..._s31_260810_140414_dgxcopy` model_9999 → `eval/static_260814_233603`.
A/B 매핑 근거: 원고 "0.044 margin over Replicate B" = R31 − 선택 교사 Hard 델타(diagnose-20260814-235911 report.md §3a).

| DR | 선택 교사 (deg) | Replicate A (s30) | Replicate B (s31) |
|:--|:--|:--|:--|
| None | 0.507 ± 0.153 | 0.652 ± 0.121 | 0.481 ± 0.075 |
| Soft | 0.520 ± 0.210 | 0.606 ± 0.307 | 0.419 ± 0.140 |
| Medium | 0.513 ± 0.229 | 0.594 ± 0.304 | 0.478 ± 0.231 |
| Hard | 0.812 ± 0.963 | 0.988 ± 1.208 | 0.856 ± 1.358 |

값 = `att_norm.ss_error ± ss_error_std`, 모든 셀 n = 64, 생존 64/64(`survival_pct` 100). 소수 셋째 자리까지 원고 표와 같다(재현 확인).
Hard 의 per-env SD(0.96~1.36)는 세 arm 평균 차(≤ 0.18)보다 5~8배 크다 — SE 가 아니라 env 편차라 원고의 floor·2×SE 규칙을 무효화하지는 않지만, 분포가 크게 겹친다는 사실은 표에 보이는 편이 정직하다. 같은 보고서 §3a 의 paired 값: Hard R30 − 선택 교사 +0.176° (SE 0.093, 1.9×), R31 − 선택 교사 +0.044° (SE 0.109, 0.4×).

## 2. 선택 교사 커리큘럼은 Beta(1,1) 에 포화했다 — iteration 7748, 21/21 차원

`curriculum_trajectory.json`(런별 a·b 궤적, 허용오차 1e-6) 판독:

| 런 | 기록 구간 | 종료 시 균일 차원 | 21/21 최초 |
|:--|:--|:--|:--|
| 선택 교사 (iterbudget, 5248..9998) | 250 it 간격 | **21/21** | **7748** |
| Replicate B (s31) | 0..9750 | 21/21 | 8000 |
| Replicate A (s30) | 0..9750 | 4/21 | 7750 (도달 후 17차원 후퇴) |
| 참고: p3b r2050 (R3a 교사 계열, 앵커 B 채점 박스의 출처) | 2050..9999 | 1/21 | 미도달 |

Replicate A 의 후퇴는 같은 보고서 §4 의 설명(DORAEMON 성공률 0.469 < α 0.5, 복구 분기에서 종료)과 맞는다.
⚠️ 마지막 행은 A5 질문 대상이 아니지만 앵커 B 에 걸린다: 앵커 B 채점(`exam_chain_r3a.sh`)은 p3b 최종 DORAEMON 을 공통 시험 박스로 쓰고, 그 분포는 포화하지 않았다(8개 차원은 전 구간에서 한 번도 균일에 닿지 않음). 새 §V 의 "Hard" 는 선택 교사 표의 Hard 와 같은 박스가 아니다.

## 3. "iteration 2350 이후 두 세그먼트만 보정을 담는다"는 원고 문장은 틀렸다 — 세 세그먼트 모두 보정 플랜트

원고 `simulation.tex` Plant calibration 문단: "trained in three resumed segments, and the last two, from iteration 2350 on, carry both adopted corrections". 세 세그먼트의 as-run `params/env.yaml`:

| 세그먼트 | 런 | resume | main_hydro volume | max_thrust_scale |
|:--|:--|:--|:--|:--|
| 1 (0..2250 기록, 크래시 전) | `teacher_baseline_buoyfix/trpo_eint_s30_260727_160913` | false | **0.0079** | **(0.85, 1.15)** |
| 2 (model_2350 재개) | `trpo_eint_s30_rs2350_260727_195102` | model_2350 | 0.0079 | (0.85, 1.15) |
| 3 (model_4999 재개, 선택 교사) | `trpo_iterbudget_s30_260805_012813` | model_4999 | 0.0079 | (0.85, 1.15) |

세그먼트 1 부터 두 보정(부피 0.009→0.0079, ±15 % 추력 포화 대역)이 다 들어 있다. 원고는 "세 세그먼트 모두 보정 플랜트로 학습됐다"로 고쳐야 한다. 2350 에서 바뀐 것은 크래시 재개뿐이다(finding/088). 두 Replicate 도 resume false 단일 세그먼트, 같은 두 필드 — "보정 전 구간을 복제가 재현했는가"라는 질문은 전제가 성립하지 않는다.

## 4. 규칙
비교 열은 전부 공통 draw 값이다. 자기 최종 분포로 다시 채점한 보조 열은 만들지 않았다.

## 검증
- 채점 수치: summary.json 직접 판독(`/root/v14work/a5_table.py`), 세션이 선택 교사 4 tier 를 따로 다시 읽어 일치 확인.
- 포화·플랜트·resume: 세션이 5개 런의 `curriculum_trajectory.json`·`params/env.yaml`·`params/agent.yaml` 을 독립 스크립트로 다시 읽어 위 표 전부 일치.
- 조사: native 서브에이전트(판독 전용), 판정: 오케스트레이터 세션.
## Comments
