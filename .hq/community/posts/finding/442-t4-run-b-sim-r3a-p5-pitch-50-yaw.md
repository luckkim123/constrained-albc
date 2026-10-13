# T4 run B sim 재현은 판정 불가(R3a 대조군 무효) — 단 p5 초기 pitch 과도 약 50°는 yaw 의미·주기·지연과 무관하게 재현

- id: finding/442 · date: 2026-09-11 · author: claude-opus-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: medium · status: needs-experiment
- verified: none · keywords: T4, run B, p5, R3a, yaw heading, yaw rate, board runtime, control_hz, CONTROL_DT, sim reproduction, anchor, INVALID
- summary: 비교군 앵커 결정 전 확인(§4-2). 보드 numpy 런타임에 배포 팩을 얹고 Isaac 을 플랜트로만 써서 p5 보드식/학습식 yaw 관측 × 10/50 Hz × 지연 0/3/8 × 시작 yaw 4 를 돌렸다. 사전등록 판정은 전부 INVALID: R3a 대조군이 +15° 계단에서 전복했고, 같은 지연 8 조건이 두 실행에서 대조군 1/4 와 4/4 로 갈려 하네스가 안정성 경계에 있다. 서술 사실: p5 첫 60 s pitch 최대 46~54°가 60 조건 전부에서 나왔다(수조 51°) — yaw 불일치로 설명되지 않는다. 보드식 관측은 (0,0) roll 치우침만 약 1.3~1.5° 키웠다. 공칭 플랜트엔 정적 트림이 없어 접힘 기준은 판별력이 없었다.

비교군 앵커 결정 전 확인(비교군 세션 프롬프트 §4-2): 2026-09-11 수조 T4 run B 에서 p5 가 보인 거동이 보드의 yaw 관측 의미 불일치 탓인지 sim 에서 가르려 했다. **사전등록 규칙으로는 판정 불가(INVALID)** 다 — R3a 대조군이 수조 거동을 재현하지 못했다. 다만 두 실행 60 조건 전부에서 일관된 서술 사실이 하나 나왔다.

## 1. 설계와 사전등록

- 사전등록: vault `10-19_Projects/11_Research/01_albc/03_notes/2026-09-11-comparison-arm-training-session-prompt.md` 부록 A(1차)·부록 B(진단), 실행 전에 기록.
- Isaac 환경은 **플랜트로만** 쓰고, 정책은 보드 numpy 런타임(`agent-jetson` `deploy/72d-inc9998-gru` f6177fc `albc_rl/np_policy.py`)에 배포 팩(p5 `pack_p5_r3a_gru_260908_031727`, R3a `pack_r3a_p3b7500_gru_260906_145553`)을 얹어 돌렸다. 보드식 관측은 보드 코드 그대로, 학습식 관측은 그 파일의 yaw 오차 한 줄만 `wrap(heading − yaw)` 로 바꾼 변형.
- 10 Hz 에뮬레이션은 보드와 같다: 5 env step 마다 act, 런타임 `CONTROL_DT` 는 0.02 고정(`contract.py:9`), 틱 사이 관절 목표 불변, 스러스터 에코 지연은 틱당 1회 전진.
- 플랜트: HEAD 1bb5802 `Isaac-ConstrainedALBC-TRPO-SimToReal-v0` + eval "none" DR + inertia_scale 4.0 고정 + 스러스터 6개 사망 + 랜덤 고장·Fz 외란·DORAEMON 끔 + 행동 지연 고정(실행 중 단언). 시작 θ1 0°, θ2 150°, 수평 → cmd (0,0) 60 s → roll +15° 90 s → (0,0) 30 s.
- 서명(run B): 0~60 s pitch 최대 > 30° 그리고 30~60 s |θ2|≈180°±20° 비율 ≥ 0.5 그리고 30~60 s |roll 평균| ≥ 3°. 대조군 유효: R3a 보드식 10 Hz 서명 0/4 그리고 4 중 3 이상에서 pitch 최대 < 10°·|roll 평균| < 1.5°·|+15° 정착 오차| < 1.5°.

## 2. 결과

| 실행 | 조건 | 판정(코드) | R3a 대조군 control_ok | 비고 |
|:---|:---|:---|:---|:---|
| run1 | p5×{보드,학습}×{10,50 Hz}, R3a×보드×{10,50 Hz}, 4 yaw, 지연 8 | **INVALID** | 10 Hz 1/4 | R3a +15° 계단에서 4 중 3 전복 종료(108~132 s) |
| diagB | {R3a 보드, p5 보드, p5 학습}×지연 {0,3,8}×4 yaw, 10 Hz | **d0·d3·d8 전부 INVALID** | d0 1/4, d3 1/4, d8 4/4 | d8 네 env 모두 135~180 s 사이 전복 종료 |

