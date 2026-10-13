# v14 A6/A7: Table V exam is a 155 s 31-segment trajectory with a yaw-RATE block (heading came 09-07, after that exam and the anchor), 2.5 rad per-axis termination; paired SE keeps roll OS Hard full-vs-PPO a tie (1.92 SE) but makes pitch OS Hard full-vs-no_encoder a separation (3.58 SE)

- id: finding/448 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: reference
- confidence: high · status: none
- verified: 2026-09-12 · keywords: v14, A6, A7, F-4, F-5, F-17, eval protocol, yaw rate, overshoot, paired SE, common set, finding/393, Table V
- summary: 54.4 s is an eval-episode capsize time (env 45, full_method hard), 30 s is the training horizon. Yaw OS = overshoot of measured yaw rate relative to the commanded rate step (389c0cd metrics.py); a subagent HEAD-based heading claim was wrong (4078564 is 2026-09-07 12:49). The manuscript 1.72 SE compares full vs no_encoder, not PPO. Paired on the 62-env common set: roll 1.654x->1.921x, pitch 1.718x->3.580x. Table V Roll OS Hard 10.77/13.21 are common-set values, contradicting finding/393 for that column.

**v14 AC 요청 A6(평가 프로토콜 사실)·A7(paired SE) 답.** 옛 Table V 채점(`paper_ablation_5000/*/eval_ablation_5000/static_260824_150028`, 공유 draw, 64 env, seed 42, DORAEMON 앵커 = 선택 교사 iterbudget)과 앵커 B 채점 규약 기준. 새 평가 없음.

## A6-1. 평가 에피소드는 155 s 궤적이다 — "54.4 s" 와 "30 s" 는 다른 양
- 궤적 = 31 세그먼트 × 5.0 s(`--segment_duration` 기본) = 155 s, 7750 step × 0.02 s(`data_hard.npz` `time[-1]` 155.0). eval 은 `episode_length_s = 31 × seg + 10`(165 s)로 잡아 궤적 중 time_out 이 없게 한다.
- supp 의 30 s 는 **학습** 롤아웃 에피소드(S1 표), 54.4 s 는 **평가** 에피소드 안에서 한 env 가 버틴 시간이다. full_method `data_hard.npz` 에서 env 45 가 step 2718(54.4 s), env 43 이 step 804(16.1 s)에 처음 terminated — supp:166-167 수치와 일치.

## A6-2. 명령 계단 (Table V 채점 당시 코드 389c0cd = 2026-08-24, 앵커 3791441 도 같다)
- 31 세그먼트: warmup 1 · 자세 블록 12(영점 1 + 3×3 격자 ±30° 9 + 복귀 2) · warmup 1 · 선속도 블록 11(영점 1 + 2×2×2 코너 ±0.25 m/s 8 + 복귀 2) · warmup 1 · yaw 블록 5(영점 1 + +w·−w 2 + 복귀 2). 합 1+12+1+11+1+5 = 31. warmup 세그먼트는 지표에서 빠진다.
- 앵커 B 채점(`exam_chain_r3a.sh`)은 같은 스케줄에 `--att-amp-deg 15` 를 쓴다.

## A6-3. Yaw 는 이 채점들에서 **rate** 계단이다 — "Yaw OS" 는 rate 계단 크기 대비 %
- ⚠️ 조사 에이전트가 main HEAD(1bb5802) 코드를 읽고 "yaw 는 heading 목표이고 원고의 yaw rate 서술이 낡았다"고 보고했는데 **틀렸다.** heading 전환은 `4078564`(2026-09-07 12:49, "yaw command: rate -> position")로, Table V 채점(08-24)과 앵커 ea42375(09-07 01:38)보다 뒤다.
- 채점 당시 `trajectory.py`: `YAW_RATE_AMP = 0.5` rad/s, 블록 = +0.5, −0.5, 0, 0. `config.py` `yaw_rate_cmd_range (−0.5, 0.5)`. npz 키도 `yaw_rate`·`target_yaw_rate` 뿐이다. 원고 system.tex:94 "yaw rate (reference range −0.5 to 0.5 rad/s)" 는 이 데이터에 맞다.
- Yaw OS = `_step_response_scalar_segment(yaw_rate, alive, prev_target, cur_target, min_step_mag=0.01)` — 측정 yaw rate 의 계단 응답 overshoot 를 **명령 rate 계단 크기**(0→+0.5 는 0.5, +0.5→−0.5 는 1.0, −0.5→0 은 0.5, 마지막 0→0 은 계단 없음이라 제외) 대비 % 로 잰다(389c0cd `_eval_dr/metrics.py` yaw 블록). roll/pitch OS 와 같은 형식이지만 대상이 각도가 아니라 각속도다.

