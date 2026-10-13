# Program: depth-xy-ftc-2026-09

**Status: PENDING USER APPROVAL — this document authorizes NO launch.**

## Objective

Quote the requester's stated goal verbatim. Every decision below argues against
THIS line, not against a restatement of it.

> (2026-09-12 04:3x KST, 사용자) "근데 궁금한게 지금은 학습이 자세라 제어만 하는데 여기에 xyz 제어까지 추가해도 되는거 아니야? 기존 제어기들이 제어하는 방식 정도로만 하면 dvl이 없는 로봇이어도 가능할 것 같은데? 이것도 해봐줄 수 있어? 이건 병렬로 하기 위해 ksm nas에서 하자. 주말중에 전부 실험해봐야하니깐"

Operator answers to the session's scope question (2026-09-12 05:0x KST, AskUserQuestion, verbatim):

> 범위 — 선택지 "z 폐루프 + xy 개루프 (Recommended)" (제시문: 깊이는 압력 기반 관측(깊이 오차·heave rate)으로 폐루프, xy 는 wasd 처럼 추진 명령만 받아 자세 유지하며 실현(보상은 명령 추력 대비 실현 추력). DVL 없는 실기에 배포 가능) 에 대해: "추천대로 하되 모델이 z축 스러스터의 값도 보면 좋을 것 같네. 아 그리고 고장 제어도 여전히 추가해주고."

> 비교 기준 — "DGX 에서 자세만 기준선도 (Recommended)" (제시문: 같은 코드·시드로 자세만 기준선 1런 + xyz arm 1런을 DGX 에서 직렬로(약 15 h). 자세 성능 비교가 머신 효과 없이 성립)

**Redefinition notice (not an edit of an earlier objective).** Two earlier operator decisions point the other way, and this program does not overturn either of them:
- 2026-09-06: "일단 yaw는 학습이 담당하는걸로 하고, 병진 이동 같은 경우는 그냥 포기하자" (`retrain-simtoreal-2026-09/PLAN.md:347-348`), with the verticals trained dead and the depth PID's Fz injected as a randomized disturbance (`:356-363`).
- 2026-09-11/12 move test: RL holds roll/pitch 0 with the arm only; the firmware classical controllers own the thrusters (depth PID + wasd open-loop), RL thruster scale 0 (vault `10-19_Projects/11_Research/01_albc/03_notes/2026-09-11-move-test-thruster-ownership-design.md` §0, §8-1; flashed 2026-09-12 02:10).
This program adds a separate TRAINING arm in which the policy owns the thrusters for depth and commanded horizontal thrust. The tank plan above stays as it is.

Redefining the objective later in this document is a re-ask, not an edit: say so
at the point of redefinition and put it in the decision list.

## Diagnosis

What the record already establishes, with `[EVIDENCE: ...]` per claim. Read the
analysis reports and `omx wiki query` first — a plan that rediscovers a settled
fact will also re-make a settled mistake.

**Status 2026-09-12 05:2x KST: design in progress — this section holds what was verified before designing.**

