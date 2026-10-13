# grasp-step exam tooling validated on GPU1: zero-command hold + per-level payload toggle; the draft's none tier has 0 kg payload and is refused; smoke found three silent defects (Hydra toggle crash, time-out slack, reset jitter skipping the toggle)

- id: finding/452 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-09-12 · keywords: paper-ablation-5000, grasp-step, payload toggle, hold-zero-cmd, eval.py static, episode_length_buf jitter, Isaac Kit SystemExit, readout, GPU1
- summary: Grasp worktree eval/grasp-step 1a5981d (on afa3c6b): --hold-zero-cmd/--hold-seconds, --payload-toggle-step/--payload-start-with injected per level after the level DR, per-step payload_mass/payload_cog_offset trace, tools/grasp_step_readout.py (agy draft, 8 tests, 2 mutations caught). Draft premises that failed: eval none level has 0 kg payload (pick raises uniform_(0.1,0.0), drop has no step) -> soft,medium,hard pending operator decision; a Hydra env toggle crashes the construction reset. Smoke-found defects fixed: +0.02 s slack flags every env terminated (+10 s); albc_env.py:1756 marks envs past the toggle from the jittered episode_length_buf, so eval re-arms after its restart (64/64 envs toggle once vs 1/4 skipped before); SystemExit returns rc 0 inside Kit (RuntimeError). Smoke 4 K0-K6 and a 4-env chain check pass; queued r3a5000_grasp_v1 (chain md5 f7f0697d), nothing launched.

**파지 계단(grasp-step) 시험 도구를 만들고 GPU1 스모크로 검증했다. 발사는 사람 몫이고 아직 아무것도 돌지 않았다.** 설계 정본은 PLAN `## Update 2026-09-12 (04시 KST)`, 승인 초안 vault `.omc/proposals/grasp-step-exam-draft.md`, 요청 `.hq/work/scholar/albc/handoff-marinelab-2026-09-11.md` §1.

## 1. 초안 전제 둘이 무너졌다
| 전제 | 실측 | 영향 |
|:--|:--|:--|
| tier none·hard | eval `none` 레벨의 payload 는 공칭 0 kg(`analysis/dr_config.py` `_TRUE_NOMINAL_PHYSICS`). pick 은 `_setup_payload_toggle` 의 stash 보정이 `uniform_(0.1, 0.0)` 으로 RuntimeError(G3), drop 은 0 → 0 이라 계단이 없다 | none 제외, soft·medium·hard 권고 — **사용자 판단 대기** |
| 토글은 cfg `payload_toggle_steps` 로 켠다 | `eval.py static` 은 env 를 none DR 로 생성한다(`apply_dr_config(env_cfg, DR_SCALE["none"])`). Hydra `env.payload_toggle_steps=750 env.payload_start_with_prob=0.0` 이면 생성 리셋에서 soft·hard 셀도 크래시(G1·G4·G5, rc 1, 20~30 s) | 레벨 DR 을 적용한 뒤 `raw_env.cfg` 에 주입하는 플래그로 바꿨다 |

그 밖에 넷:
- 리셋은 `_reset_framework` 에서 `episode_length_buf` 를 에피소드의 최대 절반까지 지터한 **뒤** `_setup_payload_toggle`(`albc_env.py:1756`)이 `buf >= payload_toggle_steps` 인 env 를 "이미 토글 시점을 지남" 으로 표시한다. eval 은 그 뒤 buf 를 0 으로 되돌리지만 표시는 남는다. 슬랙 +10 s(에피소드 2000 스텝, 지터 최대 1000)에서는 지터가 750~999 인 env 가 끝까지 토글하지 않았다(스모크 3 F1 hard env2 — 판독기가 `no_toggle` 로 잡아 rc 2). eval 이 buf 를 0 으로 되돌린 직후 토글이 켜져 있으면 표시·카운터를 다시 무장한다.
- codex 초안의 hold 슬랙 +0.02 s 는 마지막 스텝을 time-out 으로 만들어 모든 env 가 `terminated` 로 읽혔다(스모크 2 전 셀 alive_until 1499). 궤적 경로와 같은 +10 s 로 바꿨다.
- `raise SystemExit` 는 Isaac Kit 안에서 프로세스 rc 0 으로 끝났다(H3). 새 가드는 `RuntimeError` 로 바꿨고(K3 rc 1), 체인은 eval rc 에 더해 판독기 `--levels` 로 빠진 레벨을 rc 1 로 잡는다.
- pick 방향에서 DR 추첨이 0.1 kg 미만인 env 는 env 보정이 그 레벨 cfg 범위 uniform(0.1, hi) 에서 다시 뽑는다(soft env1 0.022 → 0.271 kg). DORAEMON 분포가 아니라 레벨 cfg 범위이므로 판독표에 질량 전·후 통계를 같이 싣는다.

