# ALBC final-teacher — 다음(마지막) DGX 런 계획 수립 브리프

당신은 constrained-albc 프로젝트의 marinelab(워크스테이션) 계획 세션이다.
산출물은 **계획**이지 실행이 아니다. 훈련 launch는 절대 자동 실행 금지 —
`omx queue-launch`로 큐만 걸고 사람 승인을 기다린다.

---

## 0. OBJECTIVE — 사용자 원문 (모든 판단의 기준선)

> "다음 실험을 dgx에서 진행할껀데, num envs나 max iter 같은 경우는 늘리기는 하되
> claude의 판단에 맡기는거야. num envs가 3만이 과하다 하면 줄여도 괜찮고, max iter도
> 마찬가지로 20,000 정도가 과하다 하면 낮춰도 괜찮아. 어쨌든 중요한건 **최고의 성능이
> 나오도록 학습**할 수 있게 하면 되고, **관련된 결합 파라미터도 파악해서 수정**하는거지.
> marinelab에 여러 실험 기록이 있으니 그걸 참고하고. **이 한번을 마지막이라고 생각하고
> 꼼꼼하게 분석 및 조사 후 계획**을 세우도록 하고, 지금 현재 완료된 dgx 실험의 결과도
> 포함해서 분석하도록 말이야."

**목적 = 최종 teacher의 성능 최대화.** 측정 가독성, 단일 변수 분리, 기존 런과의
byte-identity, 대조 가능성 — 이것들은 전부 이 목적에 **종속**된다. 그중 하나를 위해
성능을 포기하는 결정을 내렸다면, 그 트레이드는 당신이 결정할 사항이 아니라 사용자
결정 절에 올릴 항목이다.

---

## 1. 왜 이 브리프가 이렇게 쓰였는가 — 직전 런의 실패

직전 DGX 런(`trpo_dgx16k_s30_260805_185713`)은 "num_envs와 max_iterations 외에는
아무것도 바꾸지 말 것"이라는 규칙 아래 실행됐고, **11배의 연산을 쓰고 4096-env
레퍼런스와 같은 자리에 도착**했다(0.4968 대 0.5070 / 0.5067, seed 30 동일 plant).

원인은 분석 누락이 아니다. `PLAN.md §3b "Parameter coupling under scale-up"`에
결합 분석이 제대로 있었고, `step_interval` 행은 발사 전에 이미 정확히 예측했다 —
"si=250이면 iter 7748에 포화, **그 뒤 12,252 반복을 고정된 최대 난이도에서**".
실패는 그 결정이 §8 "decisions this program cannot make"에 오르지 않고 프로그램
내부에서 처리된 것이고, 그 판단 기준이 **성능이 아니라 대조 가독성**이었다는 것이다.

**따라서 이번 계획에서 결합 파라미터는 명시적으로 변경 범위 안에 있다.**
"기존 런과 비교 가능해야 하니 유지"는 이번에는 그 자체로 충분한 사유가 아니다.

---

## 2. 반드시 먼저 읽을 것

- `experiments/rsl_rl/albc_trpo_teacher/teacher_envscale_dgx/trpo_dgx16k_s30_260805_185713/analysis/diagnose-20260809-142000/report.md`
  (한국어판 `report.ko.md` 동일 디렉터리) — 직전 런 분석 정본
- `.omx/programs/dgx-final-scaleup/PLAN.md` — 특히 §3b(결합 분석 3-tier), §3(노브 표),
  §8(사용자 결정 9개). **§3b Tier 2가 이번 계획의 출발점이다.**
- `.omx/programs/dgx-final-scaleup/HANDOFF-DGX.md` §하드룰 2 — 무엇이 왜 보류됐는지의 목록
- `experiments/.../teacher_envscale_dgx/README.md`, `experiments/INDEX.md`
- `omx wiki query` 로 다음 4건 필독:
  `doraemon_curriculum_saturation_is_iteration_clocked_not_env_cloc`,
  `within_one_run_the_training_log_is_blind_to_eval_regressions_a_3`,
  `an_eval_schedule_too_sparse_to_resolve_the_curve_manufactures_a_`,
  `a_checkpoint_ranking_established_at_none_can_dissolve_at_hard_an`
- `omx wiki list --status needs-experiment` / `--status needs-apply-before-retrain`
  — 열린 lead를 계획에 싣거나 사유와 함께 명시적으로 defer할 것. 조용한 탈락 금지.

---

## 3. 확정된 사실 — 재발견하지 말 것

