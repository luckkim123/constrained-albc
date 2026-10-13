# 재개 브리프 — 2026-09-13 (일) 11:30 KST, 세션 교대

이 문서 하나로 이어받을 수 있게 썼다. 수치는 전부 11:23 실측이다. 옮겨 적은 판정은 행동 전에 원본을 다시 확인하라.

## 1. 운영자 지시 원문 (우선순위 순)

1. **depth-xy 시험이 모든 자원 배분의 1순위.**
   - 07:5x: "xy를 먼저 테스트할 수 있게 하라고 이거 내가 몇번째 말한건지도 모르겠네"
   - 같은 시각: "대체 몇번 쳐 말해야 하는거임? 한 두번으로는 안되나?"
   - 09-12 23:0x 에도 같은 지적이 있었다: "depth xy가 맨 마지막이네. 이걸 좀 빨리 해달라 한걸로 기억나는데"
   - 다른 작업을 이보다 앞에 두려면 먼저 묻는다.
2. **시험과 학생 둘 다 이번 주말 범위.** 07:4x AskUserQuestion 답 "시험과 학생 둘 다 (Recommended)".
   - 선택지 설명문: 시험 도구와 학생 경로 수정(80D 꼬리 오독 해결 + 테스트)을 병렬로 작성 → GPU0 가 비면 teacher 시험, 학생 증류(R2 기준 약 12분), 학생 시험 순. 보드 배포(스러스터 소유권 변경)는 별도 결정으로 남긴다.
3. **"기록 남기고 계속 모니터링해줘"** — 세 자원(DGX, GPU0, GPU1) 감시와 기록을 계속한다.
4. **원 요청** (09-12 04:3x): "근데 궁금한게 지금은 학습이 자세라 제어만 하는데 여기에 xyz 제어까지 추가해도 되는거 아니야? 기존 제어기들이 제어하는 방식 정도로만 하면 dvl이 없는 로봇이어도 가능할 것 같은데? 이것도 해봐줄 수 있어? 이건 병렬로 하기 위해 ksm nas에서 하자. 주말중에 전부 실험해봐야하니깐"
5. **"n6a랑 n6b는 빼고 그냥 가자"**

## 2. 지금 상태 (11:23 KST 실측)

| 자원 | 상태 | 다음 사건 |
|:--|:--|:--|
| DGX | `n1_lagrangian` model_2850. 5.58 s/iter (model_0 06:56:53 → model_250 07:20:08). 체인 `~/xyz_launch/launch_paper_dgx_b.sh` 생존, 로그 `~/xyz_launch/paper_dgx_b.out` | 14:42경 END → `n4_residual` START·GATE → 22:30경 END. 주말 마감 여유 약 1.5 h |
| GPU0 | 마지막 paper arm `noboth` model_2500. 2.43 s/iter (09:41:17 → 11:22:39). 완주 5/6: ref_full, a6_ppoenc, noenc, ppo, noipo(END 09:41:04 rc=0 ok=1) | 13:05경 END → 체인 종료 → **GPU0 빔** |
| GPU1 | **유휴** (19 MiB, 0 %). 게인 tdc 75/75, pid 75/75 (마지막 셀 10:49). **`--select` 미실행** → `selection.json` 없음 → atdc 9셀 미발사. 채점 체인 `exam_chain_r3a.sh` 생존, 36셀 완료, noboth 체크포인트 대기 | 브리프 4절 순서 |
| depth-xy teacher | 06:56:37 완주, 정지 서명 없음 (depth-xy PLAN `## Update 2026-09-13 (07시 KST)`) | 시험 없음 — 이것이 1순위 |

DGX 체크포인트의 컨테이너 사본 (md5 일치 확인):

| 런 | 경로 (`/workspace/constrained-albc-xyz/logs/rsl_rl/albc_trpo_teacher/` 아래) | md5 model_2500 / model_4999 |
|:--|:--|:--|
| depth-xy arm | `depth_xy_ftc_dgx/trpo_dgx_depthxy_260912_230816/` (+ `params/`) | 628ba757 / 2843fd7c |
| DGX 자세만 기준선 | `paper_ablation_r3a_dgx/trpo_dgx_ref_260912_144855/` (+ `params/`) | 08484ef5 / 8a820d41 |

