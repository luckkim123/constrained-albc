# constrained-albc 진단 리포트

> 작성: 2026-05-25. 6개 영역(env/physics, algorithm, encoder/runners/student, TDC, analysis, structure)을
> 읽기 전용 에이전트로 병렬 진단 후, **CRITICAL 항목은 코드로 직접 재검증**했다.
> 각 항목에 검증 상태를 표기한다: `[검증됨]` = 코드/데이터로 확인, `[미검증]` = 에이전트 보고이나 직접 확인 안 함,
> `[기각]` = 검증 결과 사실이 아님.
>
> **이 리포트는 진단만 담는다. 수정은 항목별 승인 후 별도 진행한다.**

---

## 0. 요약 — 옥석 가리기

진단 에이전트가 올린 "CRITICAL" 2건은 **직접 검증 결과 모두 과잉판정으로 기각**했다.
이는 `03-analysis-quality.md`(근거 없는 주장 금지)와 `feedback_no_baseless_claims`가 경계하는 패턴이라
리포트 전반에서 검증 상태를 명시한다.

| 영역 | 실제 CRITICAL | HIGH | MEDIUM | 비고 |
|:---|:---:|:---:|:---:|:---|
| env / physics | 0 | 1 | 4 | 에이전트 CRITICAL 2건 → 기각/다운그레이드 |
| algorithm | 0 | 1 | 3 | 에이전트 CRITICAL 1건 → 기각 (표준화 전제 무시) |
| encoder/runner/student | 0 | 0 | 2 | 구조 양호, 중복만 존재 |
| TDC | 0 | 0 | 2 | 제어 수학 정확, C++ 후보 1건 |
| analysis | 0 | 1 | 3 | eval_dr.py 4041줄 분해가 최대 기회 |
| structure | 0 | 2 | 4 | config 중복 + 테스트 부재가 핵심 |

**가장 높은 ROI 세 가지** (상세는 §7):
1. `analysis/eval_dr.py` (4041줄) 모듈 분해 + 공통 metric/plotting 라이브러리화
2. config 9개 클래스의 base-template 리팩토링 (중복 25~40%)
3. 환경/config/runner 스모크 테스트 추가 (현재 테스트는 TDC 1개뿐)

---

## 1. 기각·다운그레이드된 항목 (먼저 정리)

### [기각] constraints.py:88 — attitude cost `torch.max`는 버그 아님
에이전트는 CRITICAL로 분류했으나, `torch.max(a, b)`는 인자가 **두 텐서**이면 element-wise maximum이
PyTorch 표준 동작이다 (reduction은 단일 텐서일 때만). `(roll.abs(), pitch.abs())` 두 (N,) 텐서가 들어가므로
per-env max가 정확히 계산된다. "우연히 맞다"가 아니라 **명세상 맞다**.
→ 실제 등급: **LOW (가독성)**. `torch.maximum`으로 바꾸면 의도가 더 명확해지는 nit일 뿐.

### [기각] constraint_trpo.py:462 — cost surrogate `1/(1-γ)` 스케일이 margin을 폭주시킨다
에이전트는 "100× 부풀려 log(margin) 폭발 → CRITICAL"이라 했으나 **전제가 코드와 모순**된다.
`constraint_trpo.py:437-438`에서 `cost_advantages_flat`는 surrogate 진입 **전에 per-constraint std 표준화**된다
(mean≈0, std≈1). 462행은 그 표준화된 advantage에 ratio를 곱해 평균낸다. on-policy 시작점 ratio≈1이므로
`cost_surrs ≈ mean(정규화 advantage) ≈ 0`. 따라서 `100 × ≈0 ≈ 0`이지 "100×50"이 아니다.
에이전트는 표준화를 무시하고 advantage를 O(1)로 가정했다.
→ **margin 폭주 주장은 기각.** 단, `1/(1-γ)` 스케일이 NORBC 수식과 정확히 일치하는지는 논문 대조가 필요한데
`references/NORBC`에 Python 구현이 없어 **현 시점 단정 불가** (아래 §3-A1에서 별도 표기).

