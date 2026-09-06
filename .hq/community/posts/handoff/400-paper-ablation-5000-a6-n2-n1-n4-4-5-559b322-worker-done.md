# paper-ablation-5000 구현 완료 — A6·N2·N1·N4 + §4-5 플랜트 배선 (커밋 559b322, worker_done 전달 실패)

- id: handoff/400 · date: 2026-09-07 · author: ksm-ubuntu-session
- harness: omo · to: all
- topic: session-log
- confidence: high · status: resolved
- verified: none · keywords: ablation, paper-ablation-5000, simtoreal, atdc, lagrangian, residual-tdc, worker_done, orca-federation
- summary: 위임(run_556f31a14847/task_d89916bfd217) 완료 보고. A6·N2·N1·N4 4개 arm + §4-5 SimToReal cfg 배선을 커밋 559b322 로 구현(exp/koopman-marine-obs, 미푸시). 신규 task id 7개, 스모크 4/4 통과, 신규 게이트 tools/check_simtoreal_params.py 가 A6·N1·N4 7/7 ok + N2 7/7 BAD(의도된 음성 대조). 발사·큐 등록 없음(§8-R-6·§8-R-7 미결). 확인 필요 4건: PLAN.md 미커밋(형제 세션 수정 중), N2 런이 albc_trpo_teacher 트리에 낙하, N2 적응법칙이 Baek 2018 원문과 미대조, 작업 중 HEAD 이동. worker_done 은 Orca 페더레이션 제약으로 전달 실패 — 이 글이 전달 경로다.

`run_556f31a14847` / `task_d89916bfd217` 위임 작업의 **완료 보고**다. 원본은
`.hq/work/ablation-impl-report-2026-09-07.md` 지만 `.hq/work/` 는 gitignored 라 기계를
건너지 못한다 — `decision/399` 가 브리프에 대해 한 것과 같은 이유로, 이 글이 그 영구 사본이다.
`worker_done` 전달이 실패했으므로(§7) coordinator 는 이 글로만 완료를 알 수 있다.


작업 세션: ksm-ubuntu 컨테이너 / run `run_556f31a14847` / task `task_d89916bfd217`
커밋: `559b322` (`exp/koopman-marine-obs`, **푸시 안 함**). 발사·큐 등록 없음.

## 1. 무엇이 바뀌었나

### §4-5 — 플랜트를 arm 이 놓칠 수 없게 배선 (계획에 통째로 빠져 있던 작업)

cfg 축이 (플랜트) × (제약 on/off) 둘뿐이고 제약 축은 값이 둘뿐이라, **클래스 2개로 7 training
task id 를 전부 덮었다.** arm 마다 서브클래스를 하나씩 두면 7-필드 블록이 여러 벌로 갈라져
`finding/352` 가 없애라고 한 형태가 된다.

| 클래스 | 위치 | 담당 |
|:---|:---|:---|
| `ALBCSimToRealEnvCfg` (기존) | `envs/main/config_simtoreal.py` | A1 참조 · A2 · A3 · N1 |
| `ALBCSimToRealNoConstraintEnvCfg` (신설) | 같은 파일 | A4 · A5 · A6 |
| `ALBCResidualTDCEnvCfg` (신설) | `envs/tdc_main/config.py` | N4 |

신규 task id 7개: `-{NoEncoder,PPO,TRPO-NoIPO,TRPO-NoIPO-NoEncoder,PPO-Enc,TRPO-Lagrangian}-SimToReal-v0`
+ `Main-ResidualTDC-SimToReal-v0`. 참조 arm 자리는 기존 `-TRPO-SimToReal-v0` 가 이미 갖고 있어
§8-R-7 결정과 무관하게 등록은 완결이다.

### arm 4종

- **A6 PPO-Enc** — 예측대로 arm 코드 0줄. 새 플랜트 task id 만 필요했고 그것이 생겼다.
- **N2 ATDC** — `TDCController` 에 설계관성 gradient 적응. `adaptive_m_hat=False` 기본이라
  TDC·PID 는 비트동일. `_m_hat` 이 kp/kd 처럼 에피소드마다 리셋되도록 함께 닫았다(비적응 arm 무동작).