| 사실 | 근거 |
|:--|:--|
| DORAEMON 확장은 **iteration 클록**. env를 4배로 해도 포화가 250 반복밖에 안 밀린다(~7000 → 7250) | 직전 런 Beta 상태 실측 |
| 성능 병목은 연산이 아니라 **선언된 DR 경계**. 포화 후 예산은 고정 난이도 반복만 산다 | 직전 런 + posttam README 사전등록 가드 |
| **훈련 로그는 eval 회귀를 못 본다.** `none` 34% 악화 구간에서 reward 분해·TRPO·encoder·21개 constraint 전부 1% 미만 변동 | 직전 런 창별 TB 덤프 |
| 체크포인트 간 비교는 **`none` 레벨만** 유효. 4자리까지 재현 확인, 같은 ckpt의 `hard`는 1.2174→1.3865로 이동 | 직전 런 독립 eval 2회 |
| `none`에서 세운 순위는 `hard`·`ood`에서 **해소된다**. 배포 체크포인트 선택은 OOD에서 재검정 필요 | 직전 런 OOD 4점 |
| eval 스케줄이 성기면 **가짜 정체**를 만들고 정지 규칙을 오발시킨다 | 직전 런 4점 대 7점 |
| 단일 seed 교차 런 비교는 **cross-seed floor 56.0% p2p** 아래에서 무의미 | `seed_floor_dgx` |
| 8192 arm은 고정 box에서 **NULL** 측정 | PLAN §8 Q2 note |

**DGX GB10 실측 처리량** (계획의 wall-clock 근거로 쓸 것):

| num_envs | s/iter | 10,000 반복 | 출처 |
|---:|---:|---:|:--|
| 4,096 | 5.50 | 15.3 h | `seed_floor_dgx/trpo_dgxseed30` ckpt mtime 중앙값(구 plant, 20-dim — 현 plant는 다소 느림) |
| 16,384 | 18.06 | 50.2 h | 직전 런 실측 |
| 32,768 | 34.73 | 96.5 h | PLAN §3 기록 |

---

## 4. 반드시 다뤄야 할 결합 파라미터

각 항목에 대해 **성능 목적 기준으로** 변경/유지를 판단하고 근거를 적어라.
유지하는 경우에도 "무엇을 포기했는지"를 함께 적어라.

1. **DR 선언 경계 (`dr_config`)** — 최우선. 직전 계획에서 "실측 하드웨어 경계 대기"로
   차단됐다. **이 차단이 아직 유효한지 먼저 판정하라.** stonefish hydro 실측, buoy
   added-mass 조사, T200/XW540 벤치 등 그 사이 축적된 측정이 경계를 정할 수 있는지
   확인할 것. 여전히 막혀 있다면, 경계를 못 넓히는 상태에서 이번 런이 무엇을 살 수
   있는지 정직하게 적고 사용자 결정으로 올려라.
2. **`step_interval` (현 250)** — `max_iterations`와 진짜로 결합하는 유일한 지점.
   shape (a) 조기 포화 + 긴 고정 난이도 구간 대 (b) 후반 포화 + 단계별 dwell 3배.
   직전 계획은 (a)를 권고했고 결과는 null이었다. **이번엔 성능 기준으로 재판정하고,
   어느 쪽이든 사용자 결정 절에 올려라.**
3. **`kl_ub` (현 0.12)** — E1의 known-bad는 **4096 envs·구 plant**에서 나온 것이다.
   env를 늘리면 success 추정 잡음이 줄어 더 큰 스텝이 안전해질 수 있다. 그 전이
   가능성을 판단하라(전이 안 된다고 결론 내려도 좋으나 근거를 적을 것).
4. **`performance_lb` (현 250) / `alpha` (0.5)** — 직전엔 "다음 purpose 소관"으로
   미뤘다. 이번이 마지막이면 그 다음은 없다. 측정된 p25(E-int 255.8 / obs76fault 260.1)를
   근거로 재도출할지 판단하라.
5. **`entropy_coef_per_dim` / `min_std_per_dim` / `init_noise_std`** — A2/A3에서
   5/5 무채택. 유지가 기본이나, env 증가로 탐험이 실제로 줄어든 정황이 있다
   (반복 정렬 대조에서 sigma 7% 낮음, 자유 thruster 차원 −19~24%). 인과 미확인.
6. **`num_mini_batches` (현 4)** — 배치가 4~8배 커지면 미니배치 수도 결합 대상이다.
7. **`num_envs` / `max_iterations` 자체** — 사용자는 "늘리되 판단에 맡긴다"고 했다.
   ⚠️ 다만 증거는 반대 방향을 가리킨다: env 증가는 커리큘럼 중립이고 8192 arm은 NULL,
   4096이 3.3배 빠르게 같은 자리에 도착했다. **사용자 지시와 증거가 어긋나는 지점이므로
   당신이 조용히 결정하지 말고 사용자 결정 절에 트레이드를 명시해 올려라.**