---

## 2. env / physics (`albc_env.py`, `mdp/`)

### [미검증·HIGH] 쿼터니언 정규화 gradient 비안전 — `albc_env.py:847`
`_quat_align_z_to()`에서 `axis / axis_norm.clamp(min=eps)`가 양 분기 모두 평가돼 `axis_norm`이 작을 때
gradient가 폭주할 수 있다. 단, 이 함수는 payload **시각화 마커** 용도라 학습 gradient 경로에 실제로
포함되는지 확인 필요. `torch.nn.functional.normalize` 또는 분모에 `+eps`로 안전화 권장.
→ 학습에 영향 없으면 LOW로 강등. **수정 전 호출 경로 확인 필수.**

### [미검증·MEDIUM] added-mass 안정성 clamp가 DR된 inertia 사용 — `events.py:267`
post-DR clamp가 `hydro.rigid_body_inertia`(이미 `inertia_scale` 적용됨)를 기준으로 `M_a < 0.95*I`를
검사한다. PhysX 실제 inertia는 `inertia_scale`로 randomize되지 않으면 둘이 어긋나 forward-Euler 발산 위험.
메모리(`added mass stability: init validation + post-DR per-axis clamp 0.95*I`)와 연결됨.
→ **물리적으로 가장 점검 가치 높은 항목.** base inertia 기준으로 clamp하거나 PhysX inertia도 같이 scale.

### [검증됨·MEDIUM] obs 차원 silent mismatch — `albc_env.py:883`
`use_integral_obs`/`integral_dims`에 따라 obs가 87↔84↔81로 바뀌는데 런타임 assert 없음.
메모리도 "docstring 81D vs observation_space=87 authoritative"로 과거 혼란 기록.
→ `_get_observations()` 끝에 `assert policy_obs.shape[-1] == cfg.observation_space` 추가. 저비용 고효율.

### [검증됨·MEDIUM] hot-loop 텐서 재생성 — `albc_env.py:940`
`torch.tensor(sigmas, device=...)`를 매 step 생성. `__init__`에서 1회 할당하면 됨. 4096 env에서 소폭 이득.

### [미검증·MEDIUM] ocean current OU가 max_velocity를 5% 초과 — `config.py:312`, `albc_env.py:674`
`clamp_bound = max_vel * 1.05`로 명세(`max_velocity=(0.5,...)`)를 5% 위반. encoder 입력 분포에
영향 가능. 의도면 주석화, 아니면 정확 clamp.

### [미검증·LOW] in-place 누적오차 (`_error_integral.mul_`, `:913`), yaw wrap edge(`:501`), manipulability 정규화(`:489`), control decimation 미문서화(`:457`), euler 캐시 매 step(`:1150`) — 모두 정확성 영향 적음, 정리 단계에서 일괄.

---

## 3. algorithm (`constraint_trpo.py`, `doraemon.py`, `constraints.py`)

### [검증됨] TRPO/IPO 핵심 수학 — 정확
직접 읽어 확인: gaussian KL(`:329`), Fisher-vector product 이중 backprop(`:354`), CG+damping(`:367`),
step size `sqrt(2δ/sHs)`, line search가 surrogate 개선 **AND** KL≤δ 동시 검사(`:406`),
IPO adaptive threshold `max(d_k, J+α·d_k)`(`:308`), per-constraint cost adv 표준화(`:437`). **표준 구현과 일치.**