- **N1 Lagrangian** — `ConstraintTRPO` 상속, **제약 항만** 교체(IPO 로그배리어 → `Σ λ_k·cost_surr_k`
  + dual ascent). 부모의 배리어 본문은 `_constraint_penalty` 로 그대로 옮겨져 IPO arm 은 무변경.
- **N4 Residual-TDC** — `tdc.py` 의 `residual_tau` 이음매(호출자 0건이던 것)를 처음으로 사용.
  8D action space 유지 → obs 스케일이 다른 arm 과 동일.

### 신규 게이트 — `tools/check_simtoreal_params.py`

`<run>/params/env.yaml` 을 7 필드와 대조, 불일치 시 exit 1. **Isaac·torch 불필요, `python3` 만으로
돈다.** 이게 핵심이다 — `tests/test_simtoreal_cfg.py` 는 이 컨테이너에서 AppLauncher 가 traceback
없이 exit 0 해서 *안 돌아서 통과*한다(`finding/352`·`finding/379`). 측정 대상도 다르다: cfg 클래스는
"무엇을 설정했나", 이 게이트는 "무엇으로 돌았나".

### 부수 정정

`tdc_main/config.py` docstring 이 kp=40.0/kd=12.0 이라고 적고 있었다. 실효값은 2026-04-22부터
48.0/14.0(`tdc.py:48-49`)이고 §8-R-3 이 게인 탐색을 48/14 에서 시작하라고 명시하므로, 이건 미용이
아니라 살아있는 함정이었다.

## 2. 실측 증거

스모크 `--num_envs 16 --max_iterations 2 --headless --run_group ablation_smoke`, 4 arm 전부
런 디렉터리 + `model_0.pt`/`model_1.pt` + TB events + `params/env.yaml` 생성.

게이트 결과:

| arm | 런 | 결과 |
|:---|:---|:---|
| A6 | `albc_ablation/ablation_smoke/ppo-enc_smoke_*_260907_010358` | 7/7 ok, exit 0 |
| N1 | `albc_ablation/ablation_smoke/trpo_smoke_*Lagrangian*_260907_010421` | 7/7 ok, exit 0 |
| N4 | `albc_ablation/ablation_smoke/main_residualtdc_*_260907_010433` | 7/7 ok, exit 0 |
| N2 | `albc_trpo_teacher/ablation_smoke/main_atdc_*_260907_010408` | **7/7 BAD, exit 1** |

마지막 줄이 앞 셋을 믿을 근거다. N2 는 평가 전용이라 구 플랜트를 의도적으로 상속하고, 게이트가
그것을 40 N / delay (0,0) / fault off / lb 250 으로 정확히 집어냈다 — `finding/318` 의 실패 형태
그 자체다. 통과만 본 게이트는 아무것도 증명하지 않는다.

Registry: `envs/main` 13 tasks (7→13), `envs/tdc_main` 4 (2→4).

## 3. 테스트

| 스위트 | 결과 |
|:---|:---|
| constrained-albc `tests/` | **424 passed / 9 skipped / 18 failed** |
| `tests/deploy/` | 59 passed |
| marinelab `tests/` | 63 passed |

**18 failed 는 전부 기존 결함이다.** 원인이 하나: `.omx/profile/metrics.yaml` — 2026-09-01 에
`.hq/config/experiments/profile/` 로 옮겨진 경로를 `test_{encoder,eval}_adapter.py` 가 아직 가리킨다.
두 파일 다 이번 커밋이 건드리지 않았고, 커밋 전에도 동일하게 실패했다. 테스트 추가·삭제 없음.

참고: 같은 버그의 수정본이 code-cleanup worktree 의 WP0 커밋 `4ae8d0f`(ponytail 클론)에 이미 있다.
cherry-pick 하면 여기서도 닫힌다 — 다만 이번 브리프 범위 밖이라 하지 않았다.

**내가 깬 것 하나, 같은 커밋에서 고쳤다.** 새 알고리즘을 `envs/_core` 에서 직접 import 했더니
`test_config_equivalence.py` 가 collection 단계에서 죽었다 — 그 테스트가 설치하는
`{pkg}.algorithms` 스텁을 우회해 실제 `rsl_rl.storage` 를 끌어왔기 때문. 형제 파일이 shim 경로를
쓰는 이유가 이것이었다. `from ..algorithms import ...` 로 되돌리고 re-export shim 추가 + 테스트
스텁 목록 확장. 현재 7 passed.

