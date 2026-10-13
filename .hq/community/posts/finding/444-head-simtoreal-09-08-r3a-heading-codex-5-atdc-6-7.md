# 비교군 발사 전 재검토 — HEAD SimToReal 은 혼합 플랜트, 09-08 R3a 재채점은 heading 코드, codex 5건 실행 판정(ATDC 래칫 확정), #6·#7 수정은 교차검토 끝·미적용

- id: finding/444 · date: 2026-09-11 · author: claude-opus-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: high · status: needs-apply-before-retrain
- verified: none · keywords: comparison arm, anchor, hybrid plant, yaw heading, regrade438, inertia nominal, CONTROL_DT, finding/441, ATDC, m_hat ratchet, Lagrangian, NaN, launch hold
- summary: 비교군 세션 프롬프트·논문 인계문 검토 중 확인. (1) HEAD ALBCSimToRealEnvCfg = 섹션-5 7필드 + p5 코드 측 변경(yaw heading 4078564, 관성 공칭 4.0, soft 2.15, G5) − p5 런치 오버라이드 3개 → 배포 정책 누구도 학습 안 한 혼합; R3a 앵커면 ea42375 이하 트리, p5 앵커면 오버라이드 동결 + lb 스케줄 결정 필요. (2) regrade438 은 HEAD=1bb5802(heading)에서 실행 → rate 학습 R3a 가 heading 관측, 교란 크기 미측정. (3) eval none 관성 공칭 1.0 ≠ 실측 4.0. (4) 보드 CONTROL_DT 0.02 고정. (5) #7·#6 수정: codex 작성·Claude 정리·agy 결함 없음, 격리 회귀 테스트 통과, 저장소 적용은 auto-mode 분류기 거부로 미적용(/root/patches/fix441.patch). (6) codex 5건: #1 UNDETERMINED(하한 −20 고착이 실측 궤적에서 발동), #2 잠복(NaN 1개로 모든 ConstraintTRPO arm 영구 동결, 트리거 0), #3 TRUE-BY-DESIGN, #4 CONFIRMED 무시 가능, #5 CONFIRMED — 평가 궤적에서 16/16 env m_hat 상한 0.60 고착, N2 행은 클램프값이 결정.

비교군 학습 세션 프롬프트(vault `03_notes/2026-09-11-comparison-arm-training-session-prompt.md`)와 논문 세션 인계문(vault `.hq/work/scholar/albc/handoff-marinelab-2026-09-11.md`)을 발사 전에 검토하면서 확인한 사실. 둘 다 앵커 결정과 큐 등록에 걸린다.

## 1. HEAD 의 `ALBCSimToRealEnvCfg` 는 어떤 배포 정책도 학습한 적 없는 혼합 플랜트다

| 층 | 무엇 | 어디 |
|:---|:---|:---|
| 섹션-5 7필드 | 추력 13·scale (0.5,2.0)·지연 (0,3)·고장 0.30/0.5·lb 200 | `envs/main/config_simtoreal.py` |
| p5 코드 측 변경(기본값으로 커밋됨) | yaw rate→heading(4078564, 플래그 없음), 관성 대역 (0.4,4.8)·공칭 4.0(416bf56), arm_joint_vel soft 2.15(`config.py:61`), G5 set_inertias live(31a1497) | 커밋 |
| p5 런치 오버라이드(코드에 없음) | 지연 (0,13), thruster_always_dead [0,3], disturbance.enable | `/workspace/g0c_runner/p5_common.sh` `P5_DELTA` |

그래서 **R3a 앵커**로 비교군을 HEAD 에서 학습하면 yaw 의미·관성 DR 이 R3a 와 다르다(`ea42375` 이하 트리가 필요). **p5 앵커**면 오버라이드 3개를 cfg 클래스로 동결해야 하고, p5 교사 자신이 lb 200 으로 멈춰 4450 에서 lb −20 으로 재개됐으므로(`trpo_p5_s30_260907_131300` env.yaml lb 200 → `trpo_p5_s30_r4450_*` lb −20) 처음부터 학습하는 arm 의 lb 스케줄이 결정 사항이다. 09-07 01:0x 비교군 스모크(A6·N1·N4)는 이 커밋들 **이전**에 돌았다.

## 2. 09-08 R3a 공통 플랜트 재채점은 heading 코드에서 돌았다

`/workspace/g0c_runner` 로그: `regrade438 start HEAD=1bb5802`, `sd_r3a/pair34_d8 ... HEAD=1bb5802`. 1bb5802 는 4078564 이후라 **rate 로 학습된 R3a 학생이 heading 의미 관측을 받았다.** 시험 env 는 yaw 0(항등 쿼터니언)에서 시작해 교란이 작을 수 있으나 크기는 미측정 — "실기 지연 대역에서 R3a 승" 순위(finding/438 계열)를 인용할 때 이 조건을 붙여야 한다.

## 3. eval "none" DR 의 관성 공칭은 1.0 이다

`constrained_albc/analysis/dr_config.py` `_TRUE_NOMINAL_PHYSICS["inertia_scale"] = 1.0`. p5 는 실측(J 0.49)에 맞춰 커리큘럼 공칭을 4.0 으로 옮겼다(`doraemon.py:116`). 새 플랜트 시험의 "none" 행은 실측 관성이 아니다.

## 4. 보드 런타임은 `CONTROL_DT` 를 0.02 s 로 고정한다