### A1. [미검증·HIGH] cost surrogate `1/(1-γ)` 스케일의 수식 정합성 — `:462`
margin 폭주는 §1에서 기각했으나, **이 스케일이 NORBC 정의와 맞는지**는 미확정.
일반적으로 `1/(1-γ)`는 (a) budget→threshold 초기화 변환에 쓰거나 (b) undiscounted cost를 discounted로
변환할 때 쓴다. 여기선 이미 GAE로 discounted된 cost advantage에 다시 곱하므로 **이중 적용 의심**이 있다.
단 advantage가 정규화돼 있어 실효는 "barrier gradient의 스케일 상수"로 흡수됨 (barrier_t=100과 상쇄 가능).
→ **논문 대조 또는 저자(유저) 확인 필요.** 단독으로는 무죄/유죄 판정 보류.

### B. [검증됨·HIGH] barrier log clamp floor 1e-8 — `:464`
`margin.clamp(min=1e-8)` 후 log. margin이 음수로 내려가면(제약 위반) log(1e-8)=-18.4가 되고 gradient는
~1e8로 폭주. 현 하이퍼파라미터에선 드물지만 outlier cost 1건으로 트리거 가능. floor 상향 또는 soft-barrier
권장. (단 §1에서 본 대로 평소엔 margin이 안정적이라 CRITICAL 아닌 HIGH.)

### [검증됨] DORAEMON — 정확
Beta KL(`:125`), reverse-KL trust region, IS 성공률 추정 + ESS 검증(`:516`), entropy 최대화 + KL≤ε 제약.
표준 구현과 일치.

### [미검증·MEDIUM] cost returns `clamp(min=0)`이 버그 은폐 — `:443` / monitoring 텐서 detach 누락 `:466` / hot-path assert(-O 시 무력화) `:473` / CG damping 0.1 약할 수 있음
모두 robustness·관측성 개선. 정확성 치명 아님. 로깅 추가 + assert를 `__init__`으로 이동 권장.

---

## 4. encoder / runners / student

### [검증됨] 아키텍처·gradient flow — 정확, aux loss 0건
encoder 입력(privileged 24D → MLP → LayerNorm → softsign → z9D), actor=[obs87+z9], critic asymmetric,
z gradient flow 정상, BPTT truncation 정상. **`reconstruction/contrastive/z_bounds/auxiliary` grep 0건** —
`03-analysis-quality.md`의 "No Encoder Auxiliary Losses" 규칙 준수 확인.

### [검증됨·MEDIUM] 두 actor-critic 클래스 80% 중복 — `actor_critic_encoder.py` vs `actor_critic_asym_constrained.py`
ablation 분리 의도는 타당하나 `act/act_inference/update_normalization/load_state_dict`가 거의 동일.
`PolicyBase` 활용도를 높이거나 obs-composition을 strategy로 추출하면 통합 가능. **긴급도 낮음** (둘 다 frozen).

### [검증됨·LOW] runner 헬퍼 중복 — `constraint_encoder_runner` vs `on_policy_doraemon_runner`
`_should_log/_save_aux_state/_load_aux_state` 중복. 코드 주석이 "TRPO-specific 상속 회피용 의도적 중복"이라
명시. mixin으로 추출 가능하나 의도적이므로 우선순위 낮음.

---

## 5. TDC controllers (C++ 후보 포함)

### [검증됨] 제어 수학 — 정확
TDC 법칙(one-step delay 버퍼 인덱싱 정확, off-by-one 없음, 첫 step PD fallback), Lambda 결합행렬+DLS,
2-link FK/IK/Jacobian, restoring torque 부호. 기존 테스트(`test_tdc_controller.py` 478줄)가
Lambda/IK round-trip/reset 등 커버.

### [검증됨·C++ HIGH] `tdc.py` compute() hot-path → C++/CUDA 전환 후보
50Hz × num_envs, autograd 불필요, 순수 텐서 연산, 인터페이스 안정. 5~20× 추정. **유저가 C++ 허용**한
영역과 정확히 일치. 단 kinematics(분석해)·thruster_pd는 이득 적어 Python 유지 권장 (프로파일 후 결정).

### [검증됨·MEDIUM] `compute_M_bb()` 미사용 — `tdc.py:499`
`__init__.py`에서 export되나 호출처 0건. encoder-adaptive M_hat용으로 예약된 듯. 문서화하거나 제거.

