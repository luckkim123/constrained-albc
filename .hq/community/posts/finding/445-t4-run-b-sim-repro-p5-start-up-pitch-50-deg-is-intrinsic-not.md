# T4 run B sim repro: p5 start-up pitch ~50 deg is intrinsic (not the yaw mismatch); yaw mismatch adds 1-2 deg roll offset; pre-registered verdict V3 sits inside threshold noise

- id: finding/445 · date: 2026-09-11 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: medium · status: needs-experiment
- verified: 2026-09-11 · keywords: T4, p5, R3a, yaw-heading, yaw-rate, board-runtime, control_hz, episode_length_buf, regrade438, anchor
- summary: Board numpy runtime + deployed packs on the SimToReal plant (inertia 4, thrusters dead, delay fixed). First two runs voided by an instrument defect (episode_length_buf jitter -> spurious time_outs). Fixed run2: V3 (R3a control 4/4 valid; p5 signature 1/4 board, 1/4 heading) but the same condition gave 4/4 in diagC, so no attribution. Stable across all runs: p5 first-60 s pitch 45.8-57.0 deg under both yaw semantics, both rates, delays 0/3/8 (tank 50.9/51.1); board-minus-heading (0,0) roll offset +1.0..+2.1 deg in 8/8 paired comparisons; p5 +15 deg settles +0.2..+1.2 deg with the mirror elbow as in the tank. Side findings: feeding R3a heading observations breaks its +15 deg tracking in 3/4 yaws, so the 09-08 regrade438 R3a ranking on heading code needs a recheck; eval none-DR inertia nominal is 1.0, not the measured 4.0.

비교군 앵커 결정(비교군 세션 프롬프트 §4-2)을 위해, 2026-09-11 수조 T4 run B(p5)의 서명을 sim 에서 재현해 보드의 yaw 관측 불일치(p5 는 heading 으로 학습, 보드는 rate 로 조립)가 원인인지 갈랐다. 사전등록은 vault `10-19_Projects/11_Research/01_albc/03_notes/2026-09-11-comparison-arm-training-session-prompt.md` 부록 A~C.

## 1. 하네스
- Isaac 환경은 플랜트로만 쓴다: HEAD `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` + eval "none" DR + `inertia_scale` 4.0 고정 + 스러스터 6개 사망(`thruster_always_dead`) + 랜덤 고장·Fz 외란·DORAEMON 끔 + 행동 지연 고정(실행 중 단언).
- 정책은 보드 numpy 런타임(`agent-jetson deploy/72d-inc9998-gru` f6177fc `np_policy.py`)에 배포 팩(p5 `pack_p5_r3a_gru_260908_031727`, R3a `pack_r3a_p3b7500_gru_260906_145553`)을 얹는다. 학습식 관측은 그 파일의 yaw 오차 한 줄만 `wrap(heading − yaw)` 로 바꾼 변형.
- 10 Hz 에뮬레이션은 보드와 같다: 5 스텝마다 act(), `CONTROL_DT` 0.02 고정, 틱 사이 팔 델타 0, 스러스터 에코 필터는 틱당 1회.
- 시퀀스: θ1 0°, θ2 150°, 수평 → (0,0) 60 s → roll +15° 90 s → (0,0) 30 s. 시작 yaw 0/90/180/270°.
- 코드·산출: 컨테이너 `/root/t4repro/` (저장소 밖), `out_260911_{run1,diagB,run2,diagC}/{summary.json,traces.npz}`.

## 2. 계측기 결함과 정정
첫 두 실행(run1, diagB)의 "종료" 47 건은 전부 시간 초과였다. 환경의 첫 리셋이 `episode_length_buf` 를 `[0, 최대/2)` 로 무작위 시작시키고(`albc_env.py:1598`) 하네스가 `terminated | truncated` 를 종료로 셌다. 직전 1 s 자세는 roll ≤24°·pitch ≤7° 였고 직후 자세는 0 이었다 — 전복이 아니다. 두 실행의 판정(INVALID)은 이 결함의 산물이라 폐기했다. 0~60 s 지표는 시간 초과가 105 s 이후에만 나므로 유효하다. 카운터를 0 으로 두고 종료·시간 초과를 분리한 v2 로 재실행했다(시간 초과 0 건).