## A6-4. 종료 기준
eval 이 `max_attitude_angle = 2.5` rad 로 덮고, env 는 `|roll| > 2.5 or |pitch| > 2.5` 로 축별 독립 판정한다(결합 노름 아님). 학습 기본은 π/2.

## A6-5. 원고 그림 후보 (새 GPU 불필요, 기존 npz)
- 전복 궤적: full_method `data_hard.npz` env 45(54.4 s) 또는 env 43(16.1 s).
- PPO overshoot: ppo `.../ppo_paper_abl_ppo_260825_002302/eval_ablation_5000/static_260824_150028/data_hard.npz` env 43(에피소드 최대 |roll| 60.84°, 64/64 생존). 에피소드 전체 최대치로 고른 거친 선택이라 그림 세션이 자세 세그먼트를 다시 잘라 고를 것.

## A7. paired SE — 62-env 공통 생존 집합(full_method 가 env 43·45 를 잃음)
원고 문장부터 대조했다. **1.72×SE 는 PPO 가 아니라 no_encoder 와의 비교다**(simulation.tex:188-189 "best arm to the runner-up … 1.72×SE at Hard"; pitch OS Hard 2위 = no_encoder). 요청문의 "pitch OS Hard(선택 교사 vs PPO)"는 부정확하고, 두 수치 모두 선택 교사(9998)가 아니라 Table V full method(5000 it) 이야기다.

| 비교 | unpaired 차 (SE, 배수) | paired n · 평균차 · SD · **SE** · 배수 | 판정 |
|:--|:--|:--|:--|
| Roll OS Hard, full − PPO | −2.445 pp (1.478, **1.654×**) = 원고 1.65× | 62 · −2.445 · 10.018 · **1.272** · **1.92×** | tie 유지(2× 미만, 문턱 근접) |
| Pitch OS Hard, full − no_encoder | −1.170 pp (0.681, **1.718×**) = 원고 1.72× | 62 · −1.170 · 2.574 · **0.327** · **3.58×** | **tie → separation** |
| 참고: Pitch OS Hard, full − PPO | −1.602 pp (0.719, 2.23×) | 62 · −1.602 · 5.014 · 0.637 · 2.52× | 원고 미언급 |

- supp 의 "paired 로 바꿔도 판정이 안 바뀐다"는 일반 문장은 pitch OS Hard(full vs no_encoder) 셀에서 틀린다. 원고가 Pitch OS 열을 뺀 근거("at most marginally resolvable")도 paired 기준으로는 다시 봐야 한다.
- 정규근사 SE 이고 단일 학습 시드·단일 평가 시드 안의 env 짝짓기다 — 학습 시드 변동(F-5)과 다른 축.

## 부가: finding/393 의 "OS 열은 보정 안 됨"은 Roll OS Hard 에 안 맞는다
Table V Roll OS Hard 10.77 / 13.21 은 summary.json raw(own-survivor 평균 12.228 / 15.225)가 아니라 62-env 공통 집합 값(10.767 / 13.212)과 같다. None 은 전 arm 생존이라 구분 불가, Yaw OS Hard 는 두 방식이 20.585 / 20.590 으로 수치 구분 불가. 표를 만든 원 명령은 저장소에서 못 찾았다(`grep 10.77` 0건).

## 검증
- 세션이 `/root/v14work/a7_paired_se.py` 를 다시 돌려 위 두 핵심 셀과 원고 1.65×·1.72×·10.77·13.21 재현 확인. `a6_repr_envs.py` 재실행으로 전복 시각 16.1·54.4 s 확인.
- yaw 의미는 세션이 채점 시점 커밋(389c0cd)의 `trajectory.py`·`metrics.py` 와 heading 전환 커밋 날짜로 직접 확인.
- 조사: native 서브에이전트(판독 전용), 판정·정정: 오케스트레이터 세션.
## Comments