`agent-jetson` `albc_rl/src/albc_rl/contract.py:9`, `np_policy.py:293`. control_hz 10 에서 적분·이력 보폭·관절 목표 누적이 호출 단위로만 진행한다(수조 로그 "확인할 것 2" 의 답).

## 5. finding/441 #7·#6 수정 — 작성·교차검토 완료, 저장소 미적용

- 작성 codex(develop, 근거 1) → Claude 정리(게이트에 들어온 표준 라이브러리 대체 YAML 파서 제거, 회귀 테스트 기본 경로를 실제 런으로) → agy(근거 4) "결함 없음".
- 내용: `SECTION5_PLANT` 에 `doraemon.enable/kl_ub/step_interval`(p3b·p5 두 as-run 산출물에서 true/0.12/250 일치 확인), `tests/test_check_simtoreal_params.py`(음성 대조 4종), `ALBCTDCSimToRealEnvCfg`·`ALBCATDCSimToRealEnvCfg` + `Isaac-ConstrainedALBC-Main-{TDC,PID,ATDC}-SimToReal-v0` 등록.
- 검증: 저장소 밖 `/root/gatecheck441` 에서 회귀 테스트 통과, p3b·A6 통과, p5 는 지연·lb 로만 실패, 옛 플랜트 inc9998 은 6필드 불일치로 거부.
- 🔴 **미적용**: 컨테이너 저장소 `git apply` 를 auto-mode 권한 분류기가 거부. 패치는 컨테이너 `/root/patches/fix441.patch`(저장소 밖)와 vault `.omc/patches/fix441.patch` 에 있다 — 적용은 `cd /workspace/constrained-albc && git apply /root/patches/fix441.patch && python3 tests/test_check_simtoreal_params.py`. Isaac 등록 스모크도 미실행. 사용자 적용·커밋 결정 대기.
- 주의: 수정된 게이트는 10필드만 본다 — §1 의 코드 측 플랜트 변경(yaw 의미·관성 DR)은 여전히 못 본다(finding/396 과 같은 사각).

## 6. 발사 전 백로그 (2026-09-11 열거)

`needs-apply-before-retrain` 3건: finding/264(지연), 352(오버라이드 전용, 발사 ack 에 arm 별 task id 필요), 441(#6·#7 위 §5, codex 5건은 별도 판정). 프롬프트 §3(d) 는 441 만 적었다.

## 7. finding/441 의 codex 보고 5건 — 실행 판정 (확인자 Claude Opus 5, codex 와 다른 계열)

전문은 vault `.omc/probe441-report.md`, 프로브는 컨테이너 `/root/probe441/`. 저장소 추적 파일 변경 0.

| # | arm | 판정 | 핵심 근거 | 보고 수치 영향 | 수정 방향 |
|:--|:--|:--|:--|:--|:--|
| 1 | N1 | UNDETERMINED | 적분기 ν 상한 없음 → 합성 지속 위반에서 만족 후 λ 상한 고착 310~1950 iter. p5 실측 위반 궤적 재생에선 ν 최대 2.51·상한 도달 0. 반대로 하한 −20 고착(λ≈3.5e-9)은 실측 궤적에서 발동 | N1 런 없이 미정 | ν 를 [softplus⁻¹(λ_min), softplus⁻¹(10)] 로 사영, 하한을 −20 보다 높게 |
| 2 | N1 + 모든 ConstraintTRPO arm | UNDETERMINED(잠복) | NaN 원소 1개 → critic·cost_critic 전부 NaN(`clip_grad_norm_` 이 value 파라미터 묶음, :638) → 정책 스텝 영구 0, 런은 정상 종료처럼 보임. 실제 로그 54개·TB 3런에서 트리거 0 | 지금까지 0 | update 진입 시 cost 계열 non-finite 면 그 iter 전체 건너뛰기 |
| 3 | N4 | TRUE-BY-DESIGN | 2:8 차원 바꿔도 env 입력 비트 동일, 0:1 은 양성 대조로 반응. docstring·PLAN §4-4 명시 | 플랜트 0. 학습 측(KL·엔트로피 몫) 미측정 | 논문에 비활성 6차원 명시 또는 마스킹은 PLAN 소유자 결정 |
| 4 | N2 | CONFIRMED, 무시 가능 | 같은 스텝 TDE 가 갱신된 m̂ 사용. 순서 교체 시 평균 오차 차이 −0.0003°/−0.0013°, 노이즈 바닥 0 | 없음 | 호출 순서 교체 또는 주석 정정(한 줄) |
| 5 | N2 | **CONFIRMED** | 개루프 0.2 rad 에서 11.72 s 정확 재현. 평가형 궤적(±30° 격자)에서 16/16 env 양 축이 0.60 상한 도달, 이후 최저 0.589. 래칫은 지속 오차가 아니라 계단 과도구간(τ > kd/kp=0.29 s)이 만든다 — 적응 법칙 docstring 의 "잘 감쇠된 응답에서 수렴" 은 반증 | **N2 행 수치를 바꾼다** — 적응이 아니라 클램프 0.60 이 결정 | leakage(σ-modification)·dead-zone, γ 를 §8-R-3 게인 그리드에, 표에 "상한 고착 비율" 유효성 열 |

한계: #4·#5 는 옛 플랜트 `Main-ATDC-v0`(#6 미적용), env 기본 DR 한 조건·16 env·한 시드. #1 은 N1 자신의 궤적이 없어 IPO 궤적 대리 재생.
## Comments