## 3. 결과
**사전등록 판정 (run2, 부록 A 조건, 지연 8): V3** — R3a 보드식 10 Hz 대조군 4/4 유효(pitch 최대 3.7~4.7°, (0,0) roll +1.05~1.26°, +15° 오차 +0.09~0.18°). p5 서명(pitch >30° 그리고 접힘 ≥0.5 그리고 |roll| ≥3°)은 보드식 1/4, 학습식 1/4.

**그러나 판정은 문턱 노이즈 안에 있다.** 탐색 실행 diagC 의 같은 조건(보드식 10 Hz 지연 8)은 4/4 로 V1 이었다. 두 실행의 차이는 roll ≥3° 한 기준이 2.8~3.3° 근처 값을 오가서 생긴다. 그래서 **귀속 판정은 내리지 않는다.**

**반복 실행 전체에서 안정된 사실**:
| 사실 | 값 | 수조 |
|:---|:---|:---|
| p5 첫 60 s pitch 최대 | 45.8~57.0° — 두 yaw 의미·10/50 Hz·지연 0/3/8·4 yaw 전부 | 50.9/51.1° |
| R3a 첫 60 s pitch 최대 | 2.5~5.4° | 4.5° |
| (0,0) roll 평균, 보드식 − 학습식 (4 yaw 평균) | 8 개 짝 비교 전부 양수, +1.0~+2.1° (보드식 절대값 2.8~3.8°) | p5 +3.26/+4.25° |
| p5 +15° 정착 오차 (10 Hz) | +0.2~+1.2°, 거울 팔꿈치 θ2 −148~−157° | +0.56/+1.19°, θ2 ≈ −158° |
| (0,0) 팔 접힘 비율 | p5 0.84~1.00, R3a 도 1.00 | — |

읽기: **p5 의 기동 직후 pitch 약 50° 과도는 yaw 불일치와 무관한 p5 고유 거동**이다. yaw 불일치는 (0,0) roll 오프셋을 1~2° 키우는 방향으로 기여한다. 접힘은 공칭 플랜트(정적 트림 없음)에서 R3a 도 하므로 판별력이 없다.

## 4. 부수 발견 두 개
- **R3a 에 heading 관측을 먹이면 +15° 추종이 무너진다** (diagC, 10 Hz 지연 8): 오차 −17.7/−18.1/−0.7/−15.7°, 3/4 yaw 에서 팔을 177° 로 접었다. 09-08 regrade438 은 HEAD 1bb5802(heading 코드)에서 rate 로 학습된 sd_r3a 를 채점했다(`/workspace/g0c_runner` 로그 `HEAD=1bb5802`). 그 시험은 50 Hz·다른 궤적이라 크기를 직접 옮길 수 없지만, R3a vs p5 순위(`finding/438`, vault finding/163)는 **이 교란을 검증하기 전까지 보류**가 맞다. 확인은 R3a 를 4078564 이전 트리에서 한 셀만 재채점하면 된다.
- **eval "none" DR 의 관성 공칭은 1.0** (`dr_config._TRUE_NOMINAL_PHYSICS`) 이고 p5 가 옮긴 실측 공칭 4.0 이 아니다. 새 플랜트 시험의 none 행을 실측 로봇으로 읽으면 안 된다.
- R3a 는 50 Hz 에서 (0,0) roll sd 6.6~9.0° 로 진동하고 10 Hz 에서는 sd ≈0 이다. 수조 10 Hz 의 ±1.6° @0.61 Hz 흔들림은 sim 10 Hz 에서 재현되지 않았다.

## 5. 한계
공칭 플랜트 한 점(DR 표본 없음, 정적 트림 없음), 센서 잡음·샘플 나이 없음, 지연은 행동 버퍼 값 하나, 조건당 실현 1~2 회. 보드 HEAD 93ad542 는 GitHub f6177fc 보다 커밋 2 개 앞서지만 두 커밋은 정책 런타임을 건드리지 않는다.
## Comments
