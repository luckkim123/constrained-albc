# depth-xy-ftc: closed-loop depth + open-loop XY force + fault training as one teacher arm; OFF path bit-identical on the DGX; the arm and an attitude-only reference queued on the DGX

- id: finding/453 · date: 2026-09-12 · author: claude-opus5-ksm-mac
- project: albc · harness: omx · to: all
- subject: depth-xy-ftc-2026-09 · supersedes: none
- topic: debugging
- confidence: high · status: none
- verified: 2026-09-12 · keywords: depth-xy-ftc, depth control, pressure sensor, no DVL, open-loop XY, DGX, GB10 determinism, gen-2 extra obs, DORAEMON return, BindAddress
- summary: Operator 2026-09-12: add xyz like the existing controllers on a DVL-less robot, on ksm-nas, this weekend; chose z closed loop + xy open loop, vertical thruster values visible (already obs[14:20]), fault training kept, attitude-only reference on the same DGX. Task Isaac-ConstrainedALBC-TRPO-SimToReal-DepthXY-v0 (commit 51f6a05 on exp/depth-xy-ftc, anchor 3791441): gen-2 pressure/IMU channels + e_z, e_z integral, u_xy (80/29D), depth target start +- 0.5 m, xy force command u x 8 N, rewards on noise-free depth and realized body force, DORAEMON return excludes them. Sim classical baselines damp Fx/Fy/Fz with ground-truth body velocity. codex implemented, agy review 3 (1 accepted), container 492/23 same failures/12; DGX: anchor deterministic 43/43, OFF path 0 of 43 keys differ, arm runs, widths 72/28 and 80/29, section5 gate ok. Queued depthxy_dgx_arm_s30 + depthxy_dgx_ref_s30; nothing launched. ksm-nas refusals were a Mac route shadowing en1 (BindAddress 192.168.10.17).

**깊이 폐루프 + xy 개루프 추진 명령 + 고장 제어를 한 teacher arm 으로 구현하고, DGX 에서 자세만 기준선과 짝으로 돌릴 준비를 끝냈다. 발사는 사람 몫이고 아무것도 돌지 않는다.** 정본은 program `depth-xy-ftc-2026-09` PLAN(Objective·Design)과 HANDOFF.

## 1. 요청과 결정 (원문)
- 사용자 2026-09-12 04:3x: "근데 궁금한게 지금은 학습이 자세라 제어만 하는데 여기에 xyz 제어까지 추가해도 되는거 아니야? 기존 제어기들이 제어하는 방식 정도로만 하면 dvl이 없는 로봇이어도 가능할 것 같은데? 이것도 해봐줄 수 있어? 이건 병렬로 하기 위해 ksm nas에서 하자. 주말중에 전부 실험해봐야하니깐"
- 05:0x 선택: "z 폐루프 + xy 개루프" + "모델이 z축 스러스터의 값도 보면 좋을 것 같네. 아 그리고 고장 제어도 여전히 추가해주고." / 비교 기준 "DGX 에서 자세만 기준선도".
- 09-06 "병진 이동 같은 경우는 그냥 포기하자"·09-12 이동 시험 "RL 은 팔만, 스러스터는 펌웨어" 와 충돌한다 — 수조 계획은 그대로 두고 별도 학습 arm 으로 해석했다(PLAN Redefinition notice).

## 2. 확인한 사실
| 사실 | 근거 |
|:--|:--|
| xy 는 DVL 이 없어 폐루프 불가, 깊이는 압력센서로 가능 | `finding/240`; 보드 `pid.cpp:110`(깊이 PID), `keymap.h:34-37`(wasd 개루프) |
| sim 고전 비교군(TDC/PID/ATDC)은 Fx/Fy/Fz 를 sim 참값 몸체 속도로 감쇠한다 — 실기에 없는 신호 | `envs/tdc/controllers/thruster_pd.py` compute, `envs/tdc_main/tdc_env.py:165-171` |
| 수직 스러스터 값(m0·m3)은 이미 관측 `obs[14:20]` 에 있다(고장 반영 전 필터 echo) | `mdp/observations.py:42-86`, marinelab `thruster.py:114-159` |
| 깊이 센서 모델(gen-2: specific force + heave rate, 25 Hz ZOH)은 anchor 에 기본 OFF 로 병합돼 있다 | `decision/185`, 7c16b93 ⊂ anchor |
| DORAEMON 게이트는 전체 에피소드 보상 합을 lb 200 과 비교한다 | `albc_env.py:1421,1627` |
| 머신 효과: 같은 설정·시드에서 DGX roll ss_error +109 % | `finding/001:23` |
| ksm-nas 거부는 맥 라우팅(192.168.10/24 → en0 게이트웨이)이 en1 을 가린 탓 — `ssh -o BindAddress=192.168.10.17 ksm-nas` | 세션 실측 |
| GB10 학습은 결정적: anchor 스모크 2회 model_1.pt 43/43 키 동일 | 세션 실측 |

