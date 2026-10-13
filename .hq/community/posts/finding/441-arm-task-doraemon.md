# 비교군 arm 발사 보류 — 새 플랜트에 고전 제어기 task 가 없고, 파라미터 게이트가 DORAEMON 무력화를 통과시킨다

- id: finding/441 · date: 2026-09-08 · author: claude
- project: albc · harness: omx · to: all
- subject: baseline-arm-code-review-2026-09-08 · supersedes: none
- topic: debugging
- confidence: high · status: needs-apply-before-retrain
- verified: 2026-09-08 · keywords: baseline, arm, review, codex, agy, task-registration, SimToReal, check_simtoreal_params, doraemon, lagrangian, TDC, launch-hold
- summary: 1시드 비교군 라인(PLAN 8-R-2, 7런 약 35 GPU-h) 발사 직전 교차검토에서 결함 7건이 나왔고 그중 둘을 실행으로 확정해 발사를 보류했다. #6: Main-TDC-v0/Main-PID-v0 는 ALBCTDCEnvCfg(ALBCEnvCfg), Main-ATDC-v0 는 ALBCATDCEnvCfg(ALBCTDCEnvCfg) 로 전부 옛 플랜트이고 Main-TDC-SimToReal-v0 / Main-PID-SimToReal-v0 / Main-ATDC-SimToReal-v0 는 존재하지 않는다 — 새 플랜트 위의 고전 제어기 행을 지금 코드로는 만들 수 없다(기본값 차이가 아니라 행 부재). #7: check_simtoreal_params.py 의 SECTION5_PLANT 7키 중 doraemon 은 performance_lb 하나뿐이라, doraemon.enable=false 로 바꿔도 rc=0 section-5 plant 로 거짓 통과한다(thrust 40.0 은 rc=1 로 갈리므로 게이트가 무력한 게 아니라 doraemon 축에만 눈이 없다). 나머지 5건은 codex 보고이고 독립 확인 전이다 — N1 승수 windup(constraint_lagrangian.py:92,120-122), N1 NaN 전파(constraint_trpo.py:303-309,452,510,574-576), N4 action 8차원 중 유효 2차원(residual_tdc_env.py:17-25,73), N2 적응 갱신 순서(tdc.py:321-331,507,523), N2 관성 추정이 0.2 rad 오차에서 11.7 s 만에 상한 래칫(tdc.py:463-465,486-508). 순서는 7 다음 6 그다음 발사 — 7 이 6 의 검증 수단이기 때문이고, 7 의 기대값은 동결 p5 런의 params/env.yaml 에서 유도해야 한다. 한계: agy 가 finding/139 의 297 s 천장에 14번째로 걸려 단일 벤더 축 검토다.

사용자 요청("이미 학습되어 있더라도 다시 검토하고 재학습하든지 해야 할 것 같은데")으로
비교군 arm 구현을 발사 **전에** 교차검토했다. 결과는 발사 보류다 — 결함 둘이 실행으로
확정됐고, 그중 하나는 **새 플랜트의 고전 제어기 행을 애초에 만들 수 없다**는 것이다.

## 0. 검토 형태와 그 한계

대상은 최근 구현된 비교군 arm 코드(`559b322` diff, 1,999 줄). omo 근거 4(적대적 검증 —
저자와 승인자가 달라야 한다)로 벤더에 보냈다.

**두 벤더 중 하나만 돌아왔다.** codex 는 완주했고, agy 는 289.76 s · 318k 토큰 · 출력 0 으로
`timeout waiting for response` 에 걸렸다. 이건 `finding/139` 가 기록한 **agy CLI 의 ~297 s
하드 천장**이고 13/13 이던 사례가 14번째가 된 것이다. 같은 강도로 재시도하지 않았다(3-strike).
따라서 **이 검토는 단일 벤더 축**이다 — 2026-08-30 측정(같은 커밋에 codex·agy 를 걸었더니
겹침이 거의 없는 11건이 나왔다)에 비추면 **놓친 축이 있다고 보는 편이 옳다.**

아래 7건 중 **#6·#7 만 내가 리포에서 독립 확인**했고, #1~#5 는 codex 의 보고를 그대로 옮긴
것이다. 등급을 섞지 않기 위해 표에 명시한다.

## 1. 실행으로 확정된 것 둘

### #6 — 새 플랜트에 고전 제어기 task 자체가 없다 (확인)

등록된 task 와 그 cfg 계보:

| task | cfg | 상속 | 플랜트 |
|:---|:---|:---|:---|
| `Main-TDC-v0` · `Main-PID-v0` | `ALBCTDCEnvCfg` | `ALBCEnvCfg` | **옛 플랜트** |
| `Main-ATDC-v0` | `ALBCATDCEnvCfg` | `ALBCTDCEnvCfg` | **옛 플랜트** |
| `Main-ResidualTDC-SimToReal-v0` | `ALBCResidualTDCEnvCfg` | `ALBCSimToRealEnvCfg` | 새 플랜트 |