### [미검증·테스트 갭] TDE delay 버퍼 1-step 정확성, rate-limit anti-windup, OOD robustness, `update_gains`는 미테스트.

---

## 6. analysis (최대 정리 기회)

### [검증됨·HIGH] `eval_dr.py` 4041줄 모놀리스 → 6모듈 분해
하위명령(static/periodic/segmented/sudden)별로 metric 계산 / plotting / DR config / trajectory / CLI가
한 파일에 뭉쳐 있음. 제안 구조: `cli.py`, `dr_config.py`, `trajectory.py`, `metrics/`, `plotting/`, `modes/`.
**도메인 로직은 보존**하고 경계만 분리 — analyze.py/compare.py/encoder_tools.py에서 재사용 가능.

### [검증됨·MEDIUM] metric 계산 5중 중복 + magic number 산재
SS window 0.5, heavy-tail 임계 5.0°/0.1m 등이 3~5곳에 하드코딩. `common.py`에 `MetricsConfig` dataclass로
중앙화. matplotlib `use("Agg")`도 5곳 반복 → `plotting/common.py:setup_matplotlib()`.

### [미검증·MEDIUM] matplotlib figure leak / YAML 예외 삼킴 — `eval_dr.py:2221` 등
plot 함수 대부분 `plt.close()` 하나 try/finally 미적용. YAML 로드 실패 시 `run_agent_dict` 미정의 참조 위험.
→ `save_and_close()` 헬퍼 + `run_agent_dict={}` 초기화.

---

## 7. structure / enterprise standards

### [검증됨·HIGH] config 9개 클래스 중복 25~40% — `rsl_rl_ppo_cfg.py` / `ablation_cfgs.py` / `config_noconstraint.py`
`seed=30, num_steps_per_env=64, max_iterations=2500` 등 100% 중복, policy/algo cfg 25~40% 중복.
6개 task가 문자열 경로로 cross-ref. → `_Base*Cfg` 정의 후 상속·override만. **가장 높은 ROI 구조 개선** (§0).

### [검증됨·HIGH] 테스트 부재 — `tests/`에 TDC 1개뿐
env step/reset, config 로드, constraint 평가, runner init, encoder forward 전부 무커버.
→ 스모크 테스트(env+10step, config load, runner+1iter) 추가. CI 없음도 함께.

### [검증됨·MEDIUM] print 365 vs logger 54 (7:1)
분석/env 코드에 ad-hoc print 다수. logging 표준화 권장.

### [검증됨·MEDIUM] deps 버전 핀 없음 — `pyproject.toml`
`["marinelab","gymnasium","torch","numpy"]` 상·하한 없음. 재현성 위험. 핀 권장.

### [미검증·MEDIUM] train.py builtins `__import__` 후크 / num_constraints 자동 동기화 silent mutation / IPO barrier 재사용 불가 구조 — 동작은 하나 암묵적. 문서화·명시화 권장.

---

## 7.5 범용 도구의 marinelab 승격 (유저 제안 — 검증 완료)

> 유저 제안: "DORAEMON은 범용 툴이니 marinelab로 옮기고 constrained-albc는 import해서 쓰자.
> 다른 범용 알고리즘도 같은 방식으로."

### [검증됨] DORAEMON은 승격 적격 — 연구 코드에 0 결합
`doraemon.py`의 import는 `numpy/torch/scipy/isaaclab.utils.configclass`뿐. **`constrained_albc` 내부 참조 0건**
(grep 확인). 레이어 의존 방향(isaaclab ← marinelab ← constrained-albc)을 깨지 않는다.

**유일한 연구-결합점 = `_PARAM_DEFS` (`doraemon.py:69`)** — 15개 DR 파라미터 이름이 ALBC의
`DomainRandomizationCfg` 필드명에 하드코딩됨. 엔진(`DoraemonScheduler`/`BetaDistribution`/`EpisodeBuffer`)은
완전 범용. 결합은 `build_param_specs(dr_cfg)`가 `getattr(dr_cfg, field_name)`로 (lo,hi)를 읽는 것뿐.