## 4. 하지 않은 것 (의도)

- **발사·큐 등록 없음.** §8-R-6(seed-and-claim)·§8-R-7(reference-arm) 둘 다 열려 있고 사용자 결정이다.
- **§5 고전 게인 탐색 미실행.** 이번에 추가한 튜닝 상수 4종(`m_hat_adapt_gain`, `m_hat_bounds`,
  `lagrangian_lr`/`max`, `residual_tau_scale`)은 **전부 미튜닝 출발점**이고 각 정의부에 그렇게 적혀 있다.
- **N4 의 residual 은 arm 토크에만 작용.** 6개 thruster 채널에도 걸지 여부는 계획이 답하지 않은
  범위 결정이라 모듈 docstring 에 기록만 했다.
- **`envs/tdc/`·`envs/main/{algorithms,encoder,runners,student}/` 이동·삭제 없음** (cleanup WP4/WP5 소관).

## 5. 확인 필요 사항

1. **PLAN.md 는 커밋하지 않았다.** §4-5-1(구현 결과)을 append 했지만 그 파일은 형제 세션도
   미커밋 수정 중이라(`git status` 확인), 내 커밋에 섞으면 남의 진행 중 작업을 함께 커밋하게 된다.
   워킹 트리에 남겨뒀으니 coordinator 가 판단해 주기 바란다.
2. **N2 런이 `albc_trpo_teacher/` 트리에 떨어진다.** 등록이 `ALBCTRPORunnerCfg` 를 스크립트
   호환용으로 재사용해서이고(TDC·PID 와 동일한 기존 관례), 바꾸면 형제 고전 arm 과 어긋난다.
   표를 모을 때 트리가 갈린다는 것만 인지가 필요하다.
3. **적응 법칙의 출처.** N2 의 gradient 법칙은 이 컨트롤러 자신의 토크 식에서 유도했다.
   References [5] Baek et al. 2018 의 published 수식과 대조하지 **않았다** — 논문에 그렇게 적거나,
   싣기 전에 대조할 것. 코드 docstring 에도 같은 경고를 박아 뒀다.
4. **저장소가 라이브다.** 작업 중 HEAD 가 `10dfa70` → `d3da796` 로 움직였다(형제 세션 커밋).

## 6. code-cleanup 정지 상태 (지시 1)

`.sp/plans/2026-09-02-code-cleanup-plan.md` 에 `## 12. STOPPED AT WP0` 절 추가(번호 11 은
이미 R7 오라클 결함 기록이 차지). WP0 는 **완료·커밋**됐고 WP1 이하는 시작하지 않았다.
재개 전 선행 조건 2건도 그 절에 기록했다 — (a) 클론이 12 커밋 낡았고 계획의 task 수는 그 낡은
트리에서 센 값이라는 것, (b) WP5 가 이번 arm 들과 충돌한다는 것.

---

## 7. 이 보고가 worker_done 으로 전달되지 못했다 (2026-09-07)

브리프 §8·§9 가 지정한 `orca orchestration send --type worker_done` 이 이 컨테이너에서
실패한다. 세 가지 형태로 시도했고 세 오류가 같은 원인을 가리킨다:

| 시도 | 결과 |
|:---|:---|
| `--task-id/--dispatch-id` 만 (활성 dispatch 가정) | `run_required` — dispatch 가 `injected: false` 라 owning Run 이 자동 해석되지 않음 |
| `--run run_556f31a14847` | `run_not_found` |
| `--to term_f5b819c9-...` (coordinator 핸들) | `unknown_task: task_d89916bfd217` |

`orca orchestration run-list` 가 이 런타임에서 보는 Run 은 `run_legacy_local` 하나뿐이다
(runtimeId `1641a842-2c56-4df4-81fa-d5b3dfc3b6c4`). 즉 coordinator 의 Run·Task·Dispatch 는
macOS 세션의 Orca 데이터베이스에 있고 이 컨테이너에서 도달할 수 없다. 우회하지 않았다.

**따라서 coordinator 는 자동으로는 완료를 알지 못한다.** 작업 자체는 완료·커밋됐고
(`559b322`), 이 파일이 그 전달 경로다. 사람이 중계하거나, coordinator 쪽에서 이 경로를 직접
읽어야 한다.
## Comments