---

## 5. 산출물 규격 — 이제 기계가 검사한다

`.omx/programs/<program-id>/PLAN.md` (omx 규칙: `.sp/plans/` 금지). 신규 program이면
`omx program-init` — omx v0.11.0부터 PLAN.md·HANDOFF.md 스켈레톤을 자동으로 깔아준다.

**작성 후 반드시 `omx program-lint --path <PLAN.md>`를 통과시켜라 (rc 0).** 이 게이트는
직전 실패를 그대로 겨냥해 v0.11.0에 추가됐고, 실패했던 그 PLAN.md에 4건을 보고한다:
`objective-missing`, `decisions-section-missing`, `tier2-unmarked`,
`predicted-outcome-missing`. 검사 항목은 아래와 같다.

- `## Objective`에 `>` 인용문(원문 그대로. 의역은 `objective-not-verbatim`으로 거부)
- `## Decisions for the user` 존재 — 제목은 이것으로 통일할 것(제목 드리프트가 연결을 끊었다)
- 모든 `[DECISION-REQUIRED: <slug>]`가 그 절에 등장(슬러그는 `step_interval`/`step-interval`
  동일 취급). **결정이 필요하다고 선언해놓고 스스로 결정하는 것이 이번 사고의 본체다.**
- Tier 2에 내용이 있는데 마커가 하나도 없으면 실패(`tier2-unmarked`)
- 결정 목록 밖에서 "결정이 필요"라고 쓴 줄에 마커가 없으면 실패(제목 줄은 예외)
- `## Predicted outcome` 존재

또한 `omx queue-launch`는 이제 **`--predicted-outcome` 필수**다. 예상이 "기존과 동등"이면
그렇게 쓰라 — 예정된 null을 말하지 않아 3일을 태운 것이 직전 런이다.

다음 절을 **반드시** 포함한다.

- `## Objective (user, verbatim)` — 위 §0 원문 그대로. 이후 모든 결정은 이 줄에 대고 논증.
- `## Parameter coupling` — 3-tier 유지(mechanical / decision required / inert).
- `## Decisions for the user` — **"decision required"로 표시한 항목은 하나도 빠짐없이
  여기 등장해야 한다.** 각 항목: 선택지 / 권고 / 권고의 근거 / 다른 선택의 예상 비용.
  이번 실패의 직접 원인이 이 연결의 부재였다.
- `## Predicted outcome` — 이 런이 낼 것으로 예상되는 결과를 한 문단으로. 예상이
  "기존과 동등"이면 그렇게 쓰고, 그럼에도 돌릴 가치가 있는지 사용자 결정으로 올려라.
- `## Eval schedule` — 직전 런의 교훈 반영. 성긴 스케줄이 가짜 정체를 만든다.
  정지 규칙을 쓸 거라면 그 규칙이 읽을 수 있을 만큼 촘촘해야 한다.
- `## Wall-clock and budget` — §3 처리량 표 기반.
- `## Deferred` — `omx wiki list --status` 두 개를 열거하고 각 lead의 처리(포함/defer+사유).

---

## 6. 하드 룰

1. **계획만.** launch 자동 실행 금지. `omx queue-launch`로 큐만.
2. **당신의 분석이 "결정이 필요하다"고 판정한 항목은 당신의 결정이 아니다.**
   사용자 결정 절에 올려라. 이것이 직전 실패의 단일 원인이다.
3. **성능이 기준선이다.** 대조 가독성·byte-identity를 위해 성능을 포기하는 선택은
   그 자체로 사용자 결정 항목이다.
4. **모든 수치는 근거를 달아라.** 이 프로젝트는 stale 판정과 역인용으로 두 번 데였다
   (`moreiters` 역인용, 감사 에이전트 stale 오판). 기억이 아니라 파일에서 읽어라.
5. **단일 seed 스크리닝의 한계를 명시하라.** 교차 런 단일 seed 비교는 56% p2p floor
   아래에서 판정 불가. 채택 결론이 필요하면 seed를 늘리는 비용을 계획에 넣어라.
6. `isaaclab/`은 pristine fork — 프로젝트 파일을 쓰거나 커밋하지 말 것.

---

## 7. 마지막 한 번이라는 뜻

사용자는 이번을 마지막으로 본다. 따라서 "다음 purpose 소관"이라는 이유의 defer는
이번엔 성립하지 않는다. 미룰 항목이 있다면 **다음이 없다는 전제에서** 그래도 미룰
가치가 있는지 논증하고, 아니면 이번 계획에 넣어라.