## 3. 중단된 작업

08시대에 executor 에이전트 2개가 API 인증 오류(403)로 중단됐다. 보고서는 없고, 확인한 것은 AST 파싱 통과뿐이다.

| 워크트리 (커밋 안 됨, 둘 다 @51f6a05) | 남은 편집 | 없는 것 |
|:--|:--|:--|
| `/workspace/xyz-exam` (`exp/depth-xy-exam`) | `constrained_albc/analysis/eval.py` +248 (`depthxy` 서브커맨드: `--control-delay`, `--doraemon-dr(-from)`, `--env-dr-anchor`, `--levels`, `_depthxy_rollout`), `constrained_albc/analysis/_eval_dr/depthxy.py` 173줄 (`SCHEDULE_DURATION_S`, `build_depthxy_schedule`, `compute_depthxy_metrics`, `render_depthxy_markdown`), `tests/test_eval_depthxy.py` 94줄 | 명령 override 가 실제로 먹는지 증명, 테스트 실행, GPU1 스모크, 본 시험 명령 |
| `/workspace/xyz-student` (`exp/depth-xy-student`) | 6 파일 +67/−9 (`_core/student/{config,models,runner,teacher}.py`, `analysis/{eval,student_policy}.py`) + `tests/test_student_depth_xy_layout.py` 136줄. 설계: `policy_tail_after(env_cfg)` = `depth_xy.enable` 이면 4, 아니면 0. `StudentCfg.policy_tail_after` 로 체크포인트에 기록하고, eval 은 env 와 다르면 거부. `split_policy_tail(n_after)` 가 `[-8:-4]` 를 raw 로 떼고 depth_xy 4차원은 정규화 core 에 남긴다 | 테스트 실행, `scripts/train_student.py` 의 `_check_tail_mode_consistency` 반영 여부, 2 it 스모크, eval 경유 로드, `deploy/specs/student_gru.py`, 전체 증류 명령 |

오독의 근거: depth-xy 관측 4개가 gen-2 채널 **뒤에** 붙는다(`albc_env.py:1297` gen-2, `:1302` depth_xy). 그런데 `POLICY_TAIL_N=4` 꼬리 모드(`_core/student/models.py:25`, `config.py:76`)는 마지막 4차원을 IMU·heave 로 읽는다.

## 4. 다음 순서

1. **감시 재가동.** 스크립트는 `ssh marinelab-container cat /workspace/constrained-albc/.hq/work/paper_ablation_r3a/mac_watch_loop.sh` 에 있다(md5 d2f65cbf). 새 scratchpad 에 저장한 뒤 Monitor 를 `persistent: true` 로 건다. `trig()` 기준선은 첫 줄이 새로 잡는다.
2. **depth-xy 시험 도구 완성과 실행 (GPU1, 지금 빔).** `xyz-exam` 편집을 리뷰한다. 명세는 5절 A.
   - 테스트 → GPU1 스모크(arm model_4999, 16 envs, DR none, healthy, `flock /root/gpu1.lock`) → 본 시험(arm model_2500·model_4999 × healthy·pair34 × none/soft/medium/hard) 순으로 진행하고 결과를 보고한다.
3. **DGX 두 런의 자세 시험.** paper static exam 과 같은 플래그를 쓴다(`exam_chain_r3a.sh` 의 `exam()`: `--fault_fixed_health`, `--att-amp-deg 15`, `--control-delay`, SEG, `--env-dr-anchor --doraemon-dr-from`, `--save-extras`, `--seed 42`).
   - 대상: arm(task `...-SimToReal-DepthXY-v0`)과 기준선(`...-TRPO-SimToReal-v0`)의 model_2500·model_4999.
   - `exam_chain_r3a.sh` 는 **실행 중이라 수정 금지**. 별도 스크립트로 같은 락을 쓴다.
   - DGX 수치는 DGX 기준선하고만 비교한다(머신 효과 +109 %, finding/001).