**승격 설계 (엔진=marinelab, 파라미터 정의=overlay 주입):**
```
marinelab/marinelab/algorithms/doraemon/   (NEW — 범용 엔진)
  ├── scheduler.py   # DoraemonScheduler, DoraemonCfg
  ├── distribution.py# BetaDistribution
  ├── buffer.py      # EpisodeBuffer
  └── spec.py        # ParamSpec, build_param_specs(dr_cfg, param_defs)  ← param_defs를 인자로
constrained-albc/.../constrained_full_albc/
  └── doraemon_params.py  # _PARAM_DEFS (ALBC 15개 파라미터) + nominal overrides만 남김
                          # from marinelab.algorithms.doraemon import DoraemonScheduler
```
핵심 변경: `build_param_specs`가 `_PARAM_DEFS`를 모듈 전역이 아니라 **인자로** 받게 한다.
그러면 marinelab 엔진이 BlueROV 등 다른 로봇/연구의 DR cfg와도 동작.

### 다른 승격 후보 (예비 평가 — 미검증, 승격 시 동일 절차로 import 경계 확인 필요)
| 후보 | 승격 적격성 | 근거 |
|:---|:---|:---|
| **DORAEMON** | ✅ 적격 (검증됨) | 연구코드 0 참조, 인터페이스 깔끔 |
| TDC controller (`controllers/`) | △ 조건부 | UUV 부력제어 일반론이나 2-link arm/buoy 특화. `kinematics.py`는 범용, `tdc.py`는 ALBC 특화 결합 점검 필요 |
| ConstraintTRPO + IPO barrier | △ 조건부 | rsl_rl 인터페이스엔 범용이나 cost critic/storage 결합 큼. IPO barrier만 떼어내면 범용 가능 |
| BetaDistribution 단독 | ✅ 적격 | DORAEMON 일부, 독립 유틸로도 유용 |

→ **권장**: DORAEMON 먼저 승격(가장 깔끔, 즉시 가능). TDC/TRPO는 import 경계 별도 진단 후 결정.

---

## 8. 권고 실행 순서 (승인 후)

```
Phase A (저위험·학습 무영향) — 바로 가능
  A1. obs 차원 assert 추가 (§2)              → verify: 잘못된 obs로 즉시 raise
  A2. hot-loop sigma 텐서 사전할당 (§2)       → verify: 동일 결과 + 미세 속도
  A3. analysis MetricsConfig + plotting 공통화 (§6) → verify: 기존 plot 재현
  A4. 환경/config 스모크 테스트 추가 (§7)      → verify: pytest 통과

Phase B (구조 리팩토링·동작 보존) — 검증 게이트 필요
  B1. eval_dr.py 4041줄 6모듈 분해 (§6)       → verify: 4개 mode 출력 before/after 동일
  B2. config base-template 리팩토링 (§7)      → verify: 6 task cfg.to_dict() 동일
  B3. deps 핀 + logging 표준화 (§7)

Phase C (수식·물리 — 유저 확인/논문 대조 필요)
  C1. cost surrogate 1/(1-γ) 정합성 (§3-A1)   → NORBC 논문 대조 or 저자 확인
  C2. added-mass clamp inertia 기준 (§2)      → 학습 안정성 영향 검토
  C3. barrier log clamp floor (§3-B)          → soft-barrier 실험

Phase D (성능 — 선택)
  D1. TDC compute() C++/CUDA 포팅 (§5)        → verify: Python 대비 수치 동일 + 속도
```

**원칙**: 각 항목은 독립 검증 가능. Phase C는 학습 동작을 바꾸므로 메모리·rule상 **유저 승인 + before/after 데이터**
없이 손대지 않는다 (`feedback_no_unauthorized_changes`, `feedback_training_control`).