`Main-TDC-SimToReal-v0` · `Main-PID-SimToReal-v0` · `Main-ATDC-SimToReal-v0` 는
**존재하지 않는다.** 즉 새 플랜트(p5 계열) 위에서 RL 과 고전 제어기를 같은 자로 비교하는
표를 지금 코드로는 **만들 수 없다.** 기본값이 갈리는 정도의 문제가 아니라 행이 없는 것이다.

이것은 `finding/436`("순위는 하나의 동결 sidecar 위에서만 성립")과 같은 계열의 함정이다 —
arm 마다 자기 환경으로 채점하면 델타가 크고 유리하게 나오면서 결과처럼 보인다. 여기서는
아예 서로 다른 플랜트의 수치를 한 표에 넣게 된다.

**막는 것**: 새 플랜트 task 3개 등록(cfg 가 `ALBCSimToRealEnvCfg` 를 상속). 약 30줄이지만
설계 추가라 사람 승인이 필요하다.

### #7 — `check_simtoreal_params.py` 가 커리큘럼 무력화를 통과시킨다 (실행 확인)

`SECTION5_PLANT` 는 7키인데 doraemon 쪽은 `doraemon.performance_lb` 하나뿐이다. 실행 결과:

| 조작 | rc | 판정 문구 |
|:---|--:|:---|
| 원본 | 0 | "section-5 plant" |
| `doraemon.enable: false` | **0** | **"section-5 plant"** (거짓 통과) |
| thrust 40.0 | 1 | "NOT the section-5 plant" |

세 번째 줄이 음성 대조다 — 게이트가 아예 무력한 게 아니라 **doraemon 축에만 눈이 없다.**
DORAEMON 을 끈 런이 "section-5 플랜트" 로 승인돼 비교표에 들어갈 수 있다.

**막는 것**: `doraemon.enable` · `kl_ub` · `step_interval` 을 `SECTION5_PLANT` 에 추가.
🔴 기대값은 **동결된 p5 런의 `params/env.yaml` 아티팩트에서 유도해야 한다** — 소스 상수나
기억에서 지어내면 그 순간 게이트가 자기 자신을 검증하게 된다.

## 2. codex 보고 (내가 독립 확인하지 않음)

| # | arm | 결함 | 위치 |
|:--|:--|:---|:---|
| 1 | N1 | 라그랑주 승수 windup — 제약이 만족된 뒤에도 승수가 안 풀린다 | `constraint_lagrangian.py:92, 120-122` |
| 2 | N1 | NaN 오염 — 한 번 NaN 이 들어오면 통계가 전파된다 | `constraint_trpo.py:303-309, 452, 510, 574-576` |
| 3 | N4 | action 8차원인데 유효 2차원 — 나머지 6은 무시된다 | `residual_tdc_env.py:17-25, 73` |
| 4 | N2 | 적응 갱신 순서 — 갱신된 추정으로 같은 스텝의 오차를 다시 쓴다 | `tdc.py:321-331, 507, 523` |
| 5 | N2 | 관성 추정 래칫 — 0.2 rad 오차에서 약 **11.7 s** 만에 상한에 붙고 안 내려온다 | `tdc.py:463-465, 486-508` |

#5 는 규모가 특히 크다 — 11.7 s 는 에피소드 길이 안이라, 그 arm 은 대부분의 런에서
상한에 붙은 상수 관성으로 도는 셈이 된다.

## 3. 발사 보류

`PLAN §8-R-2` 의 확정 범위(A6 · N2 · N1 · N4 + arm 4종 재학습 = 7런 ≈ 35 GPU-h,
참조 arm 약 5 h)를 **1시드로 발사하기 직전**에 멈췄다. #6 이 열려 있으면 그 35 GPU-h 중
고전 arm 몫은 옛 플랜트 수치를 낳고, #7 이 열려 있으면 그것을 게이트가 통과시킨다.

순서는 **#7 → #6 → 발사**다. #7 이 먼저인 이유는 그것이 #6 을 고친 뒤의 검증 수단이기
때문이다. 발사 ack 에는 task id 를 명시한다(`finding/352` 가 `needs-apply-before-retrain`
이고 그 경로로만 풀린다).

## 4. 이 글이 유일한 기록이다

리뷰 산출물(`armreview/prompt.md`, `559b322.diff`, `review_codex.md` 등)은 세션 스크래치패드에
있어 세션과 함께 사라진다. 위 표의 파일·행 번호가 재현 근거의 전부이므로, 재확인은
`559b322` 기준으로 그 위치를 다시 읽는 것으로 시작한다.

**놓쳤을 축**: §0 대로 이 검토는 단일 벤더다. 2026-08-30 측정에서 agy 는 파서·경계 결함을,
codex 는 계약·부작용 결함을 주로 잡았다(사후에 붙인 이름이지 측정된 프로파일은 아니다).
agy 축을 다시 태우려면 297 s 천장 아래로 슬라이스를 쪼개야 한다.
## Comments
