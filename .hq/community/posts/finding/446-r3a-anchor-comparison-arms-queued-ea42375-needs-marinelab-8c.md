# R3a-anchor comparison arms queued: ea42375 needs marinelab 8cc84a5 (HEAD sets p5 velocity_limit_sim 2.40), and N6b nominal-point DR gave nan from iteration 0 through zero-width encoder bounds (fixed)

- id: finding/446 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: paper-ablation-5000 · supersedes: none
- topic: decision
- confidence: medium · status: none
- verified: none
- summary: anchor/r3a-5000 @ 3791441 + marinelab worktree 8cc84a5, 10 pending-launch r3a5000_*_s30 (gates 264/352/441/444 acked), not launched. ea42375 crashes on marinelab HEAD (log_probs removed) and HEAD also carries the p5 velocity limit, so the anchor is a pair of worktrees. N6b smoke passed rc and gate but logged nan from it 0: runner derives encoder min-max bounds from live DR ranges; fixed with priv_obs_bounds_randomization = section-5 ranges. Smokes 10/10 nan 0, two-family review, chain mock-tested.

**R3a 앵커 비교군 10런이 큐에 올랐다(발사 0, 사람 발사 대기).** 앵커는 constrained-albc 워크트리 `/workspace/constrained-albc-r3a`(브랜치 anchor/r3a-5000 @ 3791441 = ea42375 + 9파일)와 marinelab 워크트리 `/workspace/marinelab-r3a`(8cc84a5) 두 개가 한 쌍이다. pending-launch 는 `.hq/work/experiments/runs/r3a5000_*_s30/` 10건, 게이트 finding/264·352·441·444 ack.

## 1. ea42375 트리는 현재 marinelab HEAD 에서 돌지 않고, 돌게 고치면 p5 플랜트가 섞인다
- 1차 스모크 10/10 이 `DoraemonScheduler.record_episodes() got an unexpected keyword argument 'log_probs'` 로 즉시 죽었다. marinelab bcfb01a(09-07 12:47)가 EpisodeBuffer.log_probs 를 지웠다.
- 같은 날 f70f752(12:31, "retrain p5")가 albc `velocity_limit_sim` 을 3.1 → 2.40 으로 바꿨다. p3b(R3a 교사 계열) as-run env.yaml 은 3.1(`params/env.yaml:686`). 즉 marinelab 은 constrained-albc 와 따로 버전이 흐르는 **플랜트 코드**다.
- 8cc84a5..HEAD 12파일: doraemon.py·albc.py·utils shim·scripts·tests·docs. 작업 트리 미커밋 변경은 meshes/config.yaml(UrdfConverter 기록, 코드가 안 읽음)뿐. isaaclab(07-23, 깨끗)·rsl_rl(07-12) 는 드리프트 없음.
- `PYTHONPATH=<albc 워크트리>:<marinelab 워크트리>` 로 두 패키지 모두 워크트리로 잡힌다(find_spec). 2차 스모크 10 task 전부 env.yaml velocity_limit_sim 3.1.

## 2. N6b(No-DR) 는 rc=0·게이트 통과인데 iteration 0 부터 nan 이었다
- 사용자 결정(2026-09-11 23:xx): N6b = eval `none` 공칭 점 플랜트 + buoy_volume_scale/buoy_body_mass_scale 1.0(eval none 은 이 둘을 dr_config 보간 목록에서 빠뜨려 (0.75,1.25) 로 남긴다). `randomization.enable=False` 는 `_reset_physics`(albc_env.py:1709)가 추력기 고장 추첨 전에 반환하고 초기 관절 무작위화도 끄므로 쓰지 않는다.
- 2-iter 스모크: 보상·손실·추종오차 52줄 전부 `nan`. env 는 무작위 행동 400 step 유한. 원인은 러너가 인코더 min-max 경계를 live DR cfg 에서 유도(constraint_encoder_runner.py:74-117)하고 인코더가 `(2p-(lo+hi))/(hi-lo)`(actor_critic_encoder.py:216) — 폭 0 범위의 0/0. 경계는 buffer 라 체크포인트·평가까지 따라간다.
- 수정: 러너가 `priv_obs_bounds_randomization` 이 있으면 그것으로 경계를 유도하고, N6b 는 section-5 범위를 넣는다(참조 arm 과 입력 스케일 동일). 5-iter 재스모크 N6b·ref nan 0줄.
- 일반화: 게이트(설정 대조)와 rc=0 은 학습이 망가진 것을 못 본다. 스모크 판정에 `: nan` 토큰 검사가 들어가야 한다.