4. **학생.** `xyz-student` 를 리뷰 → 테스트 → 스모크(GPU1). GPU0 가 비는 13:05경 R3a 레시피로 증류한다.
   - R3a 레시피: GRU, DAgger beta 1.0→0.0 을 600 it 에 걸쳐 anneal, 1000 it, 4096 envs, teacher 는 depth-xy model_4999.
   - 근거: retrain-simtoreal PLAN R3a 행, `finding/387`, `decision/390`, 런 `trpo_sd_p3b7500_c3_dr5_beta0_s30_260906_003754` 의 params.
   - 증류가 끝나면 학생 시험을 돌린다. 발사 명령은 발사 전에 화면에 먼저 올린다.
5. **게인.** `classical_gain_search.py --controller tdc --select`, `--controller pid --select` → atdc `--run` (9셀, `tdc/selection.json` 필요) → atdc `--select`.
   - 도구 경로 `/workspace/constrained-albc-eval/tools/`. 발사 형식은 paper-ablation PLAN 1128행.
   - `--select` 가 GPU 를 쓰는지 먼저 확인한다. atdc 셀은 운영자 우선순위에 따라 depth-xy GPU1 작업 뒤에 둔다. 앞당기려면 묻는다.
   - 채점 체인은 `selection.json` 이 생기면 `classical_*` 행을 자동으로 채점한다(PLAN 1082행).
6. **DGX.** n1 END 에서 rc·ok·model_4999·.chain_ok 를 확인하고, n4 GATE 와 n4 속도를 확인한다.
7. **기록.** 세션 로그 행(`.hq/community/sessions/2026-09-12-v14-night.md`), 두 PLAN 의 Update 절(수정 전후 `omx program-lint` 비교), 메모리 `project_albc_depth_xy_ftc_program_2026_09_12.md`.

## 5. 부록 — 중단된 에이전트에게 준 명세 요지

**A. 시험 도구 (xyz-exam).** 승인 PLAN 원문: "a depth/xy exam on the arm (depth steps +-0.3 m, hover, xy force steps at attitude 0; depth ss error, settling, attitude deviation, force tracking; mean/median/P90/max)".

1. env 의 무작위 depth·xy 명령 샘플링(`_sample_velocity_command`, 250 step 마다 재샘플, hover 확률 0.10)을 결정적 스케줄로 덮는다. 자세 명령은 0 이다.
   - 제안 스케줄: hover 5 s → +0.3 m 10 s → 복귀 10 s → −0.3 m 10 s → 복귀 10 s → u_xy (+1,0)·(0,+1)·(−1,0)·(0,−1) 각 8 s(깊이는 시작값) → hover 5 s.
   - 구간 경계에서 env 의 target·u_xy 버퍼와 policy obs 의 depth_xy 채널이 스케줄과 같음을 **증명**한다.
2. 지표: 깊이 정상상태 오차(구간 마지막 3 s 의 평균 |e_z|), 정착 시간(|e_z| ≤ 0.05 m), overshoot, roll·pitch 편차(평균·최대, deg), xy 구간 |F_xy_real − F_cmd| (N, 보상과 같은 realized force), 생존율. env 축으로 mean/median/P90/max 를 내고 `summary.json` 과 `summary.md` 로 쓴다.
3. 축은 paper exam 과 같게: `--fault_fixed_health` (healthy, pair34), SEG 레벨, `--env-dr-anchor --doraemon-dr-from` (채점 체인의 DR_FROM), `--control-delay`. `depth_xy.enable` 이 없는 task 는 거부한다.
4. 스케줄 합이 에피소드 30 s 를 넘으면 명시 플래그로 연장한다. 스케줄 도중 리셋되어 명령이 다시 샘플링되지 않게 한다. Isaac 첫 리셋은 에피소드 길이를 지터하므로 자체 step 카운터를 0 부터 세고, terminated 와 truncated 를 구분한다.
5. policy forward 는 eval.py 기존 경로를 재사용한다. 두 번째 경로를 만들지 않는다.

