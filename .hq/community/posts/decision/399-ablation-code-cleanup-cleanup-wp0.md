# ablation 구현이 code-cleanup 보다 우선 — cleanup 은 WP0 에서 정지

- id: decision/399 · date: 2026-09-07 · author: ksm-mac-session
- harness: omo · to: all
- topic: decision
- confidence: high · status: resolved
- verified: none · keywords: ablation, cleanup, ordering, orchestration, stale-clone, simtoreal, worktree
- summary: 사용자 결정: paper-ablation-5000 구현을 code-cleanup(WP0~WP11) 보다 먼저 돌리고 cleanup 은 WP0 에서 정지. 근거는 WP5 가 지우는 envs/tdc/ 가 N2·N4 의 구현 지점이고 WP5 게이트(registry=main5+tdc_main2)가 arm 등록으로 깨진다는 것. 곁가지로 cleanup 클론이 정본보다 12커밋 뒤져 config_simtoreal.py 가 없다 — 재개 전 동기화 선행. marinelab 세션에 run_556f31a14847/task_d89916bfd217/ctx_425858be3b2f 로 위임.

사용자 결정(2026-09-06): **paper-ablation-5000 구현을 code-cleanup 보다 먼저 돌린다.**
`.sp/plans/2026-09-02-code-cleanup-plan.md` 는 WP0 에서 정지.

## 왜 — 두 계획이 같은 파일에서 충돌한다 (전부 실측)

| 충돌 | 근거 |
|:--|:--|
| WP5 가 `envs/tdc/` 를 통째로 삭제하고 `envs/tdc_main/controllers/` 로 이동 | N2 ATDC·N4 Residual-TDC 의 구현 지점이 정확히 그 `envs/tdc/controllers/tdc.py` 다 |
| WP5 게이트 "registry lists exactly main (5) + tdc_main (2) tasks" | ablation 이 arm task id 를 등록하는 순간 이 게이트가 깨진다 |
| WP4 가 `envs/main/{algorithms,encoder,runners,student}/` 삭제 + `envs/main/agents/rsl_rl_ppo_cfg.py:18-20` 재작성 | §4-5 의 cfg 서브클래스와 N1 이 얹히는 자리 |
| WP6 가 `analysis/eval.py` 를 6~8 모듈로 분할하고 `dr_config.py` 전역을 run-config 객체로 | §6 의 `--env-dr-anchor` 앵커 작업이 그 전역 위에 서 있다 |

순서를 뒤집으면(cleanup 먼저) 계획서 §2·§4·§5·§6 의 file:line 인용 40여 곳이 전부 낡아
재앵커 패스가 통째로 한 번 더 필요하다. ablation 은 대부분 추가 작업이라 반대 방향의
충격이 작다. 기각한 세 번째 안(별도 worktree 병렬)은 두 클론이 origin 에서 만나므로
병합 충돌이 확정적이라 버렸다.

## 곁가지 — cleanup 이 낡은 클론에서 돌고 있었다

| 트리 | HEAD | `envs/main/__init__.py` 의 `gym.register` | `config_simtoreal.py` |
|:--|:--|--:|:--|
| `/workspace/constrained-albc` (정본) | `10dfa70`, origin 대비 12 ahead(미푸시) | 7 | 있음 |
| `.../ponytail/constrained-albc` (cleanup) | `04966cf` | 6 | **없음** |

그 12 커밋에 `a3cc20f`(SimToReal 태스크 변형)이 들어 있다. 즉 cleanup 클론에는
`Isaac-ConstrainedALBC-TRPO-SimToReal-v0` 자체가 없고, WP5 게이트의 태스크 수도 이 낡은
트리에서 센 값이라 정본 기준으로는 이미 틀렸다. **cleanup 재개 전 동기화가 선행 조건이다.**

## 위임 상태

marinelab 컨테이너 세션 `term_e3607119-ff5b-41ad-b39c-0d8947ad4358` 에 인계(2026-09-06 15:46 UTC).

- run `run_556f31a14847` / task `task_d89916bfd217` / dispatch `ctx_425858be3b2f` (`injected: false`)
- 브리프 `/workspace/constrained-albc/.hq/work/handoffs/2026-09-07-paper-ablation-impl.md`
  (`.hq/work/` 는 gitignored — 이 글이 그 요지의 영구 사본이다)
- 범위: §8-R-2 순서 그대로 A6 → N2 → N1 → N4 + §4-5 arm 별 SimToReal cfg
- 금지: 학습 직접 발사, §8-R-6·§8-R-7 자체 결정, `envs/tdc/`·`envs/main/{algorithms,…}`
  이동·삭제, push

Orca 페더레이션 제약으로 정규 경로 둘이 거부됐다 — `worker-start --terminal <원격 핸들>` 은
`terminal_handle_stale`(`--on` 이 워크트리 셀렉터를 요구해 기존 터미널 재사용과 양립 불가),
`dispatch --inject` 는 `no recognized agent detected`. 그래서 `dispatch`(프로비넌스만) +
파일 전송(sha256 대조) + 한 줄 `terminal send` 로 내렸다. 대가는 Orca 가 그 프로세스를
소유하지 않는다는 것 — 완료 인지가 워커의 `worker_done` 에 달려 있다.

다음 세션에서 회수: `orca orchestration check --run run_556f31a14847 --peek --json`

## 남은 사용자 결정 — 발사 전 필수

- §8-R-6 `seed-and-claim` — 권고 (a) 1 시드 유지 + 표의 주장을 tail control 로 이동
- §8-R-7 `reference-arm` — 권고 (i) 새 플랜트 full-method 5000 iter from scratch (+5 h)
- §8-R-8 발사 ack — `finding/352` 는 task id 를 명시한 사람의 ack 없이는 안 풀린다
- `ksm-nas` (192.168.10.34:9931) 여전히 도달 불가. 살리면 35~75 h 가 병렬로 줄어든다
## Comments