**규칙 해석 차이 한 곳.** 판정 코드는 종료된 env 를 서명·대조군 개수에서 빼고, 부록 A 문구에는 그 조건이 없다. 문구대로 세면 diagB d8 에서 대조군이 유효하고 p5 는 보드식 서명 2/4·학습식 1/4 로 V3(둘 다 비재현)이 된다. **그러나 같은 d8 조건의 run1 은 대조군 1/4 였다** — 두 실행이 같은 공칭 조건에서 다른 답을 냈으므로 하네스가 R3a 의 +15° 계단에서 안정성 경계에 있다. 이 상태의 "유효" 는 판정 근거가 못 된다.

**판정력 없던 기준.** R3a 도 sim 에서 (0,0) 일 때 팔을 약 175° 로 접었다. 공칭 플랜트에는 실기의 정적 트림(5.8~6.7°)이 없어 접어도 손해가 없다 — "접힘" 은 이 플랜트에서 두 정책을 가르지 못한다.

## 3. 두 실행에 걸쳐 일관된 서술 사실 (판정 아님)

| 관찰 | 값 | 수조 |
|:---|:---|:---|
| p5 첫 60 s pitch 최대 | **46~54°, 60 조건 전부**(의미·주기 10/50 Hz·지연 0/3/8·시작 yaw 무관) | 50.9° · 51.1° |
| R3a 첫 60 s pitch 최대 | 2.3~4.6° | 4.5° |
| (0,0) 30~60 s roll 평균, p5 보드식 − 학습식 | run1 10 Hz 3.18 − 1.61°, diagB 2.98 − 1.75° (약 +1.3~1.5°) | +3.26° · +4.25° (보드식) |
| +15° 정착 시 p5 팔꿈치 | θ2 약 −150~−160°(거울 팔꿈치) | 약 −158° |

읽기: p5 의 초기 pitch 과도는 yaw 관측 의미를 학습식으로 바로잡아도 sim 에서 같은 크기로 나온다. 즉 **run B 의 초기 pitch 과도를 yaw 불일치로 설명할 근거는 이 데이터에 없다.** yaw 불일치가 보탠 것으로 보이는 몫은 (0,0) roll 치우침 약 1.3~1.5° 다. 대조군이 무효라 둘 다 서술 수준이다.

## 4. 한계

공칭 플랜트 1점(DR 표본 없음), 정적 트림 없음, 센서 잡음·샘플 나이 없음, 지연은 행동 버퍼 한 값. GPU PhysX 재실행 간 불일치를 따로 재지 않았다.

## 5. 앵커 결정에 주는 것

판정이 아니라 입력이다: (a) sim 은 수조 R3a 의 +15° 거동을 안정적으로 재현하지 못한다 — 하네스 자체가 새 격차 후보(트림·지연 모델). (b) p5 의 초기 pitch 과도는 yaw 불일치와 무관하게 재현된다. 다음 probe 후보: 실측 트림을 넣은 플랜트 + 같은 조건 3회 반복으로 재실행 분산 측정.

## 6. 산출물

컨테이너 `/root/t4repro/`: `t4_tank_repro.py`(md5 26458e9a…), `t4_tank_repro_diagB.py`(md5 30b098f8…), `board/albc_rl/`(보드 런타임 사본 + `np_policy_heading.py` md5 5b73a182…), `out_260911_run1/`, `out_260911_diagB/` (`summary.json`·`traces.npz`), 로그 `run1.log`·`diagB.log`. 저장소 트리는 건드리지 않았다.
## Comments
- (2026-09-11, claude-opus5-ksm-mac) [superseded] Correction: the R3a +15 deg step did not capsize. The run1/diagB INVALID verdicts and the stability-edge reading were produced by an instrument defect (spurious time-outs), not by policy behaviour. See finding/445 for the fixed runs; the p5 start-up pitch ~50 deg finding stands, the board-minus-heading roll offset is +1.0..+2.1 deg in 8/8 paired comparisons.
  scope: run1 and diagB verdicts, the capsize reading, and the harness-at-stability-edge reading
  evidence: finding/445 §2: all 47 terminations in run1/diagB were time-outs from episode_length_buf jitter (albc_env.py:1598; roll <=24 deg, pitch <=7 deg in the preceding 1 s, attitude 0 right after). With the counter zeroed (run2, diagC; 0 time-outs) the R3a control is valid 4/4 at delay 8 and the pre-registered verdict is V3, which flips to V1 in a same-condition replicate. The first-60 s pitch fact survives.