## 3. 구현 — `exp/depth-xy-ftc` @ `51f6a05` (anchor/r3a-5000 3791441 위, 로컬·미푸시)
새 task `Isaac-ConstrainedALBC-TRPO-SimToReal-DepthXY-v0`: SimToReal + gen-2(72→76) + `depth_xy`(+4 → 80, 비평 +1 → 29). 깊이 목표 = 시작 깊이 + U(−0.5, 0.5) m, xy 명령 u∈[−1,1]² × 8 N, 보상 depth 3.0(σ 0.10 m)·xy 실현 추력 2.0(σ 2 N), DORAEMON 합에서 새 항 제외(기준선 선택에서 파생), 고장 DR·제약·DR 박스 불변. flag OFF 면 폭·버퍼·보상·난수·합산 순서 불변.
- 작성: codex(ground 1, PLAN Design 원문). 검토: 세션(hold 게이트·리셋 pose 읽기·termination penalty·합산 순서) + agy(ground 4) 3건 — #1(major, 깊이 샘플이 ZOH 우회) 기각: hold 는 `compute_student_extra_obs` 첫머리 early return 이라 diff 문맥 밖이었다; #2(minor, 리셋 시드 덮어씀) 기각: publish 틱의 새 잡음 샘플이 센서 동작; #3(minor, 공유 테스트 hold=1) 수용: hold=2 테스트 추가, 사본에서 hold 를 끄면 그 테스트만 실패(음성 대조).
- 공용 `ConstraintEncoderRunner` 는 flag 를 getattr 로 읽게 세션이 고쳤다(`depth_xy` 없는 cfg 방어).
- 컨테이너 테스트(clean 워크트리 전후): anchor 475 pass / 23 fail / 12 skip → 492 pass (세션 hold=2 테스트는 이후 추가, 관련 3벌 52 pass) / 같은 23 fail / 12 skip. 관련 3벌 52 pass.

## 4. DGX 검증
DGX GB10 워크트리 `~/workspace/constrained-albc-xyz` @ `51f6a05`, marinelab @ 8cc84a5, 64 env · 2 it · seed 30 (`~/xyz_smoke/dgx_post_commit_check.sh`, 로그 `~/xyz_smoke/post_commit.log`).

| 확인 | 결과 |
|:--|:--|
| 결정성 (전제) | 수정 전 anchor 스모크 2회 `model_1.pt` 43/43 키 동일 |
| flag OFF: SimToReal task 를 새 커밋에서 | anchor 스모크와 43 키 중 차이 0 — OFF 경로 비트 동일 |
| arm task | 2 it rc 0 |
| 관측 폭 (`params/env.yaml`) | OFF 72/28, arm 80/29 |
| 발사 게이트 `tools/check_simtoreal_params.py --variant section5` | 두 런 rc 0, `velocity_limit_sim: 3.1` 한 줄 |
| 워크트리 | 검증 전후 clean |

## 5. 큐·발사
- 큐 `depthxy_dgx_arm_s30`, `depthxy_dgx_ref_s30` (pending approval, ack finding/264·352·441·444). DGX 체인 하나가 arm → ref 를 직렬로 돌린다(각 약 7.6 h, 5000 it · 4096 env · seed 30).
- 발사(사람만, DGX 에서): `EXPECT_HEAD=51f6a052fad210b52bd22b4336ecc412b5ef239b nohup bash ~/xyz_launch/launch_depthxy_dgx.sh > ~/xyz_launch/chain.out 2>&1 &` — 접속 `ssh -o BindAddress=192.168.10.17 ksm-nas`, 체인 md5 7fcd9f72, 커리큘럼 감시 `/usr/bin/python3 ~/xyz_launch/watch_depthxy_dgx.py`. 절차 전문은 HANDOFF.md.
- 남은 것: 깊이·xy 시험 도구(학습 중 작성); grasp 외란 셀(이동 시험 노트 §8-1 요청 — 큐의 grasp 체인이 1a5981d 에 핀돼 있어 별도 브랜치).
## Comments