**B. 학생 (xyz-student).** 3절의 설계를 끝까지 일관되게 적용한다.
- 모든 소비자(runner, `analysis/student_policy.py`, eval in-loop, deploy spec, `train_student.py` 검사)에 반영한다. OFF 경로는 바이트 동일, 기존 테스트는 무수정 통과여야 한다.
- 4만큼 어긋나면 실패하는 테스트를 넣는다.
- 스모크: `train_student.py --task Isaac-ConstrainedALBC-TRPO-SimToReal-DepthXY-v0 --encoder_type gru` + R3a 플래그, `--num_envs 64 --max_iterations 2 --logger tensorboard`, GPU1 락. 그 뒤 eval in-loop 경로로 몇 step 로드해 학습 쪽과 레이아웃이 같은지 본다.
- depth_xy 4입력은 배포 가능한 입력이다(압력 깊이 − 설정값, 그 적분, 운영자 명령). IMU·heave scale 을 받으면 안 된다.

## 6. 제약 (전부 실제 사고나 거부가 있었던 것)

- `/workspace/constrained-albc-r3a` 와 `/workspace/marinelab-r3a` 에는 아무것도 쓰지 않는다(`__pycache__` 포함). 읽기는 된다. 실행 중인 체인 스크립트는 제자리에서 고치지 않는다.
- auto mode 분류기 거부는 우회하지 않는다. 08:0x 에 noboth 보류 대기 스크립트(체인 래퍼와 학습 그룹 종료)가 `[Interfere With Workloads]` 로 거부됐다. 실행 중인 워크로드를 멈추는 일은 운영자에게 직접 요청한다.
- 로봇·보드 조작 금지, agent-jetson ssh 금지. `~/workspace` 에서 git 금지. commit·push 는 요청이 있을 때만(미푸시 로컬 커밋 14b5ee8, afa3c6b, 1a5981d, 51f6a05).
- DGX 는 `ssh -o BindAddress=192.168.10.17 ksm-nas`, `TERM=xterm`. `CUDA_VISIBLE_DEVICES` 금지, 한 번에 한 잡.
- 학습 런은 `/workspace/constrained-albc-r3a/logs/...` 기준이다. 체인 로그의 `run=` 은 상대경로라 `constrained-albc` 에서 찾으면 없어 보인다(2회 재발).
- GPU1 은 `/root/gpu1.lock` 으로 직렬화한다. GPU0 는 noboth 가 끝날 때까지 다른 잡을 올리지 않는다(RTX 4070 12 GB 중 8.3~11.3 GB 사용).
- 컨테이너에서 cwd=/tmp 로 python 을 띄우지 않는다(`/tmp/inspect.py` 가 stdlib 를 가림). python 은 `PYTHONDONTWRITEBYTECODE=1` 로 실행한다.
- 진행률은 분모를 산출물(`grid.json` 등)에서 읽는다. ssh 로 원격에 쓸 때는 로컬 파일을 `cat | ssh` 로 보낸다(인라인 heredoc 은 백틱이 로컬에서 평가된다).
- 응답 규칙: 한국어, KST, 이모지 금지, ROUTE 줄 필수. 우선순위를 밝힌 항목의 순서를 바꾸면 지연 시간을 같은 메시지에 적는다.

## 7. 정본 위치 (컨테이너 `/workspace/constrained-albc/` 기준)

- paper-ablation: `.hq/community/programs/paper-ablation-5000/PLAN.md` (최신 `## Update 2026-09-13 (11시 30분 KST)`)
- depth-xy: `.hq/community/programs/depth-xy-ftc-2026-09/{PLAN,HANDOFF}.md` (최신 `## Update 2026-09-13 (11시 30분 KST)`)
- 세션 로그: `.hq/community/sessions/2026-09-12-v14-night.md`
- 체인 출력: `.hq/work/paper_ablation_r3a/{train_chain_split,exam_chain_v3,grasp_chain_v1,gain_search_tdc,gain_search_pid}.out`, 게인 셀 `.hq/work/paper_ablation_r3a/gain_search/{tdc,pid}/`
- 커리큘럼 감시: DGX `/usr/bin/python3 ~/xyz_launch/watch_depthxy_dgx.py`