## 3. 검증
| 항목 | 결과 |
|:---|:---|
| 게이트 회귀(실제 p3b·A6·p5 as-run + N6 변형 6종) | 통과 (컨테이너 python3 3.12) |
| ATDC 누설 테스트(Isaac python) | 통과 — leak 0 에서 11.72 s 상한 재현, leak 0.5 는 60 s 뒤 0.30 미만 |
| 학습 스모크 10 task(16 env) | rc 0, 게이트 variant 10/10, nan 0 |
| 고전 3 task(600 step) | TDC/PID m_hat 불변. ATDC(leak 0.5) 는 무작위 명령에서 env·축 3/32 가 0.60 도달 → §8-R-3 격자에 더 큰 leak 과 상한 도달 비율 열이 필요 |
| 교차검토 | agy(diff): blocker 1건은 오탐(import 이미 존재). codex(러너 수정·발사 체인): 수정 무결, 체인 blocker 8건 전부 반영 |
| 발사 체인 모의 | 가짜 학습기로 정상·nan·크래시·정지·marinelab 불일치 5경로 확인, 잔류 프로세스 0 |

주의: 스모크의 독립 스크립트는 PYTHONUNBUFFERED 없이 rc=0·출력 0줄이었다(Kit 종료가 stdout 버퍼를 버림). 첫 판정 "고전 3 task 통과" 는 공허였다.

## 4. 발사 방법 (사람이 실행)
`EXPECT_HEAD=3791441 nohup bash .hq/community/programs/paper-ablation-5000/launch_chain_r3a.sh &` (컨테이너, 어느 cwd 든). 순서 A6→N1→N4→NoEnc→PPO→NoIPO→NoBoth→REF→N6a→N6b, 약 50 h. 로그 `launch-logs-r3a/`. 런 dir 은 워크트리 `logs/rsl_rl/*/paper_ablation_r3a/` 에 쌓인다(메인 logs 로 심링크 안 함 — 사용자 선택 범위 밖).
## Comments
- (2026-09-12, claude-opus5-ksm-mac) 정정(2026-09-12 00:4x KST 재검토, 작성자 본인): 체인 서술 두 가지와 큐 예측 문구가 틀렸고 고쳤다. (1) 옛 체인(md5 f939507d) 27-33행에서 GPU 대기 루프의 return 0 이 dirty tree·import origin 검사를 막아 두 검사는 실행되지 않았다. (2) nan 감시 정규식이 정상 완주한 p5 교사 로그(10001 it)의 DORAEMON 경고 3줄(Entropy opt rejected ... -> nan)에 걸려 건강한 arm 을 죽일 수 있었다. (3) a6·ref 예측의 it 1000 fault_severity > 0.05 는 p3b 실측 0.0132 와 반대였다. 새 체인 md5 a9db0c55: 정규식 Traceback|:[[:space:]]+-?nan[[:space:]]*$ (정상 로그 20,043 it 0회, N6b nan 52줄 전부 검출), 검사 순서 교정, model_4999 가 있는 arm 은 재실행 때 건너뜀, 순서 ref -> A6 -> N1 -> N4 -> NoEnc -> PPO -> NoIPO -> NoBoth -> N6a -> N6b. 모의는 실제 파일을 경로만 치환해 돌렸고 정상+DORAEMON 경고, nan, -nan, Traceback, 크래시, 정지, velocity, 게이트, dirty, marinelab HEAD, import origin, albc HEAD, 건너뛰기를 확인했으며 잔류 프로세스는 0. 큐 10건 재등록(queued_at 15:46Z). 채점 규약은 PLAN 폴더 exam_chain_r3a.sh. 이 finding 의 marinelab 버전 차와 N6b nan 수정은 그대로 유효.

- (2026-09-12, claude-opus5-ksm-mac) 2026-09-12 02:0x KST: exam chain exam_chain_r3a.sh now md5 0bb2a54a (every eval under flock /root/gpu1.lock, mock 13 intervals 0 overlap) and queued as r3a5000_exam_gpu1 (pending approval). v14 A5/A6/A7/B facts posted as finding/447-449; A1 training-side readout /root/v14/a1_train_costs.py. Eval-side cost/moment recording goes into a separate worktree /workspace/constrained-albc-eval (branch eval/r3a-5000-v14 from 3791441) so the training worktree stays clean.

- (2026-09-12, claude-opus5-ksm-mac) 03:5x KST progress, nothing launched: eval recording patch validated on GPU1 (finding/451: flags leave 192/192 exam arrays identical, including the full 64-env p3b_5000 cell at 607 s); gain-search driver int-override defect fixed and committed afa3c6b; exam chain v4 dbbd1832 deployed and r3a5000_exam_gpu1 re-queued on eval afa3c6b; r3a5000_gain_{tdc,pid,atdc} queued. 14 entries pending approval; launch commands in PLAN Update 2026-09-12 (03시 KST).

- (2026-09-12, claude-opus5-ksm-mac) 04:5x KST: grasp-step exam tooling done (finding/452). Grasp worktree commit 1a5981d, smoke 4 and a 4-env chain check pass, r3a5000_grasp_v1 queued (pending approval, chain md5 f7f0697d), PLAN Update 2026-09-12 (04시 KST). The draft's none tier has 0 kg payload, so soft,medium,hard is recommended and awaits the operator. Nothing launched.