- The comparison-arm env is attitude-only on purpose: 20D proprio with no linear velocity and no depth, because the robot has no DVL. [EVIDENCE: `constrained_albc/envs/main/albc_env.py:99-108,215-245` at anchor 3791441; `finding/240` "IMU + pressure ONLY. No DVL"]
- The retired 87D full-DOF deploy fed a zero placeholder where DVL linear velocity should have been. [EVIDENCE: board `robot/albc_rl/scripts/build_proprio.py:21-23` docstring]
- Sim classical baselines (TDC/PID/ATDC glue) drive Fx/Fy/Fz with a P loop on sim ground-truth body velocity against a zero target, i.e. station-keeping with a signal the robot cannot measure. [EVIDENCE: `constrained_albc/envs/tdc/controllers/thruster_pd.py` `compute()` `wrench[:, 0:3] = kp_lin * (lin_vel_cmd_body - lin_vel_body)`; `constrained_albc/envs/tdc_main/tdc_env.py:165-171` feeds `torch.zeros_like(lin_vel_b)` and `root_lin_vel_b`]
- On the board the only closed translational loop is depth: PID on the MS5837 pressure depth driving m0/m3; the setpoint moves only by keys o/l. Horizontal motion is open-loop jog (w/s/a/d, move_speed). [EVIDENCE: agent-jetson `firmware/agent/pid.cpp:110-114`; `robot/hero_agent/include/hero_agent/keymap.h:31-37,48-49`; move-test note C9, C10, C20]
- m3 is dead on the robot and m0 is the only vertical, so `(Fz, My)` is rank 1 and a depth command injects pitch moment (realised My/Fz -0.146). [EVIDENCE: `retrain-simtoreal-2026-09/PLAN.md:358-363` citing `finding/077`, `finding/154`, `finding/155`]
- A deployable depth-side sensor model already exists in the anchor lineage, default OFF: IMU specific force (3D) + pressure-derived heave rate (1D, LPF over differentiated noisy depth), zero-order held at the 25 Hz bus rate. Commit 7c16b93 (obs4 Phase A) is an ancestor of anchor/r3a-5000. [EVIDENCE: `decision/185`; `git branch -a --contains 7c16b93` lists anchor/r3a-5000]
- A teacher with those 4 channels (obs76) was trained and kept on 2026-08-04 (`trpo_obs76fault_s30_260804_043926`), but its Phase C GO/NO-GO verdict was never recorded, so it is not evidence that the channels help. [EVIDENCE: `omx campaign-status --id teacher_obs76` last note, reconstructed 2026-08-22, `do_not_cite_as`]
- Machine effect: the same config and seed on the DGX gave +109 % roll ss_error against a workstation-trained anchor, so DGX arms are compared only with DGX arms. [EVIDENCE: `finding/001:23`]
- DGX access and state: `ssh -o BindAddress=192.168.10.17 ksm-nas` (the Mac's 192.168.10/24 route via en0 refuses), GB10, idle at 04:46; Isaac Lab 2.3.0 and rsl-rl-lib 3.1.2 on both machines, torch 2.9.0+cu130 (DGX) vs 2.7.0+cu128 (container); worktrees `~/workspace/constrained-albc-xyz` @ 3791441 and `~/workspace/marinelab-xyz` @ 8cc84a5 from git bundles (neither commit is on a remote). Throughput recorded at 4096 envs: 5.4-5.5 s/iter, one job at a time. [EVIDENCE: session measurements 2026-09-12; `finding/001`; `replicate_s31` pending-launch gpu_gate]

## Design (2026-09-12 05:4x KST, session; facts: `$SC/xyz/env_facts.md` copied to `/root/xyz/env_facts.md`)

One new task, `Isaac-ConstrainedALBC-TRPO-SimToReal-DepthXY-v0` = `ALBCSimToRealEnvCfg` + one new cfg block `depth_xy` (default OFF) + gen-2 extra policy obs ON. Every new code path is behind `depth_xy.enable`; with it OFF the anchor task must stay bit-identical and consume no extra RNG (the obs4 rule, `decision/185`). Branch `exp/depth-xy-ftc` on `anchor/r3a-5000` @ 3791441, marinelab 8cc84a5 unchanged.

| part | what | why (evidence) |
|:--|:--|:--|
| depth command | target = episode-start depth + U(-0.5, 0.5) m, resampled with `_ang_cmd` every `vel_cmd_resample_steps` (250 = 5 s); in the `vel_cmd_zero_prob` (0.10) hover draw the target is the current depth and the xy command is 0 | the tank's usable band is 0.205-0.890 m (`retrain-simtoreal-2026-09/PLAN.md:128`, R-1 clamps); the board's own setpoint moves in 0.1 m key steps (`keymap.h:48-49`) |
| xy command | normalized `u_xy` in [-1, 1]^2, body-frame horizontal force command `F_cmd = u_xy * 8 N`, same resample/hover draw | open loop only, like w/s/a/d (`keymap.h:34-37`, move-test C20). 8 N = 4 x cos45 x 13 N/unit x 0.217 state, leaving the average `thruster_util` budget 0.40 room for attitude and depth (`config_simtoreal.py:47`, `config.py:126-130`, constraint #5) |
| actor obs (+4 over gen-2 76 -> 80) | `e_z = depth_meas - target` clipped to +-1 m; leaky integral of `e_z` (same leak/clamp as `_error_integral`); `u_xy` (2) | deployable from the pressure sensor (the board PID uses `desired - depth`, `pid.cpp:110`). `depth_meas` is the SAME held noisy sample as the gen-2 heave-rate channel (depth_noise_std 0.01 m, lag 0.05 s, ZOH 2 = 25 Hz, `config.py:674-691`) |
| gen-2 channels (72 -> 76) | IMU specific force (3) + pressure heave rate (1), unchanged code | already implemented and tested (`observations.py:259-323`); no DVL signal anywhere |
| vertical thruster values | unchanged: the 6D filtered thruster echo `obs[14:20]` already carries m0 and m3 (pre-fault command echo) plus 2 steps of full action history | operator: "모델이 z축 스러스터의 값도 보면 좋을 것 같네" — satisfied by the existing slot (`observations.py:42-86`, `thruster.py:114-159`); stated here so nobody adds a duplicate |
| critic obs (+1, 28 -> 29) | noise-free `e_z` | asymmetric critic, same pattern as measured lin vel (`observations.py:124-239`) |
| rewards (new, via `cfg.reward.extra_terms`) | `depth_tracking = 3.0 * exp(-e_z_true^2 / (2 * 0.10^2))`; `xy_force_tracking = 2.0 * exp(-|F_xy_real - F_cmd|^2 / (2 * 2.0^2))`, `F_xy_real` = realized body-frame horizontal thruster force after health and clamp | weights sit beside `yaw_vel` 3.5 and `att_rp` 9.0 (`rewards.py:108-113`); realized force is sim-privileged and used only in the reward |
| DORAEMON return | `_episode_return_accum` excludes the two new terms (flag `depth_xy.doraemon_return_excludes_new_terms = True`) | the gate compares the whole-episode return with `performance_lb` 200 (`albc_env.py:1421,1627`); excluding the new terms keeps the gate meaning identical to the DGX reference, which is what the operator's baseline choice buys. Cost: the curriculum does not slow down when depth or xy tracking is poor |
| faults | unchanged: `fault.enable=True`, `thruster_fail_prob=0.30`, `thruster_dead_frac=0.5`, severity DORAEMON dim | operator: "고장 제어도 여전히 추가해주고"; FTC as a distribution, never a pinned dead plant (vault memory rule; `decision/301`) |
| everything else | byte-identical to the anchor SimToReal task: DR box, DORAEMON cfg (lb 200, kl_ub 0.12, step 250), 10 IPO constraints and budgets, attitude/yaw command ranges and weights, thrust 13 N/unit, delay, episode 30 s, termination (tilt/NaN only), 4096 envs, 5000 it, seed 30 | one program-level change: the task gains depth and commanded horizontal thrust |

Implementation tasks (for the executor, in order): T1 cfg block + materializer `apply_depth_xy_obs` (requires `use_extra_policy_obs`, asserts otherwise) + privileged +1; T2 env buffers, sampling inside `_sample_velocity_command` only when enabled, reset of start depth/integral; T3 the two reward terms and the DORAEMON return exclusion; T4 `config_simtoreal_depthxy.py` + task registration; T5 tests — OFF path: dims 72/28 and no RNG consumed (seeded tensors equal to anchor); ON path: dims 80/29, sampler ranges and hover draw, reward maxima at zero error, return exclusion, gen-2 required; AST pin of the new task. Eval tooling for depth/xy exams is built while the runs train (not needed to launch).

## Parameter coupling

### Tier 1 — follows mechanically; nothing to set

- `observation_space` 72 -> 76 (gen-2) -> 80 (depth_xy) and `state_space` 28 -> 29 follow from the flags; `policy_obs_dim`/`privileged_dim` follow through `sync_policy_obs_dim`/`sync_privileged_dim` (`_core/runners/__init__.py:13-52`). [DERIVED]
- The new commands reuse `vel_cmd_resample_steps` 250 and `vel_cmd_zero_prob` 0.10. [DERIVED]

### Tier 2 — real coupling; a decision is required

| knob | current | options | coupling | marker |
|:--|:--|:--|:--|:--|
| `doraemon.performance_lb` meaning | whole return vs 200 | (a) exclude new terms (chosen) / (b) include and re-tune lb | the curriculum gate (`finding/315` stalled when the return scale moved) | `[DECISION-REQUIRED: doraemon-return]` |

### Tier 3 — no coupling to the variables under test; leave byte-identical

`fault.thruster_fail_prob` 0.30, `fault.thruster_dead_frac` 0.5, `thrust_coefficient` 13, DR box, `doraemon.kl_ub` 0.12, `doraemon.step_interval` 250, constraint budgets, `att_cmd_rp_range`, `yaw_rate_cmd_range`, reward weights `att_rp.k` 9.0 / `yaw_vel.k` 3.5 / `k_thr` -0.35, `episode_length_s` 30.

## Decisions for the user

- `[DECISION-REQUIRED: doraemon-return]` **Does the curriculum gate count the new depth/xy reward?** Resolved as (a) exclude, derived from the operator's 05:0x choice "DGX 에서 자세만 기준선도": the reference and the arm then pace their curricula on the same return. (b) would need a new lb and makes the two curricula incomparable. Reopen only if the arm's depth tracking collapses at hard while the curriculum widens.
- Operator decisions already taken (05:0x): scope z closed loop + xy open loop; vertical thruster values in the observation (already present); fault training kept; attitude-only reference on the same DGX.

## Predicted outcome

- Reference (DGX, flags OFF, anchor task): curriculum health like the p3b canary (DORAEMON mode 0 by it 1000, no stall signature); its attitude numbers differ from the workstation `r3a5000_ref_full_s30` by the machine effect (`finding/001:23`) — that difference is NOT a result of this program.
- Depth-xy arm: depth hold within about 0.05 m at none/soft; worse at hard, where buoyancy DR (volume and mass each 0.75-1.25, independent) can exceed the vertical authority of 2 x 13 N, and a dead vertical halves it; attitude error at hover within the single-realization noise floor of the DGX reference at none, with a measurable cost while horizontal thrust is commanded (the thrusters are shared and `k_thr` -0.35 penalizes the extra thrust); realized horizontal force tracks the command at none/soft.
- Honest null risks: the thruster-energy penalty and the `thruster_util` budget may push the policy to under-realize the xy command; the curriculum can stall if the extra thruster use lowers the attitude return below lb 200.

## Eval schedule

- Curriculum health from TB scalars every 500 it on both runs (DORAEMON mode, fault_severity; stall signature = mode <= -2 three reads in a row and severity < 0.05), by a DGX watcher that only reads.
- Exams at model_2500 and model_5000: the paper-ablation static exam (attitude, the same tooling and box as the workstation arms) on both runs, plus a depth/xy exam on the arm (depth steps +-0.3 m, hover, xy force steps at attitude 0; depth ss error, settling, attitude deviation, force tracking; mean/median/P90/max) — tool built during training, run on GPU1 or the DGX.

## Wall-clock and budget

- Implementation + tests + two-family review: about 4 h (estimate). DGX smoke of both tasks: about 15 min.
- DGX runs, serial (one job at a time on the GB10): arm then reference, 5000 it x about 5.5 s/iter at 4096 envs = about 7.6 h each (`replicate_s31` gpu_gate, `finding/001`) -> about 15 h. Exams about 1 h.
- Workstation GPU0 is not used (the 10-run paper chain holds it for about 48 h).

## Deferred

Enumerated 2026-09-12 05:3x from `omx wiki list` (4 needs-apply-before-retrain, 42 needs-experiment).
- Carried as launch acks (same as the anchor chain): `finding/264`, `finding/352`, `finding/441`, `finding/444`.
- Relevant, deferred with reason: `decision/301` (real actuator set) — covered as a fault distribution, not a pinned plant; `decision/408` (p5 delta: verticals pinned + depth-PID Fz disturbance) — not applied, this program anchors R3a (pre-p5) so the reference stays comparable to the paper arms; `finding/305`, `finding/309`, `finding/312` (vertical TAM, coefficient, per-thruster nominal) — held at anchor values; `finding/313`, `finding/315` (lb history) — lb 200 held, gate excludes the new terms; `finding/355`, `finding/391` (exam thrust band tooling) — exam-side, the paper exam runs as-is; `finding/363` (fault x delay additivity) — read by the paper exam's pair cells; `finding/386` (student horizon) — students are out of scope; `finding/296` (Arm W DR decomposition) — unrelated.
- Not touched by adding depth/xy to a teacher, deferred: `finding/163`, `finding/198`, `decision/263`, `finding/318`, `debugging/319`, `finding/321`, `finding/362`, `finding/378`, `finding/379`, `finding/380`, `finding/382`, `finding/383`, `finding/384`, `finding/385`, `finding/387`, `finding/389`, `decision/390`, `finding/395`, `finding/396`, `finding/397`, `finding/401`, `finding/402`, `finding/404`, `finding/405`, `finding/407`, `finding/410`, `finding/438`, `finding/439`, `finding/442`, `finding/445`.

## Validation and queue (2026-09-12 06:0x KST)

- Implementation: codex (ground 1) from the Design section; commit `51f6a052fad210b52bd22b4336ecc412b5ef239b` on `exp/depth-xy-ftc` (container `/workspace/constrained-albc-xyz`, local, not pushed), moved to the DGX by git bundle (md5 5b519245).
- Review: session — the hold is the early return at the top of `compute_student_extra_obs`, so e_z uses the same 25 Hz sample; the reset-pose read is valid because `write_root_link_pose_to_sim` writes `root_link_pose_w` at once; the termination penalty and the OFF-path reward summation are unchanged; the shared runner reads the flag through getattr. agy (ground 4), 3 findings: #1 major (depth sample bypasses the hold) rejected, the hold sits outside the diff context; #2 minor (reset seed overwritten by a noisy sample) rejected, that is the sensor; #3 minor (sharing test used hold=1) accepted, a hold=2 test added, and a copy with the hold disabled fails only that test.
- Container tests (Isaac python, clean worktree): anchor 475 pass / 23 fail / 12 skip -> 492 / the same 23 / 12; the three depth-xy test files 52 pass after the hold=2 test.
- DGX (GB10, 64 envs, 2 it, seed 30): two unmodified anchor smokes 43/43 keys equal (deterministic); SimToReal from 51f6a05 vs anchor 43 keys, 0 differ (OFF path bit-identical); depth-xy task 2 it rc 0; widths 72/28 and 80/29; section5 gate rc 0 on both; velocity_limit_sim 3.1 once; tree clean.
- Queue (pending approval, nothing launched): `depthxy_dgx_arm_s30`, `depthxy_dgx_ref_s30`, acks finding/264, 352, 441, 444; one DGX chain `~/xyz_launch/launch_depthxy_dgx.sh` (md5 7fcd9f72) runs the arm then the reference. Launch and steps: HANDOFF.md.
- Not built yet: the depth/xy exam tool (Eval schedule), to be written while the runs train.

## Update 2026-09-12 (23시 KST) — 체인 순서 복구, depth-xy 를 2번째로

운영자 지적: **"depth xy가 맨 마지막이네. 이걸 좀 빨리 해달라 한걸로 기억나는데"** (23:0x KST). 맞는 지적이다.

Objective 절의 원문이 "이건 **병렬로 하기 위해** ksm nas에서 하자" 이고, 05:0x 승인 편성은
"자세만 기준선 1런 + xyz arm 1런을 DGX 에서 직렬로(약 15 h)" 였다. 14:4x 분할에서 세션이
그 사이에 n1_lagrangian·n4_residual 을 끼워 depth-xy 를 4번째로 밀었고, 그 변경을 보고에 적지 않았다.
경위와 규칙은 finding/456.

### 복구

- 새 체인 `~/xyz_launch/launch_paper_dgx_b.sh` (md5 c65f57c4): `ref → depthxy → n1_lagrangian → n4_residual`.
  `run_arm` 이 `.chain_ok` 를 보고 `SKIP` 하므로 끝난 ref 는 재실행되지 않는다.
- 23:08:11 발사 → `SKIP ref` → `START depthxy` → `GATE ok depthxy` 23:08:21
  (`logs/rsl_rl/albc_trpo_teacher/depth_xy_ftc_dgx/trpo_dgx_depthxy_260912_230816`), GPU 10793 MiB.
- 비용: n1 약 350/5000 (약 40 분) 폐기. 부분 런 `trpo_dgx_n1_lagrangian_260912_223520` 은 남겨 두었다
  (`.chain_ok` 없음 → 새 디렉터리로 재실행).

### 일정

depth-xy 일요일 07시경 완료 (승인 편성의 06:20 과 사실상 같은 자리). 이어서 n1 15시경, n4 22시 30분경.

### 감시 기준 (finding: 학습 런은 500~1000 iter 마다 커리큘럼 건강을 본다)

`watch_depthxy_dgx.py` 기준 그대로 — 정지 서명은 `DORAEMON/mode ≤ −2` 가 3연속이고 `fault_severity < 0.05`.
depth 항은 `doraemon_return_excludes_new_terms=True` 라 DORAEMON 성공 판정에 안 들어간다.

## Update 2026-09-13 (07시 KST) — depth-xy arm 완주, 커리큘럼 건강

- `END depthxy rc=0 ok=1` 2026-09-13 06:56:37 KST. START 23:08:11 부터 7 h 48 m (평균 5.62 s/iter, 마지막 iteration 5.52 s). 23시 절의 "07시경" 예상과 맞다.
- 산출: `~/workspace/constrained-albc-xyz/logs/rsl_rl/albc_trpo_teacher/depth_xy_ftc_dgx/trpo_dgx_depthxy_260912_230816/` 에 `model_4999.pt` 와 `.chain_ok`.

### 커리큘럼 (`/usr/bin/python3 ~/xyz_launch/watch_depthxy_dgx.py`, 06:59 KST)

| it | DORAEMON/mode | fault_severity |
|--:|--:|--:|
| 500 | −2 | 0.0094 |
| 1000 | 0 | 0.0142 |
| 1500 | 0 | 0.0187 |
| 2000 | 0 | 0.0246 |
| 2500 | 0 | 0.0325 |
| 3000 | 0 | 0.0430 |
| 3500 | 0 | 0.0570 |
| 4000 | 0 | 0.0758 |
| 4500 | 0 | 0.1011 |

정지 서명(mode ≤ −2 3연속 + severity < 0.05)은 없다. 최종 `Train/mean_reward` 244.8.
이 reward 는 arm 비교에 쓰지 않는다 — 이 arm 은 기준선에 없는 보상 항을 갖고, 비교는 같은 시험 분포에서 잰 채점으로만 한다.
감시 도구 출력에 같은 블록이 두 번 나오는 것은 `depth_xy_ftc_dgx/latest` 심링크 때문이고 런은 하나다.

### 남은 것

- 깊이·xy 시험 도구는 아직 없다. 그래서 이 arm 의 결과(깊이 추종·자세 유지)를 기준선과 비교한 수치는 아직 없다. **정정 (09-13 07시 후반):** 07시에 이 줄에 "착수는 운영자 확인 뒤" 라고 적었으나 틀렸다 — `## Eval schedule` 과 HANDOFF 5단계가 이 도구를 학습 중에 만들고 model_2500·model_5000 에서 돌리도록 이미 정했다. 미작성은 세션 누락이다. 자세 시험(paper static exam)도 DGX 두 런에는 걸려 있지 않다 — `exam_chain_r3a.sh` 의 ARMS 는 워크스테이션 `r3a_*` 만 담는다.
- 학생 모델: `## Deferred` 가 `finding/386` 을 들어 "students are out of scope" 로 뺐다. 운영자 결정이 아니라 세션이 줄인 범위다. 기존 학생 경로도 그대로는 안 맞는다 — depth-xy 관측 4개가 gen-2 채널 뒤에 붙고(`albc_env.py:1297,1302`), `extra_obs_from_policy_tail` 은 마지막 4차원을 IMU·heave 로 자른다(`_core/student/config.py:76`). 09-13 운영자에게 범위 확인 요청.
- DGX 체인은 같은 초에 `START n1_lagrangian`, `GATE ok` 06:56:47 (`logs/rsl_rl/albc_ablation/paper_ablation_r3a_dgx/trpo_dgx_n1_lagrangian_260913_065642`). 이어서 n4_residual. 예상은 23시 절 그대로 n1 15시경 · n4 22시 30분경이고, n1 속도는 첫 체크포인트들에서 다시 잰다.

## Update 2026-09-13 (11시 30분 KST) — 시험·학생 범위 확정, 작업 중단 상태, 세션 교대

- 운영자 답 (07:4x AskUserQuestion): **"시험과 학생 둘 다 (Recommended)"** — 깊이·xy 시험 도구, DGX 두 런 자세 시험, 학생 경로 수정·증류·학생 시험을 이번 주말 범위에 넣는다. 보드 배포(스러스터 소유권 변경)는 별도 결정. `## Deferred` 의 "students are out of scope" 는 이 답으로 대체된다.
- 운영자 (07:5x): **"xy를 먼저 테스트할 수 있게 하라고 이거 내가 몇번째 말한건지도 모르겠네"** — 이 프로그램의 시험이 두 프로그램 전체의 자원 배분 1순위다. GPU0 에서 noboth 를 보류하려던 대기 스크립트는 auto mode 분류기가 거부했고(`[Interfere With Workloads]`), noboth 는 09:41 에 시작해 13:05경 끝난다. GPU1 은 11:23 기준 비어 있다.
- 작업 상태 (API 인증 403 으로 executor 2개 중단, 보고서 없음, AST 파싱만 통과):
  - `/workspace/xyz-exam` (`exp/depth-xy-exam` @51f6a05, 미커밋): `eval.py` +248 (`depthxy` 서브커맨드), `_eval_dr/depthxy.py` 173줄, `tests/test_eval_depthxy.py` 94줄. 스모크·테스트 미실행.
  - `/workspace/xyz-student` (`exp/depth-xy-student` @51f6a05, 미커밋): 6 파일 +67/−9 + 테스트 136줄. `policy_tail_after(env_cfg)` 를 env 에서 유도하고 체크포인트에 기록한다. 테스트·스모크·`train_student.py` 검사·deploy spec 미완.
- DGX 체크포인트 사본 (컨테이너 `constrained-albc-xyz/logs/rsl_rl/albc_trpo_teacher/`, md5 일치): arm `depth_xy_ftc_dgx/trpo_dgx_depthxy_260912_230816` model_2500 628ba757·model_4999 2843fd7c, 기준선 `paper_ablation_r3a_dgx/trpo_dgx_ref_260912_144855` model_2500 08484ef5·model_4999 8a820d41.
- 다음 순서와 명세 요지는 `.hq/community/sessions/2026-09-13-resume-brief.md` 4·5절.

## Update 2026-09-13 (12시 KST) — 깊이·xy 시험: arm 은 깊이를 잡지 못한다

- 시험 도구 `/workspace/xyz-exam` (@51f6a05 + 미커밋 `eval.py depthxy`, `_eval_dr/depthxy.py`, 테스트): 세션 리뷰에서 명령 덮어쓰기(`albc_env.py:786-791,890-896,1886-1899`)·obs 꼬리(`observations.py:89-98`)·보상 힘(`rewards.py:215-220`) 정합 확인. sim-free 테스트 3/3, 전체 스위트 실패 23건은 편집 전후 같은 목록. 세션 수정 2줄: 출력 폴더 기본값에 체크포인트 이름(`eval.py:2740` — 없으면 model_2500·4999 가 같은 폴더를 덮어씀), meta 에 실제 import 된 `constrained_albc` 경로.
- 스모크 (model_4999, 16 envs, none, healthy) 11:52 valid: 명령 덮어쓰기 증명 편차 4항 모두 0.0, 생존 16/16, truncated 0, import `/workspace/xyz-exam` + `/workspace/marinelab-r3a` (8cc84a5 — DGX 학습 짝, HANDOFF 2단계).
- 본 그리드 `xyz-exam/outputs/depthxy_exam/run_depthxy_exam.sh` (md5 810786d5): model_4999·2500 × healthy·pair34 × none~hard, 64 envs, seed 42, `--env-dr-anchor --doraemon-dr-from` = paper exam 의 p3b DR_FROM, GPU1 락 1회 점유.
- 결과 model_4999 healthy (`outputs/depthxy_exam/m4999_healthy/summary.md`, 11:57):

| level | survival | 깊이 정착 비율 (±0.05 m) | final hover e_z ss mean / P90 (m) | xy 구간 F err mean (N, 명령 8 N) | xy 구간 roll·pitch mean (deg) |
|:--|--:|--:|--:|--:|--:|
| none | 1.000 | 0 % | 24.6 / 39.8 | 2.73~3.06 | 0.22~0.67 |
| soft | 1.000 | 0 % | 32.2 / 51.6 | 2.17~2.55 | 0.37~0.59 |
| medium | 1.000 | 0 % | 40.3 / 64.8 | 2.23~2.40 | 0.59~0.83 |
| hard | 0.922 | 2 % (+0.3 구간만) | 54.6 / 97.8 | 2.43~2.69 | 1.3~3.5 |

- 깊이 오차는 구간과 무관하게 시간에 비례해 커진다 — heave 를 제어하지 않는 정책. 평가 설정 문제가 아니라는 독립 근거는 학습 TB: `Reward/depth_tracking` it4999 0.0655 / 최대 3.0 = **2.2 %**, `Reward/xy_force_tracking` 1.08 / 2.0 = **54 %** (기록 = Σ 값×가중치×dt ÷ 30 s, `rewards.py:278,284`, `albc_env.py:1504`; `Term/terminated` 0). `## Predicted outcome` 의 "depth hold within about 0.05 m at none/soft" 는 **틀렸다. 원인 미규명.** 첫 hover 구간 roll·pitch max 34~43° 는 리셋 직후 과도.
- 3단계 자세 시험 (DGX arm·기준선, model_4999 → 2500, CORE 4셀): 채점 트리 `/workspace/xyz-static` = afa3c6b(채점 체인의 트리) + `git show 51f6a05` 미커밋 적용 (patch md5 fa59abf5, 51f6a05 는 envs/tests 만 바꿔 두 런 모두 학습 env 코드로 채점). `outputs/dgx_static_exam/run_dgx_static_exam.sh` md5 238c5296, 11:59 발사, 그리드 뒤 GPU1 락을 16셀 끝까지 점유 (약 14:55 종료 추정).
- 학생: 직전 에이전트의 스모크(2 it 학습 08:33, in-loop static eval 08:48)가 현재 편집(08:25)으로 통과했음 — 브리프의 "미실행" 은 403 으로 보고가 빠진 것. 학생 테스트 55/55. R3a 실제 레시피는 `num_envs 2048` (`g0c_runner/student_arm.sh.bak-260906:59`; 브리프의 4096 은 오기). 증류는 teacher 가 깊이를 못 잡는 전제라 운영자 결정 대기.

## Update 2026-09-13 (12시 20분 KST) — 운영자 결정 2건, 깊이 실패 CPU 진단

- 운영자 답 (12:1x AskUserQuestion): 학생 증류 **"증류 보류"** (13:05 GPU0 발사 안 함), 원인 진단 **"CPU 진단 지금"**.
- 그리드 진행: m4999_healthy 11:57 · m4999_pair34 12:03 둘 다 valid. 결과 표는 m2500 셀 완료 뒤 이 PLAN 에 추가.
- CPU 프로브 (GPU 미사용): 체크포인트 가중치를 rsl_rl `MLP`·`EmpiricalNormalization`·`nn.LayerNorm` 에 싣고 `_core/encoder/actor_critic_encoder.py:216-219,259` 순서대로 forward. 동작점 = actor 정규화기 평균 + 특권 obs 경계 중점. 입력 하나를 쓸어 선형 기울기를 추력 N 으로 환산 (13 N/unit; `params/env.yaml:306-341` 할당 행렬 Fz = t0+t3, My ∝ t0−t3, Fx = 0.707(t1−t2−t4+t5), Fy = 0.707(t1+t2−t4−t5)).

| 입력 → 출력 | model_4999 | model_2500 |
|:--|--:|--:|
| u_x → Fx (양성 대조) | +7.75 N/unit | +7.53 |
| u_y → Fy (양성 대조) | +7.77 N/unit | +7.41 |
| pitch → t0−t3 (수직 스러스터 사용 대조) | −7.2 N/rad | −12.9 |
| e_z → Fz | −2.56 N/m | −1.28 |
| e_z 적분 → Fz | −0.69 N/unit | +0.97 |
| heave rate → Fz | +3.61 N/(m/s) | +1.33 |

- 판독: xy 채널은 명령 스케일대로 쓰고, 깊이 위치 되먹임은 1 m 에 1.3~2.6 N 으로 학습 DR payload 평균 1.5 kg(약 15 N) 부력 불균형을 이길 수 없다. 수직 두 개는 피치 제어에 쓰인다.
- 정규화기 평균 (학습 중 분포): e_z +0.79 m (클립 1.0), 적분 +1.47 (model_2500 시점 +0.90 · +1.66) → 학습 내내 목표보다 약 0.8 m 이상 깊었다. **가설**: σ 0.10 m 깊이 보상 안에 거의 들어가지 못해 기울기가 없었고, 가라앉는 플랜트(payload DR)가 그 상태를 유지시켰다. 몸체 +z 가 위라는 좌표 가정이면 e_z 기울기 부호도 반대 — **미검증**.
- 이 판독은 `## Predicted outcome` 과 `## Decisions for the user` 의 doraemon-return (a) 선택("Reopen only if the arm's depth tracking collapses") 재개 조건에 해당한다. 재설계(보상 폭, DORAEMON 합 포함, payload 부력 대응, 깊이 오프셋 커리큘럼)는 운영자 결정이며 이 절은 아무것도 결정하지 않는다.

## Update 2026-09-13 (12시 15분 KST) — 운영자 결정: depth-xy 포기

- 운영자 원문 (12:1x, 12시 20분 절 CPU 진단 보고 직후): **"그러면 그냥 detph xy는 포기하자. 그 외의 것들이나 진행해줘."**
- 이 프로그램에 남은 작업은 없다. 학생 증류(12시 20분 절에서 보류)는 취소. DGX 두 런 자세 시험 배치(`/workspace/xyz-static/outputs/dgx_static_exam/run_dgx_static_exam.sh`)는 GPU1 락을 기다리던 상태에서 12:11:30 `stopped by signal` 로 취소 — 한 셀도 돌지 않았다. 깊이·xy 그리드 마지막 셀(m2500_pair34)만 12:14경 끝나도록 두었다(기록 완결).
- 재설계는 하지 않는다. 12시 20분 절의 판독(깊이 위치 되먹임 1.3~2.6 N/m, 학습 중 e_z 평균 +0.79 m, σ 0.10 m 보상 폭 가설, e_z 기울기 부호 미검증)은 누가 이 과제를 다시 열 때의 출발점으로만 남긴다.
- 남는 산출물 (지우지 않음): `/workspace/xyz-exam` (시험 도구 미커밋 편집 + `outputs/depthxy_exam/`), `/workspace/xyz-student` (학생 80D 경로 미커밋 편집 + 스모크 산출물), `/workspace/xyz-static` (afa3c6b + 51f6a05 diff 미커밋 워크트리), DGX 체크포인트 사본 `/workspace/constrained-albc-xyz/logs/rsl_rl/albc_trpo_teacher/{depth_xy_ftc_dgx,paper_ablation_r3a_dgx}/`.