## 2. 구현 — branch `eval/grasp-step` (afa3c6b 위, 로컬 커밋 `1a5981d`)
- `eval.py static`: `--hold-zero-cmd`·`--hold-seconds`(모든 명령 채널 0, 단일 구간, 슬랙 10 s), `--payload-toggle-step`·`--payload-start-with`(레벨 DR 뒤 주입, payload 없는 레벨은 FATAL 로 거부), `--save-extras` 에 스텝별 `payload_mass`(T,N)·`payload_cog_offset`(T,N,3), `extras_meta.json` 에 토글·hold 기록. 기본 경로는 그대로.
- `tools/grasp_step_readout.py`: agy(ground 1)가 세션 명세로 작성했고 세션이 1건 고쳤다(구분선 문자열 따옴표 누락 SyntaxError). 사전등록 정의는 PLAN 04시 절. 테스트 8종, 변이 둘(정착 탐색을 토글부터 시작 / 생존 창 제한 제거)이 각각 테스트를 실패시켰다.
- 평가 워크트리와 분리한 이유: 평가 워크트리 HEAD 를 옮기면 큐의 채점 체인(`EXPECT_EVAL_HEAD=afa3c6b`)이 FATAL 이 된다.
- 체인 `grasp_chain_r3a.sh`: 행(파일럿 inc9998 + 준비된 앵커 B 4행) × pick·drop, soft·medium·hard, 64 env, grasp·marinelab 커밋 핀과 clean 검사(시작과 잠금 안), GPU1 잠금(background + `wait`, TERM trap), 판독 rc 0 뒤에만 `.complete`.

## 3. 검증 (4 env 스모크 — 수치는 결과가 아니다)
셀 규약: GPU1 잠금, seed 42, `--env-dr-anchor` + 행의 DORAEMON 박스, `--hold-zero-cmd --hold-seconds 30 --payload-toggle-step 750`. K1 만 64 env.

| 셀 | 조건 | 결과 |
|:--|:--|:--|
| K0 | 새 플래그 없이 기존 경로 | data 192/192 키, extras 공통 44/44 키가 패치 전(V1b)과 비트 동일. 새 extras 키는 `payload_mass`·`payload_cog_offset` 둘 |
| K1 | 파일럿 pick, hard, 64 env | 64/64 env 가 생존 구간에서 정확히 한 번 토글, `instrument_ok`, survival 1.0. 질량 0 → 평균 1.59 kg(P90 2.69), roll 피크 편차 평균 1.72°, 정착 평균 1.54 s(미정착 3/64). 재무장 전 스모크 3 은 4 env 중 1 이 토글하지 않았다 |
| K2 | 파일럿 drop, soft·hard | eval rc 0, 판독 rc 0, 전 env ok |
| K3 | none 레벨 pick | `RuntimeError` rc 1, npz 0 |
| K4 | p3b model_7500 pick, medium | rc 0, 판독 ok |
| K5 | R3a GRU 학생 pick, soft | rc 0, 판독 ok |
| K6 | R3b TCN 학생 drop, hard | rc 0, 판독 ok |

- 체인 실검증 `NENV=4 ONLY=pilot_inc9998 EXPECT_GRASP_HEAD=1a5981d`: pick·drop 2셀 × soft·medium·hard 전부 판독 ok, `.complete` 입력 identity 기록, `grasp_summary.md` 생성, 셀당 93 s, 네 워크트리 clean. 체인 md5 f7f0697d 를 PLAN 폴더에 두고 `r3a5000_grasp_v1` 을 큐에 올렸다(pending approval).
- hold 모드의 `summary.json` 스텝 궤적 총계(`total_att_error` 등)는 구조상 nan — hold 구간 이름이 attitude·lin_vel·yaw 블록으로 분류되지 않는다(`_eval_dr/metrics.py` `_classify_segment`). 이 시험의 계측기는 판독기다.

## 4. 교차검토
agy(`gemini-3.1-pro-high`, ground 4)에 eval diff 와 체인 초안을 넘겼다. 4건:
| # | 지적 | 판정 |
|:--|:--|:--|
| 1 | hold 가 targets 를 1차원 0 배열로 만들어 형상 오류로 죽는다 (blocker) | **기각** — 채널은 원래 1차원 시계열이고(`_eval_dr/trajectory.py:111`) eval 은 스텝마다 스칼라를 명령 열에 쓴다(`eval.py:875-994`). hold 셀이 스모크·체인에서 끝까지 돌았다 |
| 2 | `SystemExit` 가 Kit 안에서 rc 0 → 일부 레벨이 빠진 셀이 완료로 찍힌다 (major) | **수용** — `RuntimeError` 로 교체(K3 rc 1), 체인 판독에 `--levels soft,medium,hard`(빠진 레벨 = rc 1) |
| 3 | 잠금 `9>"$LOCK"` 가 다른 체인의 잠금 파일 내용을 지운다 (minor) | **기각** — 잠금 파일은 내용을 담지 않고 flock 에만 쓴다 |
| 4 | 합본 루프가 만들어지지 않는 `grasp_step_readout.md` 를 찾는다 (minor) | **기각** — 판독기가 그 파일을 기본으로 쓴다(`grasp_step_readout.py:415`); 체인 실검증에서 합본 생성 |

같은 계열 두 번째 검토자는 두지 않았다(codex 한도). 두 계열 게이트는 충족하지 않았다 — 기록한다.

## 5. 남은 것
- tier: 초안 none·hard → soft·medium·hard 권고, **사용자 결정 대기**.
- 발사는 사람만: `EXPECT_GRASP_HEAD=1a5981d645ea8f3e6eda2b9b646c04eccc034f98 nohup bash .hq/community/programs/paper-ablation-5000/grasp_chain_r3a.sh > .hq/work/paper_ablation_r3a/grasp_chain_v1.out 2>&1 &`
- 10 arm·고전 제어기 행은 학습·게인 선정 뒤 체인 `ROWS` 에 한 줄씩 추가한다.
## Comments
